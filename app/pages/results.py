"""Results page: the actual ablation study — test-set comparison table,
confusion matrices, and training curves for Models A/B/C, plus the
developing/flowering boundary breakdown. All figures come straight from
results/tables and results/plots (scripts/04_evaluate.py's output) — nothing
here is recomputed or re-typed by hand.
"""
import base64
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from common import RESULTS_PLOTS, get_boundary_stats, get_comparison_stats  # noqa: E402
from ui_theme import STAGE_META, card_title_html, footer_html, page_header_html  # noqa: E402

st.markdown(
    page_header_html(
        "bar-chart",
        "Results",
        "Test-set ablation study (n = 160, held out) comparing ResNet-only, LPF-only, and the fused model.",
    ),
    unsafe_allow_html=True,
)

stats = get_comparison_stats()
if stats is not None:
    display_cols = ["model", "test_accuracy", "macro_precision", "macro_recall", "macro_f1"]
    table = stats[display_cols].copy()
    table.columns = ["Model", "Test Accuracy", "Macro Precision", "Macro Recall", "Macro F1"]
    for col in table.columns[1:]:
        table[col] = (table[col] * 100).round(2).astype(str) + "%"

    st.markdown(f'<div class="card">{card_title_html("bar-chart", "Ablation study — overall metrics", "--brand-terracotta")}</div>', unsafe_allow_html=True)
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
