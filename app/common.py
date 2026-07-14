"""Shared path constants and data loaders used by the router (streamlit_app.py)
and every page under app/pages/. Centralized so every page reads the exact
same real figures (dataset counts, test accuracy, LPF ranges) rather than
each page recomputing or re-typing them independently.
"""
import base64
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

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

MODEL_ORDER = ["A_resnet_only", "B_lpf_only", "C_fused"]


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
def get_test_accuracy(model_key):
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
