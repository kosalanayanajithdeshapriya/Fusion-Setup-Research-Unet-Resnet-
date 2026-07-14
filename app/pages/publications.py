"""Publications page: honest status (no formal publication yet) plus links to
the real related resources that do exist — the source repo, the live demo,
and the broader research portal.
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "app"))
from ui_theme import card_title_html, footer_html, icon_svg, page_header_html  # noqa: E402

st.markdown(
    page_header_html(
        "external-link",
        "Publications & Resources",
        "This is an active undergraduate research prototype — no formal publication yet. "
        "Here's where the real, current material lives.",
    ),
    unsafe_allow_html=True,
)

st.markdown(
    f'''<div class="card">
      {card_title_html("info", "Publication status", "--stage-flowering")}
      <p style="color:var(--text-secondary); line-height:1.6; margin:0;">
      No paper has been published for this project yet — it's an ongoing undergraduate
      research prototype. This page will be updated if and when a manuscript is submitted
      or a preprint is posted.
      </p>
    </div>''',
    unsafe_allow_html=True,
)

resources = [
    (
        "git-merge", "--model-a", "Source code (GitHub)",
        "Full pipeline: feature extraction, fusion training, evaluation, and this app's code.",
        "https://github.com/kosalanayanajithdeshapriya/Fusion-Setup-Research-Unet-Resnet-",
    ),
    (
        "cpu", "--model-c", "Live demo",
        "This application, deployed on Google Cloud Run.",
        "https://tomato-fusion-demo-628712417253.us-central1.run.app",
    ),
    (
        "external-link", "--brand-green", "Research portal",
        "The broader project site covering Branch 01 (U-Net) and Branch 02 (ResNet50) individually.",
        "https://tomatoresearch.vercel.app",
    ),
]

cols = st.columns(3)
for col, (icon_name, color_var, title, desc, url) in zip(cols, resources):
    with col:
        st.markdown(
            f'''<div class="card" style="height:100%;">
              {card_title_html(icon_name, title, color_var)}
              <p style="color:var(--text-secondary); font-size:0.85rem; line-height:1.5; margin:0 0 0.8rem;">{desc}</p>
              <a href="{url}" target="_blank" rel="noopener" style="color:var({color_var}); font-weight:700; font-size:0.85rem; text-decoration:none; display:inline-flex; align-items:center; gap:0.3rem;">
                {icon_svg("external-link", size=13)} Visit</a>
            </div>''',
            unsafe_allow_html=True,
        )

st.markdown(footer_html(), unsafe_allow_html=True)
