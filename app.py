"""Who Controls AI Innovation? - 36104 Assignment 3 data narrative.

Run from the project root:  streamlit run app.py

This file is the shared frame only: title, question and tabs.
Each tab lives in its own folder under dashboards/, with its own data and
code, and is listed in DASHBOARDS below.
"""

import streamlit as st

from core.page import load_page, render_page

# Tab order. Each entry is a folder in dashboards/ that exposes a PAGE.
DASHBOARDS = [
    "dashboards.tab1_builders",
    "dashboards.tab2_compute",
    "dashboards.tab3_capital",
    "dashboards.tab4_capability",
]

st.set_page_config(page_title="Who Controls AI Innovation?", layout="wide")

pages = [load_page(name) for name in DASHBOARDS]

st.title("Who controls AI Innovation?")
st.markdown("### Is Cutting-Edge AI Development being restricted and concentrated into fewer organisations?")
st.markdown(
    "Reasonable people disagree. One side points to a handful of US companies "
    "with the chips, the cash and the record-breaking training runs. The other "
    "points to open-weight models that catch up within months and a growing "
    "list of labs, many in China, releasing large models. Each tab follows one "
    "link in the supply chain: **models → compute → capital → capability**.")

for tab, page in zip(st.tabs([p.label for p in pages]), pages):
    with tab:
        render_page(page)

st.divider()
st.caption(
    "Each tab's data sources are listed in its folder in dashboards/. "
    "36104 Data Visualisation and Narratives, Assignment 3.")
