# Who controls frontier AI?

36104 Data Visualisation and Narratives, Assignment 3: an interactive data
narrative built with Streamlit.

**Question:** *Is the power to build frontier AI concentrating in fewer organisations?*

The dashboard follows the AI supply chain, one tab per team member. Each tab
lives in its own folder with its own data and code, so everyone can work
without touching anyone else's files.

| Tab | Folder | Sub-question | Owner | Status |
|---|---|---|---|---|
| 1 · Builders | [`dashboards/tab1_builders`](dashboards/tab1_builders) | Who is producing notable and frontier models? | TBC | Done |
| 2 · Compute | [`dashboards/tab2_compute`](dashboards/tab2_compute) | Who owns the chips and the clusters? | TBC | Not started |
| 3 · Capital | [`dashboards/tab3_capital`](dashboards/tab3_capital) | Where is the money going? | TBC | Not started |
| 4 · Capability | [`dashboards/tab4_capability`](dashboards/tab4_capability) | Is the gap between the leaders and everyone else closing? | TBC | Not started |

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py                                  # the full dashboard
streamlit run dashboards/tab2_compute/app.py          # just one tab
```

Run every command from the project root.

## Layout

```
app.py                     base app: title, question, one tab per dashboard
core/                      shared base code, used by every tab
  page.py                  Page contract, error isolation, standalone runner
  theme.py                 chart colours for light and dark mode
dashboards/
  tab1_builders/           one folder per tab, all with the same layout:
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

Inside your folder, import your own modules relatively
(`from . import analysis, loading`) and shared code absolutely
(`from core.theme import colours`).

If your tab raises an error, only your tab shows it; the rest of the
dashboard keeps working. `dashboards/tab1_builders` is a complete example to
copy from.

**Shared files:** `app.py`, `core/` and `requirements.txt` affect everyone.
Agree on changes with the group before editing them. If you need a new
package, add it to `requirements.txt` with an exact version.

## Data licence

Epoch AI data is CC-BY 4.0. Each tab's README holds full citations for its files.
