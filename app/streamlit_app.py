"""Streamlit demo: upload a tomato plant image and get growth-stage
predictions from all three trained models (ResNet-only, LPF-only, Fused),
side by side, with the Fused model's result presented as the headline answer.

Usage:
    streamlit run app/streamlit_app.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from inference import FusionPredictor  # noqa: E402
from ui_theme import (  # noqa: E402
    CUSTOM_CSS,
    MODEL_META,
    STAGE_META,
    card_title_html,
    eyebrow_html,
    icon_svg,
    probability_bars_html,
    stage_badge_html,
)

MODEL_ORDER = ["A_resnet_only", "B_lpf_only", "C_fused"]
COMPARISON_CSV = ROOT / "results" / "tables" / "comparison_summary.csv"
FAVICON = ROOT / "app" / "assets" / "favicon.png"
THUMB_SIZE = 220

st.set_page_config(page_title="Tomato Growth-Stage Classifier", page_icon=str(FAVICON), layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_predictor():
    return FusionPredictor()


@st.cache_data
def get_model_stats():
    if not COMPARISON_CSV.exists():
        return None
    return pd.read_csv(COMPARISON_CSV)


def to_square_thumbnail(image: Image.Image, size: int = THUMB_SIZE) -> Image.Image:
    """Center-crop and resize to a fixed square so unrelated-aspect-ratio
    images (the original upload vs. the U-Net's fixed 224x224 mask) display
    at identical, small, matched dimensions side by side."""
    image = image.convert("RGB")
    w, h = image.size
    scale = size / min(w, h)
    new_w, new_h = round(w * scale), round(h * scale)
    image = image.resize((new_w, new_h), Image.LANCZOS)
    left, top = (new_w - size) // 2, (new_h - size) // 2
    return image.crop((left, top, left + size, top + size))


# ---------------------------------------------------------------- sidebar ---
with st.sidebar:
    st.markdown(
        f'<div class="sidebar-title">{icon_svg("fruit", size=20)} About this pipeline</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "A **dual-branch fusion model** for classifying tomato plant growth stage "
        "from a single photo."
    )
    with st.expander("How it works", icon=":material/info:", expanded=True):
        st.markdown(
            f'{icon_svg("layers", size=14)} &nbsp;**Branch 01 — U-Net** &nbsp; segments the leaf area, reduces it to a '
            "**1-dim** Leaf Pixel Fraction (LPF).\n\n"
            f'{icon_svg("image", size=14)} &nbsp;**Branch 02 — CNN (ResNet50)** &nbsp; strips the classifier head, '
            "outputs a **2048-dim** visual feature vector.\n\n"
            f'{icon_svg("git-merge", size=14)} &nbsp;**Fusion layer** &nbsp; concatenates both (2049-dim) into a small '
            "MLP head that predicts the final growth stage.",
            unsafe_allow_html=True,
        )

    stats = get_model_stats()
    if stats is not None:
        st.markdown(
            f'<div class="sidebar-title" style="margin-top:1.1rem;">{icon_svg("bar-chart", size=18)} Test-set accuracy</div>',
            unsafe_allow_html=True,
        )
        for name in MODEL_ORDER:
            meta = MODEL_META[name]
            expected_label = f'Model {meta["short"]} ({meta["label"]})'
            row = stats[stats["model"] == expected_label]
            if not row.empty:
                acc = row.iloc[0]["test_accuracy"] * 100
                st.markdown(
                    f'<div class="stat-pill"><span>{meta["short"]} — {meta["label"]}</span>'
                    f'<b>{acc:.1f}%</b></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.caption("Growth stages")
    for stage in STAGE_META:
        st.markdown(stage_badge_html(stage), unsafe_allow_html=True)

# ------------------------------------------------------------- hero header --
st.markdown(
    f"""
    <div class="hero-banner">
      {eyebrow_html("RESEARCH DEMO &middot; DUAL-BRANCH FUSION MODEL")}
      <div class="title-row">{icon_svg("fruit", size=30)}<h1>Tomato Growth-Stage <span class="accent">Classifier</span></h1></div>
      <p>Fusing Branch 02 (ResNet50 visual features) with Branch 01 (U-Net leaf-coverage signal) to identify
      seeding, developing, flowering, and fruiting stages from a single photo.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Upload a tomato plant image", type=["jpg", "jpeg", "png"])

if uploaded is None:
    st.info("Upload a .jpg / .jpeg / .png image to get a prediction.")
    st.stop()

with st.spinner("Loading models..."):
    predictor = get_predictor()

suffix = Path(uploaded.name).suffix or ".jpg"
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(uploaded.getvalue())
    tmp_path = tmp.name

try:
    with st.spinner("Running ResNet50 + U-Net inference..."):
        result = predictor.predict(tmp_path)
finally:
    Path(tmp_path).unlink(missing_ok=True)

class_names = result["class_names"]
predictions = result["predictions"]

input_thumb = to_square_thumbnail(Image.open(uploaded))
mask_uint8 = (np.clip(result["mask"], 0, 1) * 255).astype(np.uint8)
mask_thumb = to_square_thumbnail(Image.fromarray(mask_uint8).convert("RGB"))

# --------------------------------------------------------- image + mask -----
col_img, col_mask = st.columns(2)
with col_img:
    st.markdown(f'<div class="card">{card_title_html("image", "Input image", "--model-a")}', unsafe_allow_html=True)
    st.markdown('<div class="thumb-wrap">', unsafe_allow_html=True)
    st.image(input_thumb, width=THUMB_SIZE)
    st.markdown("</div></div>", unsafe_allow_html=True)
with col_mask:
    st.markdown(
        f'<div class="card">{card_title_html("layers", "U-Net leaf segmentation", "--model-b")}'
        f'<p class="subtitle">Leaf Pixel Fraction (LPF) = {result["lpf"]:.4f}</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="thumb-wrap">', unsafe_allow_html=True)
    st.image(mask_thumb, width=THUMB_SIZE)
    st.markdown("</div></div>", unsafe_allow_html=True)

# ------------------------------------------------------ headline result -----
fused = predictions["C_fused"]
st.markdown(
    f'<div class="section-title">{icon_svg("git-merge", size=17)} Final prediction — Fused model</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'''<div class="card" style="text-align:center; padding:1.6rem;">
      <div class="result-row" style="justify-content:center;">
        {stage_badge_html(fused["predicted_class"], large=True)}
        <span class="confidence-tag">{fused["confidence"]:.1%} confidence</span>
      </div>
      <div style="max-width:400px; margin:1rem auto 0;">
        {probability_bars_html(class_names, fused["probabilities"])}
      </div>
    </div>''',
    unsafe_allow_html=True,
)

predicted_classes = {name: predictions[name]["predicted_class"] for name in MODEL_ORDER}
if len(set(predicted_classes.values())) > 1:
    st.markdown(
        f'<div class="agree-banner warn">{icon_svg("alert-triangle", size=17)} '
        f'Models disagree on the predicted growth stage — see the comparison below.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="agree-banner ok">{icon_svg("check-circle", size=17)} '
        f'All three models agree on this prediction.</div>',
        unsafe_allow_html=True,
    )

# ----------------------------------------------------- model comparison -----
st.markdown(
    f'<div class="section-title">{icon_svg("bar-chart", size=17)} Model comparison</div>',
    unsafe_allow_html=True,
)
cols = st.columns(3)
for col, name in zip(cols, MODEL_ORDER):
    pred = predictions[name]
    meta = MODEL_META[name]
    with col:
        st.markdown(
            f'''<div class="card model-card" style="--card-accent: var({meta["var"]});">
              {eyebrow_html(meta["eyebrow"], meta["var"])}
              <h3>{meta["label"]}</h3>
              <p class="subtitle">{meta["subtitle"]}</p>
              <div class="result-row">
                {stage_badge_html(pred["predicted_class"])}
                <span class="confidence-tag">{pred["confidence"]:.1%}</span>
              </div>
              <div style="margin-top:0.8rem;">
                {probability_bars_html(class_names, pred["probabilities"])}
              </div>
            </div>''',
            unsafe_allow_html=True,
        )
