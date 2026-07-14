"""Home page: hero, upload + how-it-works, and the live demo (upload -> predict
-> results). This is the page users land on and the one that actually runs
inference; every other page is informational.

Model D (the leaf-focused segment-then-classify pipeline) is the featured/
default architecture: it's shown first in the hero copy, headlines the
"Final prediction" section with a Recommended ribbon, and leads the model
comparison grid — per its real, deployment-realistic full-pipeline accuracy
(see inputs/leaf_pipeline_metadata.json's comparison_table). Models A/B/C
remain fully shown as the underlying ablation/comparison study.
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
from common import MODEL_ORDER, get_hero_photo_uris, get_leaf_pipeline_metadata, get_lpf_ranges, get_test_accuracy  # noqa: E402
from inference import FusionPredictor  # noqa: E402
from ui_theme import (  # noqa: E402
    MODEL_META,
    STAGE_META,
    card_title_html,
    chip_html,
    cta_row_html,
    eyebrow_html,
    feature_row_html,
    footer_html,
    hero_photo_hero_html,
    icon_svg,
    insight_panel_html,
    probability_bars_html,
    recommended_ribbon_html,
    stage_badge_html,
    stage_range_list_html,
    step_flow_html,
    stats_row_html,
)

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
    ("shield-check", "Background-Robust Segmentation", "--model-d"),
    ("layers", "Leaf Region Masking", "--model-b"),
    ("cpu", "Deep Feature Extraction", "--model-a"),
    ("bar-chart", "Growth Stage Classification", "--brand-terracotta"),
    ("droplet", "Leaf Density Analysis", "--model-b"),
]
cta_buttons = [
    ("Try Live Demo", "arrow-right", "primary", "#upload-a-tomato-plant-image"),
    ("Explore Research", "external-link", "secondary", None),
]

hero_uris = get_hero_photo_uris()
lpf_ranges = get_lpf_ranges()
acc_d = get_test_accuracy("D_leaf_pipeline")

col_text, col_ranges, col_photo = st.columns([1.15, 0.62, 1], gap="medium")
with col_text:
    st.markdown(
        f'''{eyebrow_html(icon_svg("star", size=12) + " RECOMMENDED &middot; LEAF-FOCUSED SEGMENT + CLASSIFY PIPELINE")}
        <h1 style="font-family:'Outfit',sans-serif; font-weight:800; font-size:clamp(1.6rem,3.6vw,2.3rem); line-height:1.15; margin:0; color:var(--text-primary);">
          Tomato Leaf Density-Based Growth <span class="accent" style="color:var(--brand-terracotta)">Stage Detection</span>
        </h1>
        <p style="color:var(--text-secondary); margin:0.8rem 0 0; font-size:0.98rem; max-width:520px;">
          A U-Net segmentation stage masks out the background — using the same crop-aligned
          preprocessing as the classifier, so the mask actually lines up with what it sees —
          then a ResNet50 classifier reads growth stage from leaf material only. No shortcut
          through greenhouse or pot context available, which is why its {f"{acc_d:.1f}%" if acc_d else "—"} test
          accuracy is the most realistic number across all five models compared here.
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
        ("upload", "Upload Image", "Input a single tomato plant image, any size"),
        ("layers", "Segment Plant Region", "U-Net predicts a binary plant/background mask on a crop-aligned 224×224 image"),
        ("shield-check", "Mask & Classify", "Background is zeroed out; ResNet50 classifies from leaf material only"),
        ("bar-chart", "Stage Prediction", "Growth stage + confidence, robust to background/environment changes"),
    ]
    st.markdown(
        f'<div class="card">{card_title_html("cpu", "How the Recommended Pipeline Works", "--model-d")}{step_flow_html(steps)}</div>',
        unsafe_allow_html=True,
    )

stats = [
    ("image", "982", "Total Images", "--model-a"),
    ("leaf", "4", "Growth Stages", "--model-b"),
    ("star", f"{acc_d:.1f}%" if acc_d else "—", "Recommended Model Accuracy", "--model-d"),
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
    with st.spinner("Running segmentation + classification (all 4 models)..."):
        result = predictor.predict(tmp_path)
finally:
    Path(tmp_path).unlink(missing_ok=True)

class_names = result["class_names"]
predictions = result["predictions"]

input_thumb = to_square_thumbnail(Image.open(uploaded))
leaf_mask_uint8 = (np.clip(result["leaf_mask"], 0, 1) * 255).astype(np.uint8)
leaf_mask_thumb = to_square_thumbnail(Image.fromarray(leaf_mask_uint8).convert("RGB"))
deeplab_mask_uint8 = (np.clip(result["deeplab_mask"], 0, 1) * 255).astype(np.uint8)
deeplab_mask_thumb = to_square_thumbnail(Image.fromarray(deeplab_mask_uint8).convert("RGB"))

# ----------------------------------------------------- image + both masks ---
col_img, col_leaf_mask, col_deeplab_mask = st.columns(3)
with col_img:
    st.markdown(
        f'<div class="card">{card_title_html("image", "Input image", "--model-a")}'
        f'{photo_frame_html(input_thumb)}</div>',
        unsafe_allow_html=True,
    )
with col_leaf_mask:
    st.markdown(
        f'<div class="card">{card_title_html("shield-check", "U-Net plant mask (crop-aligned)", "--model-d")}'
        f'<p class="subtitle">Model D\'s segmentation stage</p>'
        f'{photo_frame_html(leaf_mask_thumb)}</div>',
        unsafe_allow_html=True,
    )
with col_deeplab_mask:
    st.markdown(
        f'<div class="card">{card_title_html("shield-check", "DeepLabV3 plant mask", "--model-e")}'
        f'<p class="subtitle">Model E\'s segmentation stage</p>'
        f'{photo_frame_html(deeplab_mask_thumb)}</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------- headline result (Model D) ---
featured = predictions["D_leaf_pipeline"]
st.markdown(
    f'<div class="section-title">{icon_svg("star", size=17)} Final prediction — recommended model</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'''<div class="card model-card recommended" style="--card-accent: var(--model-d);">
      {recommended_ribbon_html("Recommended · Model D")}
      <div class="result-split">
        <div class="result-left">
          {stage_badge_html(featured["predicted_class"], large=True)}
          <span class="confidence-tag">{featured["confidence"]:.1%} confidence</span>
        </div>
        <div class="result-right">
          {probability_bars_html(class_names, featured["probabilities"], featured["predicted_class"])}
        </div>
      </div>
    </div>''',
    unsafe_allow_html=True,
)
leaf_meta = get_leaf_pipeline_metadata()
_ct = leaf_meta["comparison_table"] if leaf_meta else None
_deeplab_acc = _ct["full_pipeline_test_accuracy"]["deeplabv3"] * 100 if _ct else None
_native_acc = _ct["full_pipeline_test_accuracy"]["unet_native"] * 100 if _ct else None
st.markdown(
    f'''<div class="card" style="border-left: 3px solid var(--model-d);">
      <p style="margin:0; color:var(--text-secondary); font-size:0.85rem; line-height:1.55;">
      {icon_svg("info", size=13)} <b>Why this model is featured:</b> a whole-image ResNet50 classifier
      can score higher in raw accuracy, but ablation testing found it partly relies on
      background/greenhouse context — accuracy on the fruiting class collapsed to 0% once
      background was removed at evaluation time. This pipeline masks the background out
      <i>before</i> classifying, so that shortcut isn't available. It also fixes a subtler issue:
      an earlier version fed the segmentation stage different preprocessing than the classifier
      expected, misaligning the predicted mask with the image the classifier actually sees —
      correcting that alone raised full-pipeline accuracy from {f"{_native_acc:.1f}%" if _native_acc else "—"}
      to {f"{acc_d:.1f}%" if acc_d else "—"} with no change in segmentation quality. All told, its
      {f"{acc_d:.1f}%" if acc_d else "—"} test accuracy — using the segmentation model's own predicted
      masks, not hand-drawn ones, and beating Model E's (the second-best, DeepLabV3-based pipeline
      below) {f"{_deeplab_acc:.1f}%" if _deeplab_acc else "—"} — is the most realistic estimate of
      performance on new photos from different environments.
      </p>
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
        f'All five models agree on this prediction.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------- model insight (Model C fusion) --
resnet_pred = predictions["A_resnet_only"]
st.markdown(
    f'<div class="section-title">{icon_svg("git-merge", size=17)} Model C insight — how the ResNet + U-Net fusion works</div>',
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
cols = st.columns(len(MODEL_ORDER))
for col, name in zip(cols, MODEL_ORDER):
    pred = predictions[name]
    meta = MODEL_META[name]
    with col:
        recommended = meta.get("recommended", False)
        second_best = meta.get("second_best", False)
        card_class = "card model-card recommended" if recommended else "card model-card"
        if recommended:
            ribbon = recommended_ribbon_html("Recommended", accent_var="--model-d")
        elif second_best:
            ribbon = recommended_ribbon_html("2nd Best", accent_var="--model-e", icon="check-circle")
        else:
            ribbon = ""
        st.markdown(
            f'<div class="{card_class}" style="--card-accent: var({meta["var"]});">'
            f'{ribbon}'
            f'{eyebrow_html(meta["eyebrow"])}'
            f'<h3>{meta["label"]}</h3>'
            f'<p class="subtitle">{meta["subtitle"]}</p>'
            f'<div class="result-row">'
            f'{stage_badge_html(pred["predicted_class"])}'
            f'<span class="confidence-tag">{pred["confidence"]:.1%}</span>'
            f'</div>'
            f'<div style="margin-top:0.8rem;">'
            f'{probability_bars_html(class_names, pred["probabilities"], pred["predicted_class"])}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown(footer_html(), unsafe_allow_html=True)
