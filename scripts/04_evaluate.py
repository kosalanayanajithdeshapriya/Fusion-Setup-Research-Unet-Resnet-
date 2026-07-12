"""Task 4 + 5: evaluate Models A/B/C on the test split (once), save confusion
matrices, training curves, and a comparison table (CSV + markdown) to results/.

Usage:
    python scripts/04_evaluate.py
"""
import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from model_common import MLPHead, MODEL_CONFIGS  # noqa: E402

COMBINED_NPZ = ROOT / "outputs" / "combined_features.npz"
RESNET_METADATA = ROOT / "inputs" / "resnet_metadata.json"
CHECKPOINT_DIR = ROOT / "checkpoints"
OUTPUT_DIR = ROOT / "outputs"
RESULTS_PLOTS = ROOT / "results" / "plots"
RESULTS_TABLES = ROOT / "results" / "tables"

MODEL_COLORS = {
    "A_resnet_only": "#2a78d6",  # blue
    "B_lpf_only": "#1baf7a",     # aqua
    "C_fused": "#e34948",        # red
}
BLUE_SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]

CHART_STYLE = {
    "figure.facecolor": "#fcfcfb",
    "axes.facecolor": "#fcfcfb",
    "axes.edgecolor": "#c3c2b7",
    "axes.labelcolor": "#0b0b0b",
    "text.color": "#0b0b0b",
    "xtick.color": "#898781",
    "ytick.color": "#898781",
    "axes.titlecolor": "#0b0b0b",
    "grid.color": "#e1e0d9",
    "font.family": "sans-serif",
}


def load_model(name, cfg, num_classes, device):
    model = MLPHead(cfg["in_dim"], cfg["hidden_dim"], num_classes, cfg["dropout"]).to(device)
    state_dict = torch.load(CHECKPOINT_DIR / f"model_{name}_best.pt", map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def plot_confusion_matrices(cms, class_names, model_names):
    plt.rcParams.update(CHART_STYLE)
    cmap = LinearSegmentedColormap.from_list("blue_seq", BLUE_SEQUENTIAL)

    fig, axes = plt.subplots(1, len(model_names), figsize=(5 * len(model_names), 4.5))
    for ax, name in zip(axes, model_names):
        cm = cms[name]
        im = ax.imshow(cm, cmap=cmap, vmin=0)
        ax.set_xticks(range(len(class_names)))
        ax.set_yticks(range(len(class_names)))
        ax.set_xticklabels(class_names, rotation=45, ha="right")
        ax.set_yticklabels(class_names)
        ax.set_xlabel("Predicted")
        if name == model_names[0]:
            ax.set_ylabel("True")
        ax.set_title(MODEL_CONFIGS[name]["display_name"])
        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                color = "#ffffff" if cm[i, j] > thresh else "#0b0b0b"
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontsize=10)
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.tight_layout()
    out_path = RESULTS_PLOTS / "confusion_matrices.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved {out_path}")


def plot_training_curves(model_names):
    plt.rcParams.update(CHART_STYLE)
    fig, axes = plt.subplots(2, len(model_names), figsize=(5 * len(model_names), 7), sharex=False)

    for col, name in enumerate(model_names):
        history_path = OUTPUT_DIR / f"history_{name}.json"
        with open(history_path) as f:
            history = json.load(f)
        epochs = range(1, len(history["train_loss"]) + 1)
        color = MODEL_COLORS[name]

        ax_loss = axes[0, col]
        ax_loss.plot(epochs, history["train_loss"], color=color, linestyle="-", linewidth=2, label="train")
        ax_loss.plot(epochs, history["val_loss"], color=color, linestyle="--", linewidth=2, label="valid")
        ax_loss.set_title(MODEL_CONFIGS[name]["display_name"])
        ax_loss.set_xlabel("epoch")
        if col == 0:
            ax_loss.set_ylabel("loss")
        ax_loss.legend(frameon=False)
        ax_loss.grid(True, linewidth=0.5)

        ax_acc = axes[1, col]
        ax_acc.plot(epochs, history["train_acc"], color=color, linestyle="-", linewidth=2, label="train")
        ax_acc.plot(epochs, history["val_acc"], color=color, linestyle="--", linewidth=2, label="valid")
        ax_acc.set_xlabel("epoch")
        if col == 0:
            ax_acc.set_ylabel("accuracy")
        ax_acc.legend(frameon=False)
        ax_acc.grid(True, linewidth=0.5)

        for ax in (ax_loss, ax_acc):
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)

    fig.tight_layout()
    out_path = RESULTS_PLOTS / "training_curves.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved {out_path}")


def main():
    RESULTS_PLOTS.mkdir(parents=True, exist_ok=True)
    RESULTS_TABLES.mkdir(parents=True, exist_ok=True)

    with open(RESNET_METADATA) as f:
        class_names = json.load(f)["class_names"]
    print(f"class order: {class_names}")

    data = np.load(COMBINED_NPZ, allow_pickle=True)
    growth_stage = data["growth_stage"]
    split = data["split"]
    resnet_features = data["resnet_features"].astype(np.float32)
    lpf = data["lpf"].astype(np.float32).reshape(-1, 1)

    label_to_idx = {c: i for i, c in enumerate(class_names)}
    y = np.array([label_to_idx[g] for g in growth_stage], dtype=np.int64)
    test_mask = split == "test"
    print(f"test split size: {test_mask.sum()}")
    y_test = y[test_mask]

    resnet_scaler = joblib.load(CHECKPOINT_DIR / "resnet_scaler.joblib")
    lpf_scaler = joblib.load(CHECKPOINT_DIR / "lpf_scaler.joblib")
    resnet_scaled = resnet_scaler.transform(resnet_features).astype(np.float32)
    lpf_scaled = lpf_scaler.transform(lpf).astype(np.float32)
    fused_scaled = np.concatenate([resnet_scaled, lpf_scaled], axis=1)

    features_by_model = {
        "A_resnet_only": resnet_scaled[test_mask],
        "B_lpf_only": lpf_scaled[test_mask],
        "C_fused": fused_scaled[test_mask],
    }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_names = list(MODEL_CONFIGS.keys())

    cms = {}
    rows = []
    dev_idx = class_names.index("developing")
    flow_idx = class_names.index("flowering")
    boundary_rows = []

    for name in model_names:
        cfg = MODEL_CONFIGS[name]
        model = load_model(name, cfg, len(class_names), device)
        X_test = torch.tensor(features_by_model[name], dtype=torch.float32, device=device)
        with torch.no_grad():
            preds = model(X_test).argmax(1).cpu().numpy()

        acc = accuracy_score(y_test, preds)
        report = classification_report(
            y_test, preds, labels=list(range(len(class_names))),
            target_names=class_names, output_dict=True, zero_division=0,
        )
        cm = confusion_matrix(y_test, preds, labels=list(range(len(class_names))))
        cms[name] = cm

        row = {
            "model": cfg["display_name"],
            "test_accuracy": acc,
            "macro_precision": report["macro avg"]["precision"],
            "macro_recall": report["macro avg"]["recall"],
            "macro_f1": report["macro avg"]["f1-score"],
            "weighted_f1": report["weighted avg"]["f1-score"],
        }
        for c in class_names:
            row[f"{c}_precision"] = report[c]["precision"]
            row[f"{c}_recall"] = report[c]["recall"]
            row[f"{c}_f1"] = report[c]["f1-score"]
            row[f"{c}_support"] = report[c]["support"]
        rows.append(row)

        dev_support = cm[dev_idx].sum()
        flow_support = cm[flow_idx].sum()
        boundary_rows.append({
            "model": cfg["display_name"],
            "developing_true_predicted_flowering": int(cm[dev_idx, flow_idx]),
            "developing_true_predicted_flowering_rate": cm[dev_idx, flow_idx] / dev_support if dev_support else 0.0,
            "flowering_true_predicted_developing": int(cm[flow_idx, dev_idx]),
            "flowering_true_predicted_developing_rate": cm[flow_idx, dev_idx] / flow_support if flow_support else 0.0,
        })

        print(f"[{cfg['display_name']}] test_accuracy={acc:.4f}")

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(RESULTS_TABLES / "comparison_summary.csv", index=False)
    with open(RESULTS_TABLES / "comparison_summary.md", "w") as f:
        f.write(summary_df.to_markdown(index=False))
    print(f"saved {RESULTS_TABLES / 'comparison_summary.csv'} and .md")

    boundary_df = pd.DataFrame(boundary_rows)
    boundary_df.to_csv(RESULTS_TABLES / "developing_flowering_boundary.csv", index=False)
    with open(RESULTS_TABLES / "developing_flowering_boundary.md", "w") as f:
        f.write(boundary_df.to_markdown(index=False))
    print(f"saved {RESULTS_TABLES / 'developing_flowering_boundary.csv'} and .md")

    plot_confusion_matrices(cms, class_names, model_names)
    plot_training_curves(model_names)


if __name__ == "__main__":
    main()
