"""Dataset page: real counts, split breakdown, sample images per stage, and
the actual measured LPF distribution per class (not an assumed/invented
biological curve — computed directly from inputs/lpf_full_dataset.csv).
"""
import base64
import io
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from common import get_dataset_df, get_hero_photo_uris  # noqa: E402
from ui_theme import STAGE_META, card_title_html, footer_html, hero_photo_grid_html, page_header_html, stats_row_html  # noqa: E402

df = get_dataset_df()

st.markdown(
    page_header_html(
        "layers",
        "Dataset",
        "A self-collected, greenhouse-photographed tomato plant dataset spanning all four growth stages.",
    ),
    unsafe_allow_html=True,
)

total = len(df)
split_counts = df["split"].value_counts()
class_counts = df["growth_stage"].value_counts()

stats = [
    ("image", f"{total}", "Total Images", "--model-a"),
    ("layers", f"{int(split_counts.get('train', 0))}", "Train", "--model-b"),
    ("check-circle", f"{int(split_counts.get('valid', 0))}", "Validation", "--brand-terracotta"),
    ("bar-chart", f"{int(split_counts.get('test', 0))}", "Test (held out)", "--model-c"),
]
st.markdown(f'<div class="card">{card_title_html("bar-chart", "Dataset at a glance", "--brand-terracotta")}{stats_row_html(stats)}</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="card">{card_title_html("image", "Sample images per growth stage", "--model-a")}'
    f'<p class="subtitle">One held-out test-split sample per class</p>'
    f'{hero_photo_grid_html(get_hero_photo_uris())}</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------- per-class breakdown ---
st.markdown(f'<div class="section-title">Per-class image counts</div>', unsafe_allow_html=True)
cols = st.columns(4)
for col, stage in zip(cols, STAGE_META):
    meta = STAGE_META[stage]
    count = int(class_counts.get(stage, 0))
    pct = count / total * 100
    with col:
        st.markdown(
            f'''<div class="card" style="text-align:center;">
              <div style="color:var({meta["var"]}); font-family:'Outfit',sans-serif; font-weight:800; font-size:1.6rem;">{count}</div>
              <div style="color:var(--text-muted); font-size:0.8rem; margin-top:0.2rem;">{meta["label"]} &middot; {pct:.0f}%</div>
            </div>''',
            unsafe_allow_html=True,
        )


@st.cache_data
def render_lpf_distribution_chart():
    """Real measured LPF (Leaf Pixel Fraction) distribution per class —
    computed from the dataset, not an assumed monotonic curve. Colors reuse
    the same validated stage palette used throughout the app."""
    order = list(STAGE_META.keys())
    colors = {
        "seeding": "#6E4FA6", "developing": "#1F8A5F",
        "flowering": "#C1622E", "fruiting": "#B03A2E",
    }
    data = [df[df["growth_stage"] == s]["lpf"].values * 100 for s in order]
    labels = [STAGE_META[s]["label"] for s in order]

    plt.rcParams.update({
        "figure.facecolor": "#F6EFE2", "axes.facecolor": "#F6EFE2",
        "axes.edgecolor": "#948A76", "text.color": "#241C12",
        "xtick.color": "#6B6152", "ytick.color": "#241C12",
        "font.family": "sans-serif", "axes.labelcolor": "#241C12",
    })
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    box = ax.boxplot(
        data, vert=False, labels=labels, patch_artist=True,
        widths=0.55, showfliers=True,
        medianprops={"color": "#241C12", "linewidth": 1.6},
        flierprops={"markersize": 3, "markerfacecolor": "#948A76", "markeredgecolor": "none"},
    )
    for patch, stage in zip(box["boxes"], order):
        patch.set_facecolor(colors[stage])
        patch.set_alpha(0.55)
        patch.set_edgecolor(colors[stage])
    for whisker in box["whiskers"]:
        whisker.set_color("#948A76")
    for cap in box["caps"]:
        cap.set_color("#948A76")
    ax.set_xlabel("Leaf Pixel Fraction (%)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linewidth=0.5, color="#e1ddd0")
    ax.set_axisbelow(True)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


st.markdown(
    f'<div class="card">{card_title_html("bar-chart", "Measured leaf coverage (LPF) by stage", "--model-b")}'
    f'<p class="subtitle">Box plot of the actual per-image LPF values in the dataset — developing has the '
    f'highest median leaf coverage, not fruiting, since fruit weight and partial occlusion reduce visible '
    f'leaf area once fruiting begins.</p>'
    f'<img src="{render_lpf_distribution_chart()}" style="width:100%; height:auto; border-radius:12px;"/></div>',
    unsafe_allow_html=True,
)

st.markdown(footer_html(), unsafe_allow_html=True)
