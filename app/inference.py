"""Shared inference logic for the demo UI: runs a single image through all
five models — A (ResNet-only), B (LPF-only), C (Fused), D (the crop-aligned
U-Net leaf-focused pipeline, the recommended model), and E (the earlier
DeepLabV3-based leaf-focused pipeline, the second-best model) — reusing the
exact same checkpoints, scalers, and preprocessing as the training pipeline
in scripts/ and the standalone leaf_pipeline*.py files as-is.
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
import leaf_pipeline  # noqa: E402
import leaf_pipeline_deeplab  # noqa: E402
from leaf_pipeline import load_leaf_pipeline  # noqa: E402

CHECKPOINT_DIR = ROOT / "checkpoints"
INPUTS_DIR = ROOT / "inputs"


@torch.no_grad()
def predict_leaf_pipeline_with_mask(image_pil, unet_model, classifier, device):
    """Mirrors leaf_pipeline.predict_growth_stage() exactly (same crop-aligned
    transforms, same normalization, same class order) but additionally returns
    the predicted plant/background mask, so the UI can show it the same way the
    U-Net LPF branch's mask is shown. Purely additive — inputs/leaf_pipeline.py
    itself is untouched. The U-Net here returns raw 1-channel logits (not a
    dict like torchvision's DeepLabV3), so the mask is sigmoid+threshold, not
    argmax."""
    raw = leaf_pipeline.RAW_TRANSFORM(image_pil.convert("RGB")).unsqueeze(0).to(device)
    normed = leaf_pipeline.NORMALIZE(raw.squeeze(0)).unsqueeze(0)
    logits = unet_model(normed)
    pred_mask = (torch.sigmoid(logits) > leaf_pipeline.MASK_THRESHOLD).float()
    masked_raw = raw * pred_mask
    masked_norm = leaf_pipeline.NORMALIZE(masked_raw.squeeze(0)).unsqueeze(0)
    clf_logits = classifier(masked_norm)
    probs = torch.softmax(clf_logits, dim=1)[0].cpu().numpy()
    pred_idx = int(probs.argmax())
    mask_np = pred_mask[0, 0].cpu().numpy()
    label = leaf_pipeline.CLASS_NAMES[pred_idx]
    prob_dict = {c: float(p) for c, p in zip(leaf_pipeline.CLASS_NAMES, probs.tolist())}
    return label, prob_dict, mask_np


@torch.no_grad()
def predict_deeplab_pipeline_with_mask(image_pil, seg_model, classifier, device):
    """Mirrors leaf_pipeline_deeplab.predict_growth_stage() exactly (same
    transforms, same normalization, same class order) but additionally returns
    the predicted plant/background mask. torchvision's DeepLabV3 returns a
    dict with an "out" key (2-channel logits), unlike the U-Net pipeline's
    plain 1-channel tensor, so the mask here is argmax, not sigmoid+threshold."""
    raw = leaf_pipeline_deeplab.RAW_TRANSFORM(image_pil.convert("RGB")).unsqueeze(0).to(device)
    norm = leaf_pipeline_deeplab.NORMALIZE(raw)
    pred_mask = seg_model(norm)["out"].argmax(dim=1, keepdim=True).float()
    masked_raw = raw * pred_mask
    masked_norm = leaf_pipeline_deeplab.NORMALIZE(masked_raw)
    logits = classifier(masked_norm)
    probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    pred_idx = int(probs.argmax())
    mask_np = pred_mask[0, 0].cpu().numpy()
    label = leaf_pipeline_deeplab.CLASS_NAMES[pred_idx]
    prob_dict = {c: float(p) for c, p in zip(leaf_pipeline_deeplab.CLASS_NAMES, probs.tolist())}
    return label, prob_dict, mask_np


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

        self.leaf_seg_model, self.leaf_classifier = load_leaf_pipeline(
            str(INPUTS_DIR / "unet_leaf_seg.pth"),
            str(INPUTS_DIR / "resnet50_leaf_classifier.pth"),
            device=self.device,
        )

        # Model E (second-best) reuses the identical classifier weights loaded
        # above for Model D (confirmed via metadata.json: same checkpoint,
        # reused across all segmenter variants) — only the segmenter differs.
        self.deeplab_seg_model, _ = leaf_pipeline_deeplab.load_leaf_pipeline(
            str(INPUTS_DIR / "deeplabv3_leaf_seg.pth"),
            str(INPUTS_DIR / "resnet50_leaf_classifier.pth"),
            device=self.device,
        )

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

        leaf_label, leaf_probs, leaf_mask = predict_leaf_pipeline_with_mask(
            img, self.leaf_seg_model, self.leaf_classifier, self.device
        )
        predictions["D_leaf_pipeline"] = {
            "display_name": "Model D (Leaf-Focused Pipeline)",
            "predicted_class": leaf_label,
            "confidence": leaf_probs[leaf_label],
            "probabilities": leaf_probs,
        }

        deeplab_label, deeplab_probs, deeplab_mask = predict_deeplab_pipeline_with_mask(
            img, self.deeplab_seg_model, self.leaf_classifier, self.device
        )
        predictions["E_deeplab_pipeline"] = {
            "display_name": "Model E (DeepLabV3 Leaf-Focused Pipeline)",
            "predicted_class": deeplab_label,
            "confidence": deeplab_probs[deeplab_label],
            "probabilities": deeplab_probs,
        }

        return {
            "lpf": lpf,
            "mask": mask,
            "leaf_mask": leaf_mask,
            "deeplab_mask": deeplab_mask,
            "class_names": self.class_names,
            "predictions": predictions,
        }
