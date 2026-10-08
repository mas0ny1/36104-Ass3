# Who controls AI Innovation?

36104 Data Visualisation and Narratives, Assignment 3: an interactive data
narrative built with Streamlit.

**Question:** *Are Cutting Edge AI Development being retricted and concentrated into fewer organisations?*

| Tab | Folder | Sub-question | Owner | Status |
|---|---|---|---|---|
| 1 · Builders | [`dashboards/tab1_builders`](dashboards/tab1_builders) | Who is producing notable and frontier models? | Mason | Complete |
| 2 · Compute | [`dashboards/tab2_compute`](dashboards/tab2_compute) | Who owns the chips and the clusters? | Duc Vu | Complete |
| 3 · Capital | [`dashboards/tab3_capital`](dashboards/tab3_capital) | Where is the money going? | To be confirmed | Stub |
| 4 · Capability | [`dashboards/tab4_capability`](dashboards/tab4_capability) | Is the gap between the leaders and everyone else closing? | To be confirmed | Stub |

---

## Persona and Decision Served

- **Target Persona:** Tech Policy & Competition Analyst (e.g. at an antitrust authority, digital market observatory, or public policy think-tank).
- **Decision Served:** Determining whether physical infrastructure and model development in frontier AI have crossed anti-competitive concentration thresholds, informing policy decisions on open-source access, merger scrutiny, and public sovereign compute investments.

---

## User Stories

The dashboard supports three core user stories in the standard `As a..., I want..., so that...` format:

1. **Story 1 (Model Production):**
   *As a competition analyst, I want to* track which organizations produce notable and frontier models over time, *so that I can* evaluate whether cutting-edge model development has transitioned irreversibly from academic institutions into private industry labs.  
   *Walkthrough:* Open **Tab 1 · Builders**, view the sector shift from 2010 to 2025 (academic share falling from ~40% to <10%), and inspect lab shares of large-scale models and training compute.

2. **Story 2 (Geopolitical & Owner Concentration):**
   *As a competition analyst, I want to* measure the distribution of physical supercomputing clusters across sovereign nations and calculate market concentration ratios (CR4, HHI), *so that I can* assess whether access to hardware infrastructure constitutes an anti-competitive bottleneck for independent builders.  
   *Walkthrough:* Open **Tab 2 · Compute**, inspect the headline KPI cards showing CR4 (62.7%), HHI (1,689), and US Compute Share (79.9%), examine the Top 10 Owner Rankings bar chart, and review the Global Compute Share segmented bar chart across the United States, Europe, China, and Rest of World.

3. **Story 3 (Silicon Supply & Physical Grid Bottlenecks):**
   *As a policy researcher, I want to* analyze upstream chip shipments over time and examine cluster power requirements (MW) against compute scale, *so that I can* determine whether hardware vendor monopolies and electrical grid constraints reinforce Big Tech dominance over sovereign alternatives.  
   *Walkthrough:* Open **Tab 2 · Compute**, examine the quarterly *Chip Delivery Time-Series* (2022–2026) showing Nvidia supplying >76% of all AI accelerator compute, and use the *Minimum Cluster Scale* slider with the *Power vs Compute* log-log scatter plot to isolate megaclusters (>100 MW).

---

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py                                  # the full dashboard
```

To run an individual tab in isolation during development:

```bash
streamlit run dashboards/tab1_builders/app.py        # Tab 1 alone
streamlit run dashboards/tab2_compute/app.py         # Tab 2 alone
```

---

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
