"""Home page: hero, upload + how-it-works, and the live demo (upload -> predict
-> results). This is the page users land on and the one that actually runs
inference; every other page is informational.
"""
import base64
import io
import sys
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from common import get_hero_photo_uris, get_lpf_ranges, get_test_accuracy  # noqa: E402
from inference import FusionPredictor  # noqa: E402
from ui_theme import (  # noqa: E402
    MODEL_META,
    STAGE_META,
    card_title_html,
    chip_html,
    cta_row_html,
    eyebrow_html,
    feature_row_html,
    floating_pill_html,
    footer_html,
    hero_photo_hero_html,
    icon_svg,
    insight_panel_html,
    probability_bars_html,
    stage_badge_html,
    stage_range_list_html,
    step_flow_html,
    stats_row_html,
)

MODEL_ORDER = ["A_resnet_only", "B_lpf_only", "C_fused"]
THUMB_SIZE = 220

# Real, previously-verified example (test-split photo, full pipeline run) —
# shown on the hero before any user upload. Not fabricated: this is the
# actual computed output for app/assets/hero/flowering.jpg's source image.
EXAMPLE_STAGE = "flowering"
EXAMPLE_LPF = 0.2329
EXAMPLE_CONFIDENCE = 1.0


@st.cache_resource
def get_predictor():
    return FusionPredictor()


def to_square_thumbnail(image: Image.Image, size: int = THUMB_SIZE) -> Image.Image:
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


def photo_frame_html(image: Image.Image, pill_html: str = "") -> str:
    uri = image_data_uri(image)
    return (
        f'<div class="photo-frame">'
        f'<img src="{uri}" style="width:100%; height:auto; display:block;"/>'
        f'{pill_html}</div>'
    )


# ==================================================================== hero ===
chips = "".join(chip_html(stage) for stage in STAGE_META)
feature_items = [
    ("droplet", "Leaf Coverage Estimation", "--model-b"),
    ("layers", "Leaf Density Analysis", "--model-b"),
    ("cpu", "Deep Feature Extraction", "--model-a"),
    ("bar-chart", "Growth Stage Classification", "--brand-terracotta"),
    ("shield-check", "Explainable AI Prediction", "--model-c"),
]
cta_buttons = [
    ("Try Live Demo", "arrow-right", "primary", "#upload-a-tomato-plant-image"),
    ("Explore Research", "external-link", "secondary", None),
]

hero_uris = get_hero_photo_uris()
lpf_ranges = get_lpf_ranges()

col_text, col_photo, col_ranges = st.columns([1.15, 1, 0.62], gap="medium")
with col_text:
    st.markdown(
        f'''{eyebrow_html("RESEARCH PROTOTYPE &middot; DUAL-BRANCH FUSION MODEL")}
        <h1 style="font-family:'Outfit',sans-serif; font-weight:800; font-size:clamp(1.6rem,3.6vw,2.3rem); line-height:1.15; margin:0; color:var(--text-primary);">
          Tomato Leaf Density-Based Growth <span class="accent" style="color:var(--brand-terracotta)">Stage Detection</span>
        </h1>
        <p style="color:var(--text-secondary); margin:0.8rem 0 0; font-size:0.98rem; max-width:520px;">
          A dual-branch deep learning framework that fuses U-Net leaf-coverage estimation with
          ResNet50 visual features to classify tomato growth stages from a single RGB image.
        </p>
        {feature_row_html(feature_items)}
        {cta_row_html(cta_buttons)}
        ''',
        unsafe_allow_html=True,
    )
with col_photo:
    if EXAMPLE_STAGE in hero_uris:
        st.markdown(
            hero_photo_hero_html(hero_uris[EXAMPLE_STAGE], EXAMPLE_LPF * 100, EXAMPLE_STAGE, EXAMPLE_CONFIDENCE),
            unsafe_allow_html=True,
        )
with col_ranges:
    st.markdown(f'<div class="section-title" style="font-size:0.85rem; margin-top:0;">Typical Leaf Coverage by Stage</div>', unsafe_allow_html=True)
    st.markdown(stage_range_list_html(lpf_ranges, active_stage=EXAMPLE_STAGE), unsafe_allow_html=True)

st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)

# ---------------------------------------------------- upload + how it works --
st.markdown('<a id="upload-a-tomato-plant-image"></a>', unsafe_allow_html=True)
col_upload, col_how = st.columns([1, 1.1], gap="medium")
with col_upload:
    st.markdown(
        f'<div class="card">{card_title_html("upload", "Upload Tomato Plant Image", "--brand-terracotta")}'
        f'<p class="subtitle">Upload a clear image of a single tomato plant (JPG, JPEG, PNG)</p></div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Upload a tomato plant image — JPG or PNG, one plant per photo", type=["jpg", "jpeg", "png"])
with col_how:
    steps = [
        ("upload", "Upload Image", "Input a single tomato plant image"),
        ("layers", "Dual-Branch Processing", "U-Net (Branch 01) estimates leaf coverage; ResNet50 (Branch 02) extracts visual features"),
        ("git-merge", "Feature Fusion", "Concatenate the 2048-dim visual vector with the 1-dim LPF signal"),
        ("bar-chart", "Stage Prediction", "Fusion MLP predicts the growth stage with a confidence score"),
    ]
    st.markdown(
        f'<div class="card">{card_title_html("cpu", "How It Works", "--model-a")}{step_flow_html(steps)}</div>',
        unsafe_allow_html=True,
    )

acc_a = get_test_accuracy("A_resnet_only")
acc_c = get_test_accuracy("C_fused")
stats = [
    ("image", "982", "Total Images", "--model-a"),
    ("leaf", "4", "Growth Stages", "--model-b"),
    ("bar-chart", f"{acc_c:.1f}%" if acc_c else "—", "Fused Test Accuracy", "--brand-terracotta"),
    ("check-circle", "160", "Held-out Test Images", "--model-c"),
]
st.markdown(stats_row_html(stats), unsafe_allow_html=True)

if uploaded is None:
    st.info("Upload a .jpg / .jpeg / .png image above to get a prediction.")
    st.markdown(footer_html(), unsafe_allow_html=True)
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

st.markdown(footer_html(), unsafe_allow_html=True)
