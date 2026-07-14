"""Standalone leaf-focused tomato growth-stage inference pipeline (U-Net segmenter,
crop-aligned variant). Segments the plant/leaf region out of a raw photo using a
from-scratch U-Net, blacks out the background, then classifies growth stage with a
ResNet50 trained on masked images. No dependency on the U-Net project or this project's
training code -- copy-paste into another project alongside unet_leaf_seg.pth and
resnet50_leaf_classifier.pth.

THIS IS THE RECOMMENDED PIPELINE (see metadata.json for the full comparison): 89.4%
full-pipeline test accuracy, ahead of both the DeepLabV3 variant (84.4%,
export_leaf_pipeline/) and an earlier version of this same U-Net pipeline that used
U-Net's own native direct-resize preprocessing (78.75%). The improvement came from
feeding U-Net the SAME Resize(256)->CenterCrop(224) image the classifier expects,
instead of U-Net's own native direct-resize (which distorts aspect ratio and misaligned
the mask with what the classifier was trained on) -- segmentation quality itself barely
changed between the two U-Net variants, so the earlier version's weaker accuracy was
almost entirely down to that geometry mismatch, not U-Net's segmentation ability.
"""
import torch
import torch.nn as nn
from torchvision import models, transforms

CLASS_NAMES = ["developing", "flowering", "fruiting", "seeding"]
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMG_SIZE = 224
MASK_THRESHOLD = 0.5
BASE_CHANNELS = 32

RAW_TRANSFORM = transforms.Compose([
    transforms.Resize(int(IMG_SIZE * 1.14)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
])
NORMALIZE = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)


class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class UNet(nn.Module):
    """Encoder-decoder U-Net with skip connections (Ronneberger et al.), trained from scratch."""

    def __init__(self, in_channels=3, out_channels=1, base_channels=BASE_CHANNELS):
        super().__init__()
        c = base_channels
        self.enc1 = DoubleConv(in_channels, c)
        self.enc2 = DoubleConv(c, c * 2)
        self.enc3 = DoubleConv(c * 2, c * 4)
        self.enc4 = DoubleConv(c * 4, c * 8)
        self.pool = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(c * 8, c * 16)

        self.up4 = nn.ConvTranspose2d(c * 16, c * 8, 2, stride=2)
        self.dec4 = DoubleConv(c * 16, c * 8)
        self.up3 = nn.ConvTranspose2d(c * 8, c * 4, 2, stride=2)
        self.dec3 = DoubleConv(c * 8, c * 4)
        self.up2 = nn.ConvTranspose2d(c * 4, c * 2, 2, stride=2)
        self.dec2 = DoubleConv(c * 4, c * 2)
        self.up1 = nn.ConvTranspose2d(c * 2, c, 2, stride=2)
        self.dec1 = DoubleConv(c * 2, c)

        self.out_conv = nn.Conv2d(c, out_channels, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        b = self.bottleneck(self.pool(e4))

        d4 = self.dec4(torch.cat([self.up4(b), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

        return self.out_conv(d1)  # logits


def load_leaf_pipeline(seg_checkpoint_path, classifier_checkpoint_path, device=None):
    """Returns (unet_model, classifier_model), both in eval() mode on device."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device) if not isinstance(device, torch.device) else device

    unet_model = UNet(in_channels=3, out_channels=1, base_channels=BASE_CHANNELS)
    unet_state = torch.load(seg_checkpoint_path, map_location=device, weights_only=True)
    unet_model.load_state_dict(unet_state)
    unet_model = unet_model.to(device).eval()

    classifier = models.resnet50(weights=None)
    classifier.fc = nn.Linear(classifier.fc.in_features, len(CLASS_NAMES))
    clf_state = torch.load(classifier_checkpoint_path, map_location=device, weights_only=True)
    classifier.load_state_dict(clf_state)
    classifier = classifier.to(device).eval()

    return unet_model, classifier


def predict_growth_stage(image_path, unet_model, classifier, device=None, threshold=MASK_THRESHOLD):
    """image_path: path to an image file, or a PIL.Image. Returns
    (predicted_class_name, confidence, probs_dict)."""
    if device is None:
        device = next(classifier.parameters()).device

    from PIL import Image
    img = image_path if hasattr(image_path, "convert") else Image.open(image_path)
    img_cropped = RAW_TRANSFORM(img.convert("RGB"))  # 0-1 scale tensor, aspect-preserving crop

    raw = img_cropped.unsqueeze(0).to(device)

    with torch.no_grad():
        normed = NORMALIZE(raw.squeeze(0)).unsqueeze(0)
        logits = unet_model(normed)
        probs_mask = torch.sigmoid(logits)
        pred_mask = (probs_mask > threshold).float()  # 1x1xHxW

        masked_raw = raw * pred_mask
        masked_norm = NORMALIZE(masked_raw.squeeze(0)).unsqueeze(0)

        clf_logits = classifier(masked_norm)
        class_probs = torch.softmax(clf_logits, dim=1)[0].cpu().numpy()

    pred_idx = int(class_probs.argmax())
    return CLASS_NAMES[pred_idx], float(class_probs[pred_idx]), dict(zip(CLASS_NAMES, class_probs.tolist()))
