# Tab 1 · Builders

**Sub-question:** Who is producing notable and frontier AI models?
**Owner:** to be confirmed · **Status:** complete

Run this tab on its own from the project root:

```bash
streamlit run dashboards/tab1_builders/app.py
```

## Files

```
__init__.py        PAGE: tab label, question, owner
app.py             runs this tab alone
data/raw/          downloaded files, never edited by hand
src/loading.py     reads and cleans the raw CSVs
src/analysis.py    lab rankings, cost trend
src/views.py       charts and page layout
```

## Data sources

Every number on screen traces back to one of these files. Add a row when you
download a new file; never overwrite a raw file without updating this table.

| File (in `data/raw/`) | Source | Downloaded | Licence | Rows | SHA-256 (first 12) |
|---|---|---|---|---|---|
| `epoch_ai_models/notable_ai_models.csv` | Epoch AI, *Data on AI models*, <https://epoch.ai/data/ai_models.zip> | 7 Oct 2026 | CC-BY 4.0 | 1,078 models | `3ac5c86f57c4` |
| `epoch_ai_models/large_scale_ai_models.csv` | same bundle | 7 Oct 2026 | CC-BY 4.0 | 532 models | `05d24f61f8c5` |
| `epoch_ai_models/frontier_ai_models.csv` | same bundle | 7 Oct 2026 | CC-BY 4.0 | 138 models | `46c62a18eeed` |

Citation: Epoch AI, 'Data on AI models'. Published online at epoch.ai.
Retrieved from <https://epoch.ai/data/ai-models> [online resource].

The bundle also contains `all_ai_models.csv` (3,626 models), which this tab
does not use, so it is not included.

## Processing

Cleaning (`src/loading.py`):

1. Parse *Publication date*, drop rows without one, and take the year.
2. Split *Organization*, *Organization categorization* and *Country (of
   organization)* on commas. They are aligned lists, one entry per organisation.
3. Merge sub-labs into parent companies with `PARENT_ORG` (e.g. Google Brain,
   DeepMind and Google Research → Google; FAIR and Meta AI → Meta).
4. Label each model's sector: all Industry → Industry; all Academia →
   Academia; both → Industry–academia collaboration; anything else → Other.

Calculations (`src/analysis.py`):

5. **Lab credit:** a model with *n* parent organisations gives each 1/*n*,
   or 1/*n* of its training FLOP when weighting by compute.
6. **Lab ranking:** each lab's share of total credit over 2023–2025, by
   number of models or by training compute.
7. **Cost trend:** least-squares fit of log₁₀(*Training compute cost (2023
   USD)*) on release date for frontier models.

## Known issues

- About 40% of large-scale models have no *Training compute (FLOP)* value.
  Compute-weighted rankings only use the rows that have one.
- A few organisation names have mis-encoded characters in Epoch's source file
  (e.g. `Universit� de Montr�al`). They are left as they are.
- 2026 is incomplete because Epoch catalogues releases with a lag, so it is
  hidden by default.
