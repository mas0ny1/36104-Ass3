# Who controls AI Innovation?

36104 Data Visualisation and Narratives, Assignment 3: an interactive data
narrative built with Streamlit.

**Question:** *Are Cutting Edge AI Development being retricted and concentrated into fewer organisations?*

| Tab | Folder | Sub-question | Owner | Status |
|---|---|---|---|---|
| 1 · Mason | [`dashboards/tab1_builders`](dashboards/tab1_builders) | Who is producing notable and frontier models? | Mason
| 2 · Compute | [`dashboards/tab2_compute`](dashboards/tab2_compute) | Who owns the chips and the clusters? | 
| 3 · Capital | [`dashboards/tab3_capital`](dashboards/tab3_capital) | Where is the money going? | 
| 4 · Capability | [`dashboards/tab4_capability`](dashboards/tab4_capability) | Is the gap between the leaders and everyone else closing? | 

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py                                  # the full dashboard
```

## Layout

```
app.py                     base app: title, question, one tab per dashboard
core/                      shared base code, used by every tab
  page.py                  Page contract, error isolation, standalone runner
  theme.py                 chart colours for light and dark mode
dashboards/
  tab1_builders/           
    __init__.py              PAGE: label, question, owner
    app.py                   runs this tab on its own
    README.md                data sources log and processing steps
    data/raw/                downloaded files, never edited by hand
    src/loading.py           read and clean the raw files
    src/analysis.py          calculations
    src/views.py             charts and page layout
  tab2_compute/            same layout
  tab3_capital/            same layout
  tab4_capability/         same layout
requirements.txt           one environment for the whole app
```

## Working on your tab

**Stay inside your own folder.** Everything you need is in
`dashboards/tabN_<name>/`:

1. Put downloads in `data/raw/<source>/` and log each file in your folder's
   `README.md`: source URL, download date, licence and row count.
2. Clean the files in `src/loading.py`. Load paths relative to the folder
   (`RAW_DIR` is already set up), never relative to where you run Streamlit.
3. Do calculations in `src/analysis.py`.
4. Replace `render()` in `src/views.py` with your charts. Get colours from
   `core.theme.colours()`. Don't call `st.set_page_config`; the base app does that.
5. **Prefix every widget key with your tab name**, e.g.
   `key="compute_year_range"`. Widget keys are shared across the whole app,
   so two tabs using the same key will clash.
6. Put your name in `owner` in your `__init__.py`.

**Shared files:** `app.py`, `core/` and `requirements.txt` affect everyone.
Agree on changes with the group before editing them. If you need a new
package, add it to `requirements.txt` with an exact version.

## Data licence

Epoch AI data is CC-BY 4.0. Each tab's README holds full citations for its files.
