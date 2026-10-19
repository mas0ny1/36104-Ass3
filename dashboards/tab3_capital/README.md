# Tab 3 · Capital

**Sub-question:** Where is the money going?
**Owner:** to be confirmed · **Status:** complete

Run this tab on its own from the project root:

```bash
streamlit run dashboards/tab3_capital/app.py
```

## Files

```
__init__.py        PAGE: tab label, question, owner
app.py             runs this tab alone
data/raw/          downloaded files, never edited by hand
src/loading.py     reads and cleans the chip-sales CSV
src/analysis.py    totals, shares and top chips (no drawing, no file reading)
src/views.py       charts and page layout
```

## Questions and charts

All three use Epoch AI's chip-sales data. Money here means the estimated value of the
AI chips shipped: Epoch's *Cost Estimate* (units shipped × approximate cost per chip). The file
does not say whether that is the price a buyer paid or the cost of making the chip. The code
calls this measure `spend`.

| # | Question | Chart | Chart control |
|---|---|---|---|
| 1 | How big is the bill, and who is paid? | Stacked bars: value shipped per year by designer | US$ value or share of total (with % labels) |
| 2 | Is the money moving to newer chips? | Heat map: the top 12 chips by year, oldest chip at the top | none |
| 3 | Which chips take the money? | Bars: the top 15 chips in US\$, coloured by designer, labelled with US\$ and share | designer buttons: Nvidia, Google, Huawei, AMD, Amazon |

Above the questions are four cards (value of chips shipped, value of Nvidia chips, biggest chip, and the
part-year so far) and below them a summary. Every number in the cards, text and summary is calculated
from the data when the page loads; nothing is typed in by hand.

## Filters

One filter row under the question 1 heading sets the **years** (slider) and the **chip
designers** (multiselect) for all three charts. The slider starts on the full range.

- The cards and the summary do not use the filters. They always use all chips, from the
  first year to the latest full year (2022–2025), so they do not change as filters move.
- Picking a single year widens the range by one year, because change over time needs two.
  Selecting no designers, or only designers with no cost estimate, shows a warning and hides
  the charts.
- Text containing dollar amounts goes through `esc()` in `views.py`. Streamlit reads two
  unescaped `$` signs as a maths formula and garbles the text.

## Data sources

Every number on screen traces back to this file. Add a row when you download a new file;
never overwrite a raw file without updating this table.

| File (in `data/raw/`) | Source | Downloaded | Licence | Rows | SHA-256 (first 12) |
|---|---|---|---|---|---|
| `epoch_ai_chip_sales/timelines_by_chip.csv` | Epoch AI, *Data on AI chip sales*, <https://epoch.ai/data/ai-chip-sales> | 13 Oct 2026 | CC-BY 4.0 | 168 chip-quarters | `2bf7b81f91f2` |

Citation: Epoch AI, 'Data on AI chip sales'. Published online at epoch.ai.
Retrieved from <https://epoch.ai/data/ai-chip-sales> [online resource].

The folder also holds other files this tab does **not** read: `chip_types.csv`,
`organizations.csv`, `cumulative_timelines.csv` and `cumulative_timelines_by_designer.csv`
from the same chip-sales download, and the Epoch *Data on AI companies* files in
`epoch_ai_companies/`.

## Processing

Cleaning (`src/loading.py`):

1. Read `timelines_by_chip.csv`: one row per chip type per quarter. The year is taken from
   the quarter's *End date*.
2. **Spend** = *Cost Estimate (USD)*, which equals *Number of Units* × *Chip Cost (USD)* in
   every row. Chips with no cost estimate have spend 0, meaning 'unknown', not 'free'.
3. **Designers:** every chip designer is shown separately: Nvidia, Google, Huawei, AMD and
   Amazon, ordered by total spend. Cambricon has no cost estimate for any chip, so it is
   left out of the charts and filters. Nvidia, Google and AMD use the shared theme colours;
   Huawei and Amazon use two extra colours set in `views.py`.

Calculations (`src/analysis.py`):

4. **Question 1:** spend per year and designer, with each designer's share of the year.
5. **Question 2:** spend per year for the 12 chips with the most spend in the selected years,
   listed from oldest to newest by the average year of their spending (weighted by dollars).
6. **Question 3:** spend per chip added up over the selected years, top 15.

## Known issues

All of these can be checked in the raw files.

- Costs are Epoch's estimates. The file also gives 5th and 95th percentile unit counts, which
  this tab does not use.
- Four chips have no cost estimate (Ascend 950PR, Siyuan 590, TPU v8i and Trainium1). They are
  about 3% of all chips shipped and count as $0, so totals are slightly low.
- Epoch's notes in `chip_types.csv` say the B200 and B300 costs are estimated from the GB200
  and GB300 systems they mostly shipped in, that the Huawei Ascend 910B and 910C costs are
  based on press reports of selling prices and order values (rounded to \$15k and \$20k per chip),
  and that the Trainium2 cost is about $4k per chip according to
  SemiAnalysis.
- The file does not say whether the cost figures are prices buyers paid or the cost of making
  the chips, so the tab calls them an estimated value.
- Several chips are flagged *Incomplete* for the July–September 2026 quarter (and three TPU
  rows for October–December 2022). 2026 covers only
  those three quarters, so its bar is shorter than a full year would be. A note under the
  filters says so whenever 2026 is included.
- The file lists chips shipped by designer. It has no column for who bought them, so it cannot
  say how much a particular company spent.
