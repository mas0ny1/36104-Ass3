# Tab 2 · Compute

**Sub-question:** Who owns the chips and the clusters?  
**Owner:** Duc Vu · **Status:** complete

Run this tab on its own from the project root:

```bash
streamlit run dashboards/tab2_compute/app.py
```

## Files

```
__init__.py        PAGE: tab label, question, owner (Duc Vu)
app.py             runs this tab alone
data/raw/          downloaded files, never edited by hand
  epoch_gpu_clusters/
    gpu_clusters.csv                      Epoch AI supercomputing clusters database (482 clusters)
    README.md                             download metadata and SHA-256 hash
  epoch_chip_sales/
    cumulative_timelines_by_designer.csv  Epoch AI quarterly chip shipments & compute (2022–2026)
    README.md                             download metadata and SHA-256 hash
src/loading.py     reads and cleans datasets, resolves parents, maps 4 geopolitical regions
src/analysis.py    concentration metrics (CR4, CR8, HHI), regional breakdowns, chip sales timeline
src/views.py       full-width layout with 4 charts spanning 4 visual vocabulary families
```

## Data sources

Every number on screen traces back to these authoritative files:

| File (in `data/raw/`) | Source | Downloaded | Licence | Rows | SHA-256 (first 12) |
|---|---|---|---|---|---|
| `epoch_gpu_clusters/gpu_clusters.csv` | Epoch AI, *GPU Clusters / AI Supercomputers*, <https://epoch.ai/data/gpu_clusters.csv> | 8 Oct 2026 | CC-BY 4.0 | 482 clusters | `b38c1b2ed67d` |
| `epoch_chip_sales/cumulative_timelines_by_designer.csv` | Epoch AI, *Data on AI chip sales*, <https://epoch.ai/data/ai-chip-sales> | 8 Oct 2026 | CC-BY 4.0 | 74 quarters | `7ce28f48c0d7` |

### Citations:
- Epoch AI, 'GPU Clusters / AI Supercomputers'. Published online at epoch.ai. Retrieved from <https://epoch.ai/data/gpu_clusters.csv> [online resource].
- Epoch AI, 'Data on AI chip sales'. Published online at epoch.ai. Retrieved from <https://epoch.ai/data/ai-chip-sales> [online resource].

## Processing

### Cleaning (`src/loading.py`):
1. **Date Parsing:** Parse cluster `First Operational Date` (2010–2025) and quarterly chip shipment `End date` (2022–2026).
2. **Numeric Normalisation:** Coerce `H100 equivalents`, `Power Capacity (MW)`, `Total number of AI chips`, and chip timeline compute estimates into floating point numbers.
3. **Parent Entity Resolution:** Map raw owner names into parent corporations (e.g. `Meta AI` → `Meta`, `Microsoft,OpenAI` → `Microsoft / OpenAI`, `EuroHPC JU,Julich` → `EuroHPC`).
4. **4-Region Geopolitical Grouping:** Categorize entities into 4 policy regions:
   - `United States` (xAI, Meta, Microsoft/OpenAI, Google, Amazon, Oracle Cloud, Tesla, CoreWeave, US DoE)
   - `China` (Anonymized Chinese systems, Alibaba, ByteDance, Tencent, Baidu)
   - `Europe` (EuroHPC, ETH Zurich, GENCI, Jülich, Nebius, Sesterce, NexGen Cloud, Northern Data Group)
   - `Rest of world` (Japan/AIST/RIKEN, South Korea, Saudi Aramco, Petrobras)
5. **Silicon Designer Tracking:** Track delivered compute across primary hardware designers (`Nvidia`, `Google`, `AMD`, `Huawei`, `Amazon`).

### Calculations (`src/analysis.py`):
1. **Regional Compute Aggregation:** Aggregate normalized H100 equivalents per region:
   - **United States:** **79.9%** (~1.26M H100 eq)
   - **Europe:** **8.3%** (~131k H100 eq)
   - **China:** **7.0%** (~110k H100 eq)
   - **Rest of world:** **4.9%** (~76k H100 eq)
2. **Antitrust Concentration Ratios:**
   - **CR4 (Four-Firm Ratio):** **62.7%** (xAI, Meta, Microsoft/OpenAI, Oracle Cloud)
   - **CR8 (Eight-Firm Ratio):** **82.1%**
   - **Herfindahl-Hirschman Index (HHI):** **1,689** (classified as a concentrated market under DOJ/FTC guidelines)
3. **Hardware Designer Time-Series:** Quarterly cumulative delivered compute (2022–2026), revealing Nvidia's **~76% market dominance** (delivering >22M H100 equivalents).
4. **Physical Power Scaling:** Correlation between power demand (MW) and cluster compute scale (H100 eq).

## Visual Vocabulary Families (Full-Width Sequential Layout)

Tab 2 features a clean, non-overlapping sequential layout where each chart occupies full container width:
1. **Magnitude / Ranking (Horizontal Bar):** Top 10 Cluster Owners by total H100 equivalents, colored by Country, with direct values readable on bars without hover.
2. **Part-to-Whole (Segmented Share Bar):** Global Compute Share across United States (79.9%), Europe (8.3%), China (7.0%), and Rest of World (4.9%).
3. **Change Over Time (Multi-Line Time Series):** Quarterly cumulative compute delivered by chip designer (2022–2026), demonstrating Nvidia's accelerating lead.
4. **Correlation & Distribution (Log-Log Scatter):** Cluster power demand (MW) vs compute scale, highlighting landmark installations (>100 MW).

## Known issues & data boundaries

- **Export Controls & Anonymized Systems:** Trade sanctions cause Chinese labs to conceal cluster specs; Epoch tracks 190 clusters in China anonymously.
- **Undisclosed Proprietary Clusters:** Private internal clusters that tech giants do not announce publicly (e.g. secret internal TPU pods or Apple private clusters) are absent.
- **Theoretical Peak vs Realized MFU:** H100 equivalents measure theoretical peak 16-bit FLOP/s; real-world training efficiency (MFU) averages 30–50% due to distributed networking overhead.
- **Defense Facilities:** Classified military and intelligence supercomputers are omitted.
