"""Standalone loader for the tomato growth-stage ResNet50 checkpoint as a feature extractor.

Copy-paste this file into another project with no other dependency on the
original training code. Requires: torch, torchvision.

Usage:
    from resnet_feature_extractor import load_resnet_feature_extractor, PREPROCESS

    model = load_resnet_feature_extractor("resnet50_tomato_final.pth")
    features = model(PREPROCESS(image).unsqueeze(0))  # -> (1, 2048)
"""
import torch
import torch.nn as nn
from torchvision import transforms, models

NUM_CLASSES = 4
CLASS_NAMES = ["developing", "flowering", "fruiting", "seeding"]

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

PREPROCESS = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def load_resnet_feature_extractor(checkpoint_path, device=None):
    """Load the trained ResNet50 checkpoint and return it as a 2048-dim feature extractor.

    Instantiates the same architecture used during training (ResNet50 with the
    final fc replaced by nn.Linear(2048, NUM_CLASSES)), loads the state_dict,
    then swaps fc for nn.Identity() so the model outputs the pooled 2048-dim
    feature vector instead of class logits.

    Args:
        checkpoint_path: path to a state_dict-only .pth file
            (e.g. resnet50_tomato_final.pth).
        device: torch.device or str to load the model onto. Defaults to
            cuda if available, else cpu.

    Returns:
        torch.nn.Module in eval() mode, on `device`, mapping an input tensor
        of shape (batch, 3, 224, 224) to (batch, 2048).
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device) if not isinstance(device, torch.device) else device

    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)

    state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)

    model.fc = nn.Identity()
    model = model.to(device)
    model.eval()
    return model
