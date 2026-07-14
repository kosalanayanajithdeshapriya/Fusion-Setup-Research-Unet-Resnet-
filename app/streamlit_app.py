"""Router entry point for the multi-page TomatoGrowth AI platform.

Sets up page config, injects the shared CSS, renders the persistent brand
bar, and hands off to Streamlit's native top navigation. Each page under
app/pages/ is a self-contained script (own imports, own content) — this file
only owns what must happen exactly once per run: config, CSS, and the
site-wide header.

Usage:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from common import FAVICON  # noqa: E402
from ui_theme import CUSTOM_CSS, icon_svg  # noqa: E402
from common import render_brand_bar  # noqa: E402

st.set_page_config(
    page_title="TomatoGrowth AI — Growth-Stage Classifier",
    page_icon=str(FAVICON),
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
render_brand_bar(icon_svg)

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/about_research.py", title="About Research", icon=":material/science:"),
    st.Page("pages/model_architecture.py", title="Model Architecture", icon=":material/hub:"),
    st.Page("pages/dataset.py", title="Dataset", icon=":material/dataset:"),
    st.Page("pages/results.py", title="Results", icon=":material/insights:"),
    st.Page("pages/publications.py", title="Publications", icon=":material/menu_book:"),
]
pg = st.navigation(pages, position="top")
pg.run()
