"""Streamlit demo: upload a tomato plant image and get growth-stage
predictions from all three trained models (ResNet-only, LPF-only, Fused),
side by side, with the Fused model's result presented as the headline answer.

Usage:
    streamlit run app/streamlit_app.py
"""
import base64
import io
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
    chip_html,
    eyebrow_html,
    floating_pill_html,
    footer_html,
    hero_photo_grid_html,
    icon_svg,
    insight_panel_html,
    probability_bars_html,
    stage_badge_html,
)

MODEL_ORDER = ["A_resnet_only", "B_lpf_only", "C_fused"]
COMPARISON_CSV = ROOT / "results" / "tables" / "comparison_summary.csv"
FAVICON = ROOT / "app" / "assets" / "favicon.png"
HERO_DIR = ROOT / "app" / "assets" / "hero"
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


def image_data_uri(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


@st.cache_data
def get_hero_photo_uris():
    """Real dataset sample photos (one per growth stage, test split) for the
    hero collage, encoded once and cached for the life of the process."""
    uris = {}
    for stage in STAGE_META:
        path = HERO_DIR / f"{stage}.jpg"
        if path.exists():
            uris[stage] = "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    return uris


def photo_frame_html(image: Image.Image, pill_html: str = "") -> str:
    """Single unified HTML block (image embedded as a data URI) so the
    floating pill is a real DOM child of .photo-frame — required for
    `position: absolute` to anchor correctly, which a split
    st.markdown()+st.image() pair does not reliably guarantee."""
    uri = image_data_uri(image)
    return (
        f'<div class="photo-frame">'
        f'<img src="{uri}" style="width:100%; height:auto; display:block;"/>'
        f'{pill_html}</div>'
    )


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

# ------------------------------------------------------------- hero header --
chips = "".join(chip_html(stage) for stage in STAGE_META)
st.markdown(
    f"""
    <div class="hero-row">
      <div class="hero-text">
        {eyebrow_html("RESEARCH DEMO &middot; DUAL-BRANCH FUSION MODEL")}
        <h1>Tomato Growth-Stage <span class="accent">Classifier</span></h1>
        <p>Fusing Branch 02 (ResNet50 visual features) with Branch 01 (U-Net leaf-coverage signal) to identify
        seeding, developing, flowering, and fruiting stages from a single photo.</p>
        <div class="chip-row">{chips}</div>
      </div>
      {hero_photo_grid_html(get_hero_photo_uris())}
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Upload a tomato plant image — JPG or PNG, one plant per photo", type=["jpg", "jpeg", "png"])

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
    st.markdown(
        f'<div class="card">{card_title_html("image", "Input image", "--model-a")}'
        f'{photo_frame_html(input_thumb)}</div>',
        unsafe_allow_html=True,
    )
with col_mask:
    pill = floating_pill_html("droplet", f'LPF {result["lpf"]:.4f}', "--model-b")
    st.markdown(
        f'<div class="card">{card_title_html("layers", "U-Net leaf segmentation", "--model-b")}'
        f'{photo_frame_html(mask_thumb, pill)}</div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------ headline result -----
fused = predictions["C_fused"]
st.markdown(
    f'<div class="section-title">{icon_svg("git-merge", size=17)} Final prediction — fused model</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'''<div class="card">
      <div class="result-split">
        <div class="result-left">
          {stage_badge_html(fused["predicted_class"], large=True)}
          <span class="confidence-tag">{fused["confidence"]:.1%} confidence</span>
        </div>
        <div class="result-right">
          {probability_bars_html(class_names, fused["probabilities"], fused["predicted_class"])}
        </div>
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

# -------------------------------------------------------- model insight -----
resnet_pred = predictions["A_resnet_only"]
st.markdown(
    f'<div class="section-title">{icon_svg("git-merge", size=17)} Model insight — what each branch contributes</div>',
    unsafe_allow_html=True,
)
st.markdown(
    insight_panel_html(resnet_pred["predicted_class"], resnet_pred["confidence"], result["lpf"]),
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
              {eyebrow_html(meta["eyebrow"])}
              <h3>{meta["label"]}</h3>
              <p class="subtitle">{meta["subtitle"]}</p>
              <div class="result-row">
                {stage_badge_html(pred["predicted_class"])}
                <span class="confidence-tag">{pred["confidence"]:.1%}</span>
              </div>
              <div style="margin-top:0.8rem;">
                {probability_bars_html(class_names, pred["probabilities"], pred["predicted_class"])}
              </div>
            </div>''',
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------ footer --
st.markdown(footer_html(), unsafe_allow_html=True)
