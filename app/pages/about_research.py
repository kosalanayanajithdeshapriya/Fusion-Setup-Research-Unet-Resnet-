"""About Research page: project motivation, why fusion, and why the two
branches are trained separately. Content adapted from README.md — not new
claims, just presented visually rather than as raw markdown.
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from ui_theme import card_title_html, footer_html, icon_svg, page_header_html  # noqa: E402

st.markdown(
    page_header_html(
        "shield-check",
        "About This Research",
        "Why fuse leaf density with visual features, and why the two branches are trained independently.",
    ),
    unsafe_allow_html=True,
)

st.markdown(
    f'''<div class="card">
      {card_title_html("info", "The problem", "--brand-terracotta")}
      <p style="color:var(--text-secondary); line-height:1.6; margin:0;">
      Most existing tomato/plant growth-stage systems classify using CNN visual features alone.
      This project tests whether an interpretable, domain-meaningful structural signal —
      <b>leaf density</b>, derived from segmentation — adds value on top of deep visual features,
      and reports the result honestly, including a null result at the aggregate level alongside
      a principled explanation (see <a href="/results" target="_self">Results</a>).
      </p>
    </div>''',
    unsafe_allow_html=True,
)

st.markdown(
    f'''<div class="card">
      {card_title_html("git-merge", "Why two branches, trained separately", "--model-b")}
      <ul style="color:var(--text-secondary); line-height:1.7; margin:0; padding-left:1.2rem;">
        <li>The branches need different supervision: ResNet50 uses image-level growth-stage
        labels, while U-Net needs pixel-level segmentation masks — a smaller, separately
        annotated subset.</li>
        <li>Training separately keeps each branch's contribution isolated and independently
        evaluable — see the <a href="/results" target="_self">ablation study</a> comparing
        ResNet-only, LPF-only, and Fused models.</li>
        <li>It matches the practical annotation constraints of a self-collected,
        partially-annotated dataset.</li>
      </ul>
    </div>''',
    unsafe_allow_html=True,
)

st.markdown(
    f'''<div class="card">
      {card_title_html("shield-check", "What this project reports honestly", "--model-c")}
      <p style="color:var(--text-secondary); line-height:1.6; margin:0;">
      Fusion is comparable to, but does not yet exceed, the ResNet-only baseline in aggregate
      accuracy on this dataset — the likely cause is dimensionality imbalance at concatenation
      (a single LPF scalar diluted against 2048 CNN dimensions). This is tracked as an open
      limitation rather than smoothed over; see the Dataset and Results pages for the full
      picture, including the developing/flowering boundary case specifically.
      </p>
    </div>''',
    unsafe_allow_html=True,
)

st.markdown(footer_html(), unsafe_allow_html=True)
