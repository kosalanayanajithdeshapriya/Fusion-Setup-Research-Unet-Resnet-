"""Shared path constants and data loaders used by the router (streamlit_app.py)
and every page under app/pages/. Centralized so every page reads the exact
same real figures (dataset counts, test accuracy, LPF ranges) rather than
each page recomputing or re-typing them independently.
"""
import base64
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
HERO_DIR = APP_DIR / "assets" / "hero"
FAVICON = APP_DIR / "assets" / "favicon.png"

INPUTS_DIR = ROOT / "inputs"
RESULTS_DIR = ROOT / "results"
RESULTS_TABLES = RESULTS_DIR / "tables"
RESULTS_PLOTS = RESULTS_DIR / "plots"
LPF_CSV = INPUTS_DIR / "lpf_full_dataset.csv"
COMPARISON_CSV = RESULTS_TABLES / "comparison_summary.csv"
BOUNDARY_CSV = RESULTS_TABLES / "developing_flowering_boundary.csv"
LEAF_PIPELINE_METADATA_JSON = INPUTS_DIR / "leaf_pipeline_metadata.json"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Model D is featured/default per its real, deployment-realistic accuracy
# (see get_leaf_pipeline_metadata) — listed first everywhere. Model E (the
# earlier DeepLabV3-based leaf pipeline) is the second-best model — same
# classifier, an older segmenter — listed right after D.
MODEL_ORDER = ["D_leaf_pipeline", "E_deeplab_pipeline", "A_resnet_only", "B_lpf_only", "C_fused"]


@st.cache_data
def get_dataset_df():
    return pd.read_csv(LPF_CSV)


@st.cache_data
def get_comparison_stats():
    if not COMPARISON_CSV.exists():
        return None
    return pd.read_csv(COMPARISON_CSV)


@st.cache_data
def get_boundary_stats():
    if not BOUNDARY_CSV.exists():
        return None
    return pd.read_csv(BOUNDARY_CSV)


@st.cache_data
def get_hero_photo_uris():
    from ui_theme import STAGE_META
    uris = {}
    for stage in STAGE_META:
        path = HERO_DIR / f"{stage}.jpg"
        if path.exists():
            uris[stage] = "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    return uris


@st.cache_data
def get_lpf_ranges():
    """Real p10-p90 LPF percentile range per stage, computed from the actual
    dataset — not an assumed/invented biological curve."""
    df = get_dataset_df()
    ranges = {}
    for stage, group in df.groupby("growth_stage"):
        ranges[stage] = (group["lpf"].quantile(0.10), group["lpf"].quantile(0.90))
    return ranges


@st.cache_data
def get_leaf_pipeline_metadata():
    """Model D's real metrics, as reported in inputs/leaf_pipeline_metadata.json
    (a self-contained checkpoint export, not produced by scripts/04_evaluate.py,
    so it's kept as its own artifact rather than merged into comparison_summary.csv)."""
    if not LEAF_PIPELINE_METADATA_JSON.exists():
        return None
    with open(LEAF_PIPELINE_METADATA_JSON) as f:
        return json.load(f)


@st.cache_data
def get_test_accuracy(model_key):
    """Test accuracy as a percentage. Model D's headline number is the
    crop-aligned U-Net pipeline's full-pipeline accuracy (its own predicted
    masks, not hand-drawn ones) from comparison_table.full_pipeline_test_accuracy
    — see get_leaf_pipeline_metadata."""
    if model_key == "D_leaf_pipeline":
        meta = get_leaf_pipeline_metadata()
        if meta is None:
            return None
        return meta["comparison_table"]["full_pipeline_test_accuracy"]["unet_crop_aligned"] * 100

    if model_key == "E_deeplab_pipeline":
        meta = get_leaf_pipeline_metadata()
        if meta is None:
            return None
        return meta["comparison_table"]["full_pipeline_test_accuracy"]["deeplabv3"] * 100

    from ui_theme import MODEL_META
    stats = get_comparison_stats()
    if stats is None:
        return None
    meta = MODEL_META[model_key]
    label = f'Model {meta["short"]} ({meta["label"]})'
    row = stats[stats["model"] == label]
    if row.empty:
        return None
    return float(row.iloc[0]["test_accuracy"]) * 100


def render_brand_bar(icon_svg):
    st.markdown(
        f'''<div class="brand-bar">
          <div class="brand-logo">{icon_svg("fruit", size=24)}
            <span>TomatoGrowth<b>AI</b></span>
          </div>
          <div class="brand-tagline">Leaf Density-Based Growth Stage Detection</div>
          <div class="brand-actions">
            <span class="pill-outline">{icon_svg("layers", size=13)} Research Prototype v1.0</span>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )
