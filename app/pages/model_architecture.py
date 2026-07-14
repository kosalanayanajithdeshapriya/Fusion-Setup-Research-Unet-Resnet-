"""Model Architecture page: how ResNet50, U-Net, and the fusion head fit
together. Facts sourced from inputs/resnet_metadata.json, inputs/unet_metadata.json,
and scripts/model_common.py — not re-derived or guessed.
"""
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from common import get_leaf_pipeline_metadata  # noqa: E402
from ui_theme import card_title_html, footer_html, icon_svg, page_header_html, recommended_ribbon_html, step_flow_html  # noqa: E402

with open(ROOT / "inputs" / "resnet_metadata.json") as f:
    resnet_meta = json.load(f)
with open(ROOT / "inputs" / "unet_metadata.json") as f:
    unet_meta = json.load(f)

st.markdown(
    page_header_html(
        "cpu",
        "Model Architecture",
        "The recommended leaf-focused pipeline, plus the underlying ResNet50 + U-Net fusion comparison study.",
    ),
    unsafe_allow_html=True,
)

# ---------------------------------- Model D: recommended architecture ------
leaf_meta = get_leaf_pipeline_metadata()
if leaf_meta is not None:
    seg = leaf_meta["segmentation_model"]
    clf = leaf_meta["classifier_model"]
    leaf_steps = [
        ("image", "Raw Photo", f"{leaf_meta['input_size'][0]}×{leaf_meta['input_size'][1]}×{leaf_meta['input_size'][2]} RGB, any input size"),
        ("layers", "DeepLabV3 Segmentation", f"{seg['architecture']} ({seg['num_classes']}-class: background / plant-leaf)"),
        ("shield-check", "Background Masking", "Background pixels zeroed out using the predicted mask"),
        ("cpu", "ResNet50 Classification", f"fc replaced with Linear(2048, {clf['num_classes']}), trained on masked images only"),
    ]
    st.markdown(
        f'''<div class="card model-card recommended" style="--card-accent: var(--model-d);">
          {recommended_ribbon_html("Recommended · Model D")}
          {card_title_html("shield-check", "Model D — Leaf-Focused Segment-then-Classify Pipeline", "--model-d")}
          <p class="subtitle">Two models run in sequence, not a feature-fusion branch — the segmentation
          stage's own predicted mask feeds directly into the classifier at inference time.</p>
          {step_flow_html(leaf_steps)}
          <ul style="color:var(--text-secondary); line-height:1.7; margin:1rem 0 0; padding-left:1.1rem; font-size:0.9rem;">
            <li><b>Segmentation training:</b> COCO polygon annotations of the same tomato photos;
            best epoch {seg['best_epoch']}, validation IoU {seg['val_iou_at_best_epoch']*100:.1f}%,
            test mean IoU {seg['test_mean_iou']*100:.1f}%</li>
            <li><b>Classifier training:</b> {clf['trained_on']} — learns leaf/plant material only,
            with no background context available</li>
            <li><b>Normalization:</b> standard ImageNet mean/std, handled internally by
            <code>inputs/leaf_pipeline.py</code></li>
            <li><b>Class order:</b> {", ".join(clf['class_names'])} (alphabetical — the trained order,
            not chronological growth order)</li>
          </ul>
        </div>''',
        unsafe_allow_html=True,
    )

# ---------------------------------- A/B/C fusion comparison architecture ---
st.markdown(
    f'<div class="section-title">{icon_svg("git-merge", size=17)} A / B / C — ResNet50 + U-Net fusion comparison</div>',
    unsafe_allow_html=True,
)

flow_steps = [
    ("image", "Input Image", f"{resnet_meta['input_size'][0]}×{resnet_meta['input_size'][1]}×{resnet_meta['input_size'][2]} RGB"),
    ("layers", "Branch 01 — U-Net", "Predicts a binary leaf mask → reduced to Leaf Pixel Fraction (LPF)"),
    ("cpu", "Branch 02 — ResNet50", "Classifier head stripped → 2048-dim pooled feature vector"),
    ("git-merge", "Fusion MLP", "Concatenate (2049-dim) → Dense(128, ReLU) → Dropout(0.3) → Dense(4, Softmax)"),
]
st.markdown(
    f'<div class="card">{card_title_html("git-merge", "Pipeline overview", "--brand-terracotta")}{step_flow_html(flow_steps)}</div>',
    unsafe_allow_html=True,
)

col_a, col_b = st.columns(2, gap="medium")
with col_a:
    st.markdown(
        f'''<div class="card model-card" style="--card-accent: var(--model-a);">
          {card_title_html("cpu", "Branch 02 — ResNet50", "--model-a")}
          <ul style="color:var(--text-secondary); line-height:1.7; margin:0; padding-left:1.1rem; font-size:0.9rem;">
            <li><b>Architecture:</b> {resnet_meta['architecture']}</li>
            <li><b>Modification:</b> {resnet_meta['modifications']}</li>
            <li><b>Output:</b> classifier head replaced with identity — 2048-dim pooled feature vector</li>
            <li><b>Normalization:</b> ImageNet mean/std, {resnet_meta['normalization']['note']}</li>
            <li><b>Training:</b> {resnet_meta['training']['optimizer']}, lr {resnet_meta['training']['learning_rate']},
            {resnet_meta['training']['epochs_run']} epochs (best epoch {resnet_meta['training']['best_epoch']})</li>
          </ul>
        </div>''',
        unsafe_allow_html=True,
    )
with col_b:
    st.markdown(
        f'''<div class="card model-card" style="--card-accent: var(--model-b);">
          {card_title_html("layers", "Branch 01 — U-Net", "--model-b")}
          <ul style="color:var(--text-secondary); line-height:1.7; margin:0; padding-left:1.1rem; font-size:0.9rem;">
            <li><b>Architecture:</b> {unet_meta['architecture']['type']}</li>
            <li><b>Encoder:</b> {unet_meta['architecture']['encoder']}</li>
            <li><b>Bottleneck:</b> {unet_meta['architecture']['bottleneck']}</li>
            <li><b>Parameters:</b> {unet_meta['architecture']['n_parameters']:,}</li>
            <li><b>Output:</b> binary leaf mask, threshold {unet_meta['binarization_threshold']} →
            LPF = leaf pixels / total pixels</li>
          </ul>
        </div>''',
        unsafe_allow_html=True,
    )

st.markdown(
    f'''<div class="card">
      {card_title_html("git-merge", "Fusion classification head", "--model-c")}
      <p style="color:var(--text-secondary); line-height:1.6; margin:0 0 0.6rem;">
      Both branches remain <b>frozen</b>; only the fusion head is trained, on top of
      precomputed features. Three comparison models share the same head shape family,
      differing only in input dimensionality:
      </p>
      <ul style="color:var(--text-secondary); line-height:1.7; margin:0; padding-left:1.1rem; font-size:0.9rem;">
        <li><b>Model A (ResNet-only):</b> 2048-dim → Dense(128, ReLU) → Dropout(0.3) → Dense(4, Softmax)</li>
        <li><b>Model B (LPF-only):</b> 1-dim → Dense(16, ReLU) → Dense(4, Softmax)</li>
        <li><b>Model C (Fused):</b> 2049-dim → Dense(128, ReLU) → Dropout(0.3) → Dense(4, Softmax)</li>
      </ul>
    </div>''',
    unsafe_allow_html=True,
)

st.markdown(footer_html(), unsafe_allow_html=True)
