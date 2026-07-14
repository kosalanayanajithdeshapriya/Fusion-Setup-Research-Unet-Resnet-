"""Results page: the actual ablation study — test-set comparison table,
confusion matrices, and training curves for Models A/B/C, plus the
developing/flowering boundary breakdown. All figures come straight from
results/tables and results/plots (scripts/04_evaluate.py's output) — nothing
here is recomputed or re-typed by hand.
"""
import base64
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from common import RESULTS_PLOTS, get_boundary_stats, get_comparison_stats, get_leaf_pipeline_metadata  # noqa: E402
from ui_theme import STAGE_META, card_title_html, footer_html, icon_svg, page_header_html, recommended_ribbon_html  # noqa: E402

st.markdown(
    page_header_html(
        "bar-chart",
        "Results",
        "Test-set ablation study (n = 160, held out) comparing ResNet-only, LPF-only, the fused model, "
        "and the recommended leaf-focused pipeline.",
    ),
    unsafe_allow_html=True,
)

# ---------------------------------- Model D: recommended, evaluated separately --
leaf_meta = get_leaf_pipeline_metadata()
if leaf_meta is not None:
    ct = leaf_meta["comparison_table"]
    full_acc = ct["full_pipeline_test_accuracy"]["unet_crop_aligned"] * 100
    deeplab_acc = ct["full_pipeline_test_accuracy"]["deeplabv3"] * 100
    native_acc = ct["full_pipeline_test_accuracy"]["unet_native"] * 100
    seg_iou = ct["segmentation_both_class_mean_iou"]["unet_crop_aligned"] * 100
    delta_vs_deeplab = full_acc - deeplab_acc
    st.markdown(
        f'''<div class="card model-card recommended" style="--card-accent: var(--model-d);">
          {recommended_ribbon_html("Recommended · Model D")}
          {card_title_html("shield-check", "Leaf-Focused Pipeline (U-Net + masked ResNet50)", "--model-d")}
          <p class="subtitle">Evaluated separately from the A/B/C ablation below — a self-contained
          two-stage pipeline, not a fusion of the same features.</p>
          <div class="stats-row" style="border-top:none; padding-top:0; margin-top:0;">
            <div class="stat-block">
              <span class="icon-chip" style="--chip-color: var(--model-d)">{icon_svg("star", size=19)}</span>
              <div><div class="stat-block-value">{full_acc:.1f}%</div>
              <div class="stat-block-label">Full-pipeline test accuracy</div></div>
            </div>
            <div class="stat-block">
              <span class="icon-chip" style="--chip-color: var(--model-b)">{icon_svg("layers", size=19)}</span>
              <div><div class="stat-block-value">{seg_iou:.1f}%</div>
              <div class="stat-block-label">Segmentation mean IoU (both classes)</div></div>
            </div>
            <div class="stat-block">
              <span class="icon-chip" style="--chip-color: var(--brand-green)">{icon_svg("check-circle", size=19)}</span>
              <div><div class="stat-block-value">+{delta_vs_deeplab:.1f}pp</div>
              <div class="stat-block-label">vs. previously-featured DeepLabV3 pipeline</div></div>
            </div>
          </div>
          <p style="color:var(--text-secondary); font-size:0.83rem; line-height:1.55; margin:0.9rem 0 0;">
          {leaf_meta["preprocessing_fix_history"]}
          </p>
        </div>''',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="section-title" style="font-size:0.9rem;">{icon_svg("bar-chart", size=15)} '
        f'Segmenter comparison — identical test set, identical classifier</div>',
        unsafe_allow_html=True,
    )
    per_class = ct["per_class_pipeline_f1"]
    comp_rows = [
        ("Full-pipeline accuracy", ct["full_pipeline_test_accuracy"]),
        ("Developing F1", per_class["developing"]),
        ("Flowering F1", per_class["flowering"]),
        ("Fruiting F1", per_class["fruiting"]),
        ("Seeding F1", per_class["seeding"]),
    ]
    comp_df = pd.DataFrame(
        [
            {
                "Metric": name,
                "DeepLabV3 (previous)": f'{vals["deeplabv3"] * 100:.1f}%',
                "U-Net native (superseded)": f'{vals["unet_native"] * 100:.1f}%',
                "U-Net crop-aligned (this pipeline)": f'{vals["unet_crop_aligned"] * 100:.1f}%',
            }
            for name, vals in comp_rows
        ]
    )
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
    st.markdown(
        f'<p style="color:var(--text-muted); font-size:0.8rem; line-height:1.5; margin:0.4rem 0 1.5rem;">'
        f'{per_class["flowering"]["note"]} &middot; {per_class["fruiting"]["note"]}</p>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------- A/B/C ablation study --------
st.markdown(
    f'<div class="section-title">{icon_svg("bar-chart", size=17)} A / B / C ablation study — overall metrics</div>',
    unsafe_allow_html=True,
)
stats = get_comparison_stats()
if stats is not None:
    display_cols = ["model", "test_accuracy", "macro_precision", "macro_recall", "macro_f1"]
    table = stats[display_cols].copy()
    table.columns = ["Model", "Test Accuracy", "Macro Precision", "Macro Recall", "Macro F1"]
    for col in table.columns[1:]:
        table[col] = (table[col] * 100).round(2).astype(str) + "%"

    st.dataframe(table, use_container_width=True, hide_index=True)

    cols = st.columns(3)
    for col, (_, row) in zip(cols, stats.iterrows()):
        with col:
            st.markdown(
                f'''<div class="card" style="text-align:center;">
                  <div style="color:var(--text-muted); font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">{row['model']}</div>
                  <div style="font-family:'Outfit',sans-serif; font-weight:800; font-size:1.9rem; color:var(--brand-terracotta); margin-top:0.3rem;">{row['test_accuracy']*100:.2f}%</div>
                  <div style="color:var(--text-muted); font-size:0.78rem;">test accuracy</div>
                </div>''',
                unsafe_allow_html=True,
            )
else:
    st.warning("results/tables/comparison_summary.csv not found — run scripts/04_evaluate.py first.")

# ---------------------------------------------- developing/flowering boundary --
boundary = get_boundary_stats()
if boundary is not None:
    st.markdown(
        f'<div class="card">{card_title_html("alert-triangle", "Developing / flowering boundary", "--stage-flowering")}'
        f'<p class="subtitle">The hardest class pair — tracked separately since it can improve independently of aggregate accuracy.</p></div>',
        unsafe_allow_html=True,
    )
    display = boundary.copy()
    display.columns = [c.replace("_", " ").title() for c in display.columns]
    st.dataframe(display, use_container_width=True, hide_index=True)

# --------------------------------------------------------------- plots ---
confusion_path = RESULTS_PLOTS / "confusion_matrices.png"
curves_path = RESULTS_PLOTS / "training_curves.png"

if confusion_path.exists():
    uri = "data:image/png;base64," + base64.b64encode(confusion_path.read_bytes()).decode("ascii")
    st.markdown(
        f'<div class="card">{card_title_html("layers", "Confusion matrices", "--model-a")}'
        f'<img src="{uri}" style="width:100%; height:auto; border-radius:12px;"/></div>',
        unsafe_allow_html=True,
    )

if curves_path.exists():
    uri = "data:image/png;base64," + base64.b64encode(curves_path.read_bytes()).decode("ascii")
    st.markdown(
        f'<div class="card">{card_title_html("bar-chart", "Training curves", "--model-b")}'
        f'<img src="{uri}" style="width:100%; height:auto; border-radius:12px;"/></div>',
        unsafe_allow_html=True,
    )

st.markdown(footer_html(), unsafe_allow_html=True)
