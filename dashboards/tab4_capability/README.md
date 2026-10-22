# Tab 4 · Capability

**Sub-question:** Is the gap between the leaders and everyone else closing?
**Owner:** Gemy Putradimi · **Status:** complete (draft, awaiting group review)

Run this tab on its own from the project root:

```bash
streamlit run dashboards/tab4_capability/app.py
```

## Files

```
__init__.py        PAGE: tab label, question, owner
app.py             runs this tab alone
data/raw/          downloaded files, never edited by hand
src/loading.py     reads and cleans the raw CSVs
src/analysis.py    concentration, lag, compute fit, saturation
src/views.py       charts and page layout
```

## What the tab shows

| # | Chart | Question it answers |
|---|---|---|
| Cards | Share of the top-N models held by the 3 biggest labs; typical open-weights lag; share of best benchmark scores held by the 3 biggest labs | Headline numbers |
| 1 | Share of the top-N models by lab, every 6 months (slider: N) | Who holds the top tier? |
| 2 | Share of benchmarks whose best score each lab holds | Does one lab lead every task? |
| 3 | The best model, the median and the middle half of models in each 12-month window | Is the field keeping pace with the leader? |
| 4 | Closed vs open running best (slider: score level), the gap in score between them, and the lag per closed record | How far behind is open-weight AI? |
| 5 | Lowest published compute that reached a chosen score, over time (slider: score), and ECI against training compute | Does compute still decide capability? |
| 6 | Best and median score of recent models on each benchmark (dumbbell, one row per benchmark) | Can benchmarks still separate leaders from the pack? |

Charts 1 and 2 print the counts behind the shares: the number of models (or
benchmarks) each lab holds inside its segment. The size of the pool behind
chart 1 (every named-lab model released in the 12 months to a date) is stated once
in the text above it, not repeated under each bar. A 100% bar alone would hide
both. The same rule applies
elsewhere: the chart 4 legend gives the number of closed and open models, the
lag chart's legend the matched and unmatched records, the compute scatter's legend how many
models in each release period have a compute figure (only 12 of 83 for 2026),
and card 3 says how many benchmarks its percentage is out of (54 of 61).

Under chart 1, a **"Check it"** expander lists the 10 models behind the latest
concentration index (HHI), each one a row of `eci_scores.csv`, and the
lab-by-lab sum that gives the figure. Use it to trace the number to the source.

Colour rule: each colour means one thing on the page. The three theme colours
are the three leading labs (charts 1 and 2); closed and open weights use the
purple and gold from Tab 3's extra palette (chart 4 and chart 5's step line); release
periods and benchmark periods use one blue ramp (chart 5's scatter and chart 6). Every chart has alt text.

## Data sources

Every number on screen traces back to one of these files. Add a row when you
download a new file; never overwrite a raw file without updating this table.

| File (in `data/raw/`) | Source | Downloaded | Licence | Rows | SHA-256 (first 12) |
|---|---|---|---|---|---|
| `epoch_capabilities/eci_scores.csv` | Epoch AI, *Capabilities & benchmarking*, <https://epoch.ai/benchmarks> (`benchmark_data.zip`, folder `epoch_capabilities_index/`) | 18 Oct 2026 | CC-BY 4.0 | 277 models | `2f47e90bef5a` |
| `epoch_capabilities/processed_data_for_eci.csv` | same bundle, folder `epoch_capabilities_index/` | 18 Oct 2026 | CC-BY 4.0 | 2,987 scores | `6a7172d69a88` |
| `epoch_capabilities/benchmark_metadata.csv` | same bundle | 18 Oct 2026 | CC-BY 4.0 | 91 benchmarks | `f227d481009d` |
| `epoch_capabilities/model_metadata.csv` | same bundle | 18 Oct 2026 | CC-BY 4.0 | 1,169 rows | `353af5b9c29d` |

Citation: Epoch AI, 'Capabilities & benchmarking'. Published online at
epoch.ai. Retrieved from <https://epoch.ai/benchmarks> [online resource].

The bundle also holds about 85 per-benchmark files, `edi_scores.csv` and
`eci_bootstraps.json`. This tab does not use them, so they are not included.
The latest model in the data is dated 7 Oct 2026.

## Processing

Cleaning (`src/loading.py`):

1. Parse dates. **Lab** = the first organisation listed for a model, with
   sub-labs merged into the parent (Google DeepMind and Google → Google; Meta AI
   → Meta; Microsoft Research → Microsoft). Models with no organisation have no
   lab and are left out of lab-level charts.
2. **Weights type** = Epoch's *Accessibility group* (Open weights / Closed
   weights). Anything else is labelled Other and left out of open-versus-closed.
3. Join each (model, benchmark) score to the model's lab and date, and to the
   benchmark's release date, random baseline and ceiling.
4. Rescale each score to (score − baseline) ÷ (ceiling − baseline). Not capped.
5. Attach training compute to a model by matching names (punctuation and case
   removed) against *model_version*, *model_group* and *display_name*.

Calculations (`src/analysis.py`):

6. **Top tier:** the N highest-ECI models released in the 12 months to each
   date. Dates are exactly 6 months apart, counting back from the last model
   (7 Oct 2026), and start at the first date with a full 12 months of data.
   **HHI** = sum of squared lab shares in percent.
7. **Benchmark leader:** for each benchmark with at least 5 scored models by that
   date, the lab of the highest score. Ties go to the earlier model.
   **Concentration over time** (the cards and the Summary) is the share held by the
   three biggest labs *at each date*, like the CR4 in Tab 2. An earlier draft fixed
   today's three labs and looked back at them, which overstated the rise (it showed
   +30 and +14 points; judged fairly the change is 0 and +5). The bar colours still
   follow today's three labs, and everyone else is grouped as Other labs.
7b. **Leader against the field:** for each 12-month window (every 3 months, from the
   first full year), over every model with a score, any lab: the best score, the
   median and the 25th and 75th percentiles. Lead = best minus median. Checked
   against the 75th percentile and against only the labs with 10 or more models
   in the file. The median is not a random sample: the mix of open-weights and
   Chinese-lab models in the window changes (open weights 53% to 33%, Chinese
   labs 19% to 39%), so the early narrowing of the lead over the median is
   partly mix.
8. **Frontier lines and lag:** running best ECI for open and closed models (only the best
   model of each release date counts, so same-day releases cannot change the answer). For
   each closed record, lag = months until the first open model scored at least as
   high. A record no open model has matched is kept with the wait so far (a
   minimum). The **typical lag** (7.0 months) is a Kaplan-Meier median, which
   counts those still-running waits; the median of matched records alone is 6.7.
   The **gap in score** is the best closed ECI minus the best open ECI so far,
   stepping at each new record, from the first date both groups have a model. It
   is shown against a "noise" band: sqrt(2) times the median half-width of a
   model's 90% interval (about 5 points), the smallest gap that can be told from
   zero. The text compares its average over the last 12 months with the 12
   months before (time-weighted).
9. **Compute:** two views. *Cheapest route*: among models with ECI at or above a
   chosen score and a published compute figure, the running minimum of compute by
   release date (a model appears when it sets a new low). *Scatter*: least squares
   of ECI on log10(FLOP) and release year; the lines draw that model at each
   release period's average date (same slope, shifted up).
10. **Benchmark spread:** for each benchmark, take the models released in the last
    12 months, rescale their scores (0 = guessing, 1 = ceiling) and report the best
    and the median. Spread = best minus median. Benchmarks with fewer than 12 such
    models are left out. Benchmarks are grouped by their own release year (2024 or
    earlier, 2025, 2026). A small spread near the ceiling means the benchmark no
    longer shows who is ahead.

## Known issues

- 17 models have no organisation (PaLM 2, Yi, Qwen2.5-Coder and others). They
  cannot be recovered from `model_metadata.csv` by name.
- 24 models are Epoch's *Other* access group (unknown or limited), including
  Gemini 4 Argon. They are in neither open nor closed.
- Closed-weights records: 23, of which 16 have been matched by an open model and 7 have not.
  An earlier draft counted 26 and 19 because it counted same-day releases as separate records;
  an independent recalculation from the raw CSV caught it.
- The top-tier HHI is noisy. With 10 models per bar, one release moves it a lot:
  it reads 3,800 / 2,600 / 2,800 / 4,000 / 3,400 / 4,200 across the six bars,
  and an earlier choice of dates gave a smoother rise to 5,400. Read the trend, not
  any single bar.
- Only 111 of 277 models have a compute figure, and 28 of the top 30 by ECI do not.
  The scatter draws the models without one in a shaded strip so they stay visible,
  and the cheapest-route chart can only use models that publish a figure.
- Top models are scored on a median of 18.5 benchmarks against 9 for a typical
  model, so benchmark-leader counts favour labs that get tested more.
- 29 of the 91 benchmarks in `benchmark_metadata.csv` have no file in the
  download. Only the 61 benchmarks in the ECI processed data are used.
- A few benchmarks have a ceiling below a perfect score, so some rescaled
  scores exceed 1. 289 scores sit more than 0.05 below the random-guess baseline
  (e.g. on Winogrande, DTBench); they do not affect the running-best calculations.
- Only 31 of the 61 benchmarks have 12 or more models released in the last year, so
  the spread chart covers those. Old benchmarks nobody scores any more (e.g. MMLU,
  2020) are therefore not in it.
- Release dates differ between `eci_scores.csv` and `processed_data_for_eci.csv`
  for 54 score rows (12 models), by a median of 6 days and up to 243. The tab
  uses the `eci_scores.csv` date.
- An earlier draft showed how fast benchmarks were beaten (Kaplan-Meier curves). It was
  replaced: it answered a different question from the section's title, rested on
  groups of 7 and 14 benchmarks, and needed long caveats.
- Two models have no confidence interval in `eci_scores.csv`.
- The ECI is Epoch's own composite. It changes whenever Epoch re-estimates it.
