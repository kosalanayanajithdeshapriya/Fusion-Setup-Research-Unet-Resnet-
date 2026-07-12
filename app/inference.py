"""Shared inference logic for the demo UI: runs a single image through both
branches (ResNet50 feature extractor, U-Net LPF) and all three trained
classifier heads (A/B/C), reusing the exact same checkpoints, scalers, and
preprocessing as the training pipeline in scripts/.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "inputs", ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from resnet_feature_extractor import load_resnet_feature_extractor, PREPROCESS  # noqa: E402
from unet_lpf_extractor import load_unet, compute_lpf  # noqa: E402
from model_common import MLPHead, MODEL_CONFIGS  # noqa: E402

CHECKPOINT_DIR = ROOT / "checkpoints"
INPUTS_DIR = ROOT / "inputs"


class FusionPredictor:
    def __init__(self, device=None):
        self.device = torch.device(device) if device else torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        with open(INPUTS_DIR / "resnet_metadata.json") as f:
            self.class_names = json.load(f)["class_names"]

        self.resnet_model = load_resnet_feature_extractor(
            str(INPUTS_DIR / "resnet50_tomato_final.pth"), device=self.device
        )
        self.unet_model = load_unet(str(INPUTS_DIR / "unet_tomato_final.pth"), device=self.device)

        self.resnet_scaler = joblib.load(CHECKPOINT_DIR / "resnet_scaler.joblib")
        self.lpf_scaler = joblib.load(CHECKPOINT_DIR / "lpf_scaler.joblib")

        self.heads = {}
        for name, cfg in MODEL_CONFIGS.items():
            head = MLPHead(cfg["in_dim"], cfg["hidden_dim"], len(self.class_names), cfg["dropout"]).to(self.device)
            state_dict = torch.load(
                CHECKPOINT_DIR / f"model_{name}_best.pt", map_location=self.device, weights_only=True
            )
            head.load_state_dict(state_dict)
            head.eval()
            self.heads[name] = head

    @torch.no_grad()
    def predict(self, image_path):
        """image_path: path to a real file on disk (jpg/png). Returns lpf,
        predicted mask, class order, and per-model prediction + probabilities."""
        image_path = Path(image_path)

        img = Image.open(image_path).convert("RGB")
        x = PREPROCESS(img).unsqueeze(0).to(self.device)
        resnet_feat = self.resnet_model(x).cpu().numpy()  # (1, 2048)

        lpf, mask = compute_lpf(self.unet_model, image_path)
        lpf_arr = np.array([[lpf]], dtype=np.float32)

        resnet_scaled = self.resnet_scaler.transform(resnet_feat).astype(np.float32)
        lpf_scaled = self.lpf_scaler.transform(lpf_arr).astype(np.float32)
        fused_scaled = np.concatenate([resnet_scaled, lpf_scaled], axis=1)

        features_by_model = {
            "A_resnet_only": resnet_scaled,
            "B_lpf_only": lpf_scaled,
            "C_fused": fused_scaled,
        }

        predictions = {}
        for name, cfg in MODEL_CONFIGS.items():
            xb = torch.tensor(features_by_model[name], dtype=torch.float32, device=self.device)
            logits = self.heads[name](xb)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
            pred_idx = int(np.argmax(probs))
            predictions[name] = {
                "display_name": cfg["display_name"],
                "predicted_class": self.class_names[pred_idx],
                "confidence": float(probs[pred_idx]),
                "probabilities": {c: float(p) for c, p in zip(self.class_names, probs)},
            }

        return {
            "lpf": lpf,
            "mask": mask,
            "class_names": self.class_names,
            "predictions": predictions,
        }
