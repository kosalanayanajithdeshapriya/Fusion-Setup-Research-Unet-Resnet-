"""Standalone leaf-focused tomato growth-stage inference pipeline.
Segments the plant/leaf region out of a raw photo, blacks out the background, then
classifies growth stage. No dependency on this project's training code -- copy-paste
into another project alongside deeplabv3_leaf_seg.pth and resnet50_leaf_classifier.pth.
"""
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.models.segmentation import deeplabv3_resnet50

CLASS_NAMES = ['developing', 'flowering', 'fruiting', 'seeding']
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

RAW_TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
])
NORMALIZE = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)


def load_leaf_pipeline(seg_checkpoint_path, classifier_checkpoint_path, device=None):
    """Returns (segmentation_model, classifier_model), both in eval() mode on device."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device) if not isinstance(device, torch.device) else device

    # aux_loss=True is required here: the saved checkpoint was trained with the
    # COCO-pretrained weights (which include an aux_classifier), so its state_dict
    # contains aux_classifier.* keys. Without aux_loss=True, weights=None builds the
    # model with aux_classifier=None and load_state_dict fails on those keys.
    seg_model = deeplabv3_resnet50(weights=None, aux_loss=True)
    seg_model.classifier[4] = nn.Conv2d(256, 2, kernel_size=1)
    seg_model.aux_classifier[4] = nn.Conv2d(256, 2, kernel_size=1)
    seg_state = torch.load(seg_checkpoint_path, map_location=device, weights_only=True)
    seg_model.load_state_dict(seg_state)
    seg_model = seg_model.to(device).eval()

    classifier = models.resnet50(weights=None)
    classifier.fc = nn.Linear(classifier.fc.in_features, len(CLASS_NAMES))
    clf_state = torch.load(classifier_checkpoint_path, map_location=device, weights_only=True)
    classifier.load_state_dict(clf_state)
    classifier = classifier.to(device).eval()

    return seg_model, classifier


def predict_growth_stage(image_pil, seg_model, classifier, device=None):
    """image_pil: a PIL.Image (RGB). Returns (predicted_class_name, probs_dict)."""
    if device is None:
        device = next(classifier.parameters()).device

    raw = RAW_TRANSFORM(image_pil.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        norm = NORMALIZE(raw)
        pred_mask = seg_model(norm)["out"].argmax(dim=1, keepdim=True).float()
        masked_raw = raw * pred_mask
        masked_norm = NORMALIZE(masked_raw)
        logits = classifier(masked_norm)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

    pred_idx = int(probs.argmax())
    return CLASS_NAMES[pred_idx], dict(zip(CLASS_NAMES, probs.tolist()))
