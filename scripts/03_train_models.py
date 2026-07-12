"""Task 3: train Model A (ResNet-only), Model B (LPF-only), Model C (fused).

Uses the "split" column from the combined table strictly: train for gradient
updates, valid for best-checkpoint selection. Test is untouched here (Task 4).
Label encoding order comes from inputs/resnet_metadata.json class_names, used
consistently across all three models. Features are standardized (StandardScaler
fit on train split only), per user confirmation.

Usage:
    python scripts/03_train_models.py
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import joblib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from model_common import MLPHead, MODEL_CONFIGS, set_seed  # noqa: E402

COMBINED_NPZ = ROOT / "outputs" / "combined_features.npz"
RESNET_METADATA = ROOT / "inputs" / "resnet_metadata.json"
CHECKPOINT_DIR = ROOT / "checkpoints"
OUTPUT_DIR = ROOT / "outputs"


def train_model(name, X_train, y_train, X_valid, y_valid, in_dim, hidden_dim, dropout,
                 num_classes, device, seed, epochs, batch_size, lr, patience, checkpoint_path):
    set_seed(seed)
    model = MLPHead(in_dim, hidden_dim, num_classes, dropout).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_valid_t = torch.tensor(X_valid, dtype=torch.float32, device=device)
    y_valid_t = torch.tensor(y_valid, dtype=torch.long, device=device)

    dataset = torch.utils.data.TensorDataset(X_train_t, y_train_t)
    g = torch.Generator().manual_seed(seed)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True, generator=g)

    best_val_acc = -1.0
    best_epoch = -1
    epochs_since_best = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss, correct, n = 0.0, 0, 0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            opt.step()
            total_loss += loss.item() * xb.size(0)
            correct += (logits.argmax(1) == yb).sum().item()
            n += xb.size(0)
        train_loss = total_loss / n
        train_acc = correct / n

        model.eval()
        with torch.no_grad():
            val_logits = model(X_valid_t)
            val_loss = criterion(val_logits, y_valid_t).item()
            val_acc = (val_logits.argmax(1) == y_valid_t).float().mean().item()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        improved = val_acc > best_val_acc
        if improved:
            best_val_acc = val_acc
            best_epoch = epoch
            epochs_since_best = 0
            torch.save(model.state_dict(), checkpoint_path)
        else:
            epochs_since_best += 1

        print(f"[{name}] epoch {epoch:3d}/{epochs}  train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}{'  *' if improved else ''}")

        if epochs_since_best >= patience:
            print(f"[{name}] early stopping at epoch {epoch} (no val_acc improvement in {patience} epochs)")
            break

    print(f"[{name}] best val_acc={best_val_acc:.4f} at epoch {best_epoch}, checkpoint saved to {checkpoint_path}")
    return history, best_val_acc, best_epoch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with open(RESNET_METADATA) as f:
        resnet_meta = json.load(f)
    class_names = resnet_meta["class_names"]
    print(f"using class order from resnet_metadata.json: {class_names}")

    data = np.load(COMBINED_NPZ, allow_pickle=True)
    growth_stage = data["growth_stage"]
    split = data["split"]
    resnet_features = data["resnet_features"].astype(np.float32)
    lpf = data["lpf"].astype(np.float32).reshape(-1, 1)

    label_to_idx = {c: i for i, c in enumerate(class_names)}
    unknown = set(growth_stage) - set(label_to_idx)
    if unknown:
        raise ValueError(f"growth_stage values not in resnet_metadata.json class_names: {unknown}")
    y = np.array([label_to_idx[g] for g in growth_stage], dtype=np.int64)

    train_mask = split == "train"
    valid_mask = split == "valid"
    test_mask = split == "test"  # untouched here, reserved for Task 4
    print(f"split sizes -> train={train_mask.sum()} valid={valid_mask.sum()} test={test_mask.sum()}")

    resnet_scaler = StandardScaler().fit(resnet_features[train_mask])
    lpf_scaler = StandardScaler().fit(lpf[train_mask])

    resnet_scaled = resnet_scaler.transform(resnet_features).astype(np.float32)
    lpf_scaled = lpf_scaler.transform(lpf).astype(np.float32)
    fused_scaled = np.concatenate([resnet_scaled, lpf_scaled], axis=1)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(resnet_scaler, CHECKPOINT_DIR / "resnet_scaler.joblib")
    joblib.dump(lpf_scaler, CHECKPOINT_DIR / "lpf_scaler.joblib")
    with open(CHECKPOINT_DIR / "class_names.json", "w") as f:
        json.dump(class_names, f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"training on {device}, seed={args.seed}")

    features_by_model = {
        "A_resnet_only": resnet_scaled,
        "B_lpf_only": lpf_scaled,
        "C_fused": fused_scaled,
    }

    summary = {}
    for name, cfg in MODEL_CONFIGS.items():
        X = features_by_model[name]
        history, best_val_acc, best_epoch = train_model(
            name=name,
            X_train=X[train_mask], y_train=y[train_mask],
            X_valid=X[valid_mask], y_valid=y[valid_mask],
            in_dim=cfg["in_dim"], hidden_dim=cfg["hidden_dim"], dropout=cfg["dropout"],
            num_classes=len(class_names), device=device, seed=args.seed,
            epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, patience=args.patience,
            checkpoint_path=CHECKPOINT_DIR / f"model_{name}_best.pt",
        )
        with open(OUTPUT_DIR / f"history_{name}.json", "w") as f:
            json.dump(history, f)
        summary[name] = {"best_val_acc": best_val_acc, "best_epoch": best_epoch}

    with open(OUTPUT_DIR / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
