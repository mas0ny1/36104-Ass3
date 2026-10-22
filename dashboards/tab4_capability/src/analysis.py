"""Calculations behind the Capability tab.

Input: the cleaned tables from loading.py. Output: small summary tables that
views.py turns into charts. Nothing here draws or reads files.
"""

import numpy as np
import pandas as pd

MONTH = 30.44   # average days in a month


# --------------------------------------------------------------------------
# Snapshots
# --------------------------------------------------------------------------

def snapshots(eci, n=7):
    """Up to `n` dates exactly 6 months apart, counting back from the latest model.

    Dates whose trailing 12-month window starts before the first model in the
    data are dropped, so every bar covers a full year. Returns a list of
    (timestamp, label), oldest first. The last snapshot is the end of the data
    and carries its real date in the label.
    """
    end = eci["date"].max().normalize()
    first = eci["date"].min()
    dates = [end - pd.DateOffset(months=6 * k) for k in range(n - 1, -1, -1)]
    dates = [d for d in dates if d - pd.DateOffset(years=1) >= first]
    snaps = [(d, d.strftime("%b %Y")) for d in dates[:-1]]
    snaps.append((end, f"{end.day} {end:%b %Y}"))
    return snaps


# --------------------------------------------------------------------------
# 1. The top tier: which labs hold it?
# --------------------------------------------------------------------------

def top_tier(eci, snaps, n):
    """Labs behind the `n` highest-scoring models released in the 12 months to each snapshot."""
    named = eci.dropna(subset=["lab"])
    rows = []
    for snap, label in snaps:
        window = named[(named["date"] > snap - pd.DateOffset(years=1))
                       & (named["date"] <= snap)]
        top = window.nlargest(n, "eci")
        for lab, k in top["lab"].value_counts().items():
            rows.append({"snapshot": snap, "label": label, "lab": lab,
                         "models": k, "total": len(top), "pool": len(window)})
    return pd.DataFrame(rows)


def field_series(eci, labs=None, n=12, step=3):
    """The best, middle and lower models of each 12-month window, every `step` months.

    Each row is the year of releases up to a date (counting back from the latest
    model), with the best score, the median and the 25th and 75th percentiles.
    Windows that start before the first model in the data are dropped. `labs`
    restricts the pool to those labs, as a check that the story does not rest on
    which models happened to be scored.
    """
    end = eci["date"].max().normalize()
    first = eci["date"].min()
    pool = eci if labs is None else eci[eci["lab"].isin(labs)]
    dates = [end - pd.DateOffset(months=step * k) for k in range(n - 1, -1, -1)]
    rows = []
    for d in (d for d in dates if d - pd.DateOffset(years=1) >= first):
        w = pool.loc[(pool["date"] > d - pd.DateOffset(years=1)) & (pool["date"] <= d), "eci"]
        rows.append({"date": d, "models": len(w), "best": w.max(), "p75": w.quantile(0.75),
                     "median": w.median(), "p25": w.quantile(0.25)})
    return pd.DataFrame(rows)


def steady_labs(eci, min_models=10):
    """Labs with at least `min_models` models in the file: a steadier cast to check against."""
    counts = eci["lab"].value_counts()
    return counts[counts >= min_models].index.tolist()


def field_mix(eci, field):
    """Open-weights and Chinese-lab share of the models in the first and last windows."""
    out = {}
    for key, row in (("first", field.iloc[0]), ("last", field.iloc[-1])):
        w = eci[(eci["date"] > row["date"] - pd.DateOffset(years=1)) & (eci["date"] <= row["date"])]
        out[key] = {"open": (w["access"] == "Open weights").mean(),
                    "china": (w["country"] == "China").mean()}
    return out


def top_models(eci, snap, n):
    """The `n` highest-scoring models behind one snapshot's bar, best first.

    Same selection as `top_tier`: models with a lab, released in the 12 months to
    `snap`. Returns the rows a reader can find in eci_scores.csv.
    """
    named = eci.dropna(subset=["lab"])
    window = named[(named["date"] > snap - pd.DateOffset(years=1))
                   & (named["date"] <= snap)]
    top = window.nlargest(n, "eci")[["model", "organization", "lab", "date", "eci"]].copy()
    top.insert(0, "rank", range(1, len(top) + 1))
    return top


def hhi_working(top):
    """The sum behind the HHI: each lab's models, share in percent, and share squared."""
    counts = top["lab"].value_counts()
    work = pd.DataFrame({"lab": counts.index, "models": counts.to_numpy()})
    work["share_pct"] = work["models"] / work["models"].sum() * 100
    work["squared"] = work["share_pct"] ** 2
    return work


def hhi(tier):
    """Herfindahl-Hirschman Index of each snapshot's top tier (0 to 10,000)."""
    share = tier["models"] / tier["total"] * 100
    return (share ** 2).groupby(tier["label"], sort=False).sum()


def top_labs(tier, k=3):
    """The `k` labs with the most top-tier models at the latest snapshot."""
    last = tier[tier["snapshot"] == tier["snapshot"].max()]
    return last.nlargest(k, "models")["lab"].tolist()


def top_k_share(df, count_col, k=3):
    """Share held by the `k` biggest labs at each snapshot, and who they were.

    Judging each date by its own biggest labs (a concentration ratio, like the CR4
    in Tab 2) avoids picking today's leaders and then looking back at them, which
    would exaggerate how much their share has grown.
    """
    rows = []
    for label, g in df.groupby("label", sort=False):
        g = g.sort_values([count_col, "lab"], ascending=[False, True])
        rows.append({"label": label, "share": g[count_col].head(k).sum() / g["total"].iloc[0],
                     "labs": g["lab"].head(k).tolist()})
    return pd.DataFrame(rows).set_index("label")


def group_labs(df, leaders, count_col):
    """Fold every lab outside `leaders` into 'Other labs' and re-sum the counts."""
    out = df.copy()
    out["lab"] = out["lab"].where(out["lab"].isin(leaders), "Other labs")
    keys = [c for c in out.columns if c not in ("lab", count_col)]
    return out.groupby(keys + ["lab"], as_index=False, sort=False)[count_col].sum()


# --------------------------------------------------------------------------
# 2. Who holds the best score on each benchmark?
# --------------------------------------------------------------------------

def benchmark_leaders(scores, snaps, min_models=5):
    """For each snapshot, which lab holds the best score on each benchmark.

    Only benchmarks with at least `min_models` scored models by that date are
    counted. A tie goes to the model released first.
    """
    named = scores.dropna(subset=["lab"])
    rows = []
    for snap, label in snaps:
        s = named[named["date"] <= snap]
        size = s.groupby("benchmark").size()
        s = s[s["benchmark"].isin(size[size >= min_models].index)]
        best = (s.sort_values(["performance", "date"], ascending=[False, True])
                .drop_duplicates("benchmark"))
        for lab, k in best["lab"].value_counts().items():
            rows.append({"snapshot": snap, "label": label, "lab": lab,
                         "benchmarks": k, "total": len(best)})
    return pd.DataFrame(rows)


def eval_coverage(scores, eci, n=10):
    """Benchmarks scored per model: the top `n` models by ECI vs every model.

    Labs whose models are tested on more benchmarks have more chances to hold a
    best score, so this is the main bias in the leader counts.
    """
    per_model = scores.groupby("model").size()
    top = eci.nlargest(n, "eci")["model"]
    return per_model.reindex(top).median(), per_model.median()


# --------------------------------------------------------------------------
# 4. Open versus closed
# --------------------------------------------------------------------------

def records(eci, access):
    """Models that set a new best ECI score among `access` models, in date order."""
    d = eci[eci["access"] == access]
    # Only the best model of each release date counts, so two models released on the
    # same day cannot change the answer depending on which one is listed first.
    d = d.sort_values(["date", "eci"], ascending=[True, False]).drop_duplicates("date")
    prev_best = d["eci"].cummax().shift(fill_value=-np.inf)
    return d[d["eci"] > prev_best][["date", "eci", "model"]]


def frontier_steps(eci):
    """Running best score for open and closed models, extended to the last date."""
    end = eci["date"].max()
    parts = []
    for access in ("Closed weights", "Open weights"):
        rec = records(eci, access).copy()
        rec["access"] = access
        tail = rec.iloc[[-1]].copy()
        tail["date"] = end
        parts += [rec, tail]
    return pd.concat(parts, ignore_index=True)


def gap_series(eci):
    """Best closed score minus best open score so far, stepping at each new record.

    Starts on the first date both groups have a model, and ends on the last date
    in the data so the final value is drawn to the edge.
    """
    closed = records(eci, "Closed weights")
    open_ = records(eci, "Open weights")
    start = max(closed["date"].min(), open_["date"].min())
    dates = sorted({*closed["date"], *open_["date"], eci["date"].max()})
    rows = []
    for d in (d for d in dates if d >= start):
        gap = (closed.loc[closed["date"] <= d, "eci"].max()
               - open_.loc[open_["date"] <= d, "eci"].max())
        rows.append({"date": d, "gap": gap})
    return pd.DataFrame(rows)


def gap_noise(eci):
    """Smallest gap, in ECI points, that can be told apart from zero.

    Each score has a 90% interval. For the difference of two independent scores
    the interval is sqrt(2) times the typical half-width.
    """
    half = ((eci["ci_high"] - eci["ci_low"]) / 2).median()
    return float(np.sqrt(2) * half)


def gap_averages(gap, end):
    """Time-weighted average gap over the last 12 months and the 12 months before."""
    daily = (gap.set_index("date")["gap"].resample("D").ffill())
    recent = daily[daily.index > end - pd.DateOffset(years=1)].mean()
    before = daily[(daily.index > end - pd.DateOffset(years=2))
                   & (daily.index <= end - pd.DateOffset(years=1))].mean()
    return recent, before


def first_reach(eci, access, level):
    """First model of this `access` type to score at least `level`, or None."""
    hit = eci[(eci["access"] == access) & (eci["eci"] >= level)]
    if hit.empty:
        return None
    row = hit.sort_values("date").iloc[0]
    return row["date"], row["model"]


def lag_at(eci, level):
    """Months between the first closed and first open model to reach `level`."""
    c = first_reach(eci, "Closed weights", level)
    o = first_reach(eci, "Open weights", level)
    end = eci["date"].max()
    if c is None:
        return c, o, None, False
    if o is None:
        return c, o, (end - c[0]).days / MONTH, False
    return c, o, max(0.0, (o[0] - c[0]).days / MONTH), True


def lag_table(eci):
    """For every closed-weights record, how long open weights took to match it.

    A record no open model has matched yet is marked unmatched, and its lag is
    the months waited so far (a minimum, since the wait is still going).
    """
    end = eci["date"].max()
    rows = []
    for _, r in records(eci, "Closed weights").iterrows():
        o = eci[(eci["access"] == "Open weights") & (eci["eci"] >= r["eci"])]
        if o.empty:
            rows.append({"date": r["date"], "model": r["model"], "eci": r["eci"],
                         "matched": False, "lag": (end - r["date"]).days / MONTH,
                         "matched_by": None})
        else:
            m = o.sort_values("date").iloc[0]
            rows.append({"date": r["date"], "model": r["model"], "eci": r["eci"],
                         "matched": True,
                         "lag": max(0.0, (m["date"] - r["date"]).days / MONTH),
                         "matched_by": m["model"]})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Waiting times that are still running (Kaplan-Meier)
# --------------------------------------------------------------------------

def km_curve(months, observed):
    """Kaplan-Meier estimate of the share still waiting, by months elapsed.

    `observed` is True when the wait ended (an open model matched the record) and
    False when it is still running, so the true wait is longer than `months`. Ignoring the running waits would make the typical
    wait look shorter than it is. The curve stops at the longest time followed.
    """
    d = pd.DataFrame({"t": np.asarray(months, float),
                      "e": np.asarray(observed, bool)}).sort_values("t")
    times = np.sort(d.loc[d["e"], "t"].unique())
    surv, rows = 1.0, []
    if len(times) == 0 or times[0] > 0:
        rows.append((0.0, 1.0))
    for t in times:
        at_risk = (d["t"] >= t).sum()
        ended = ((d["t"] == t) & d["e"]).sum()
        surv *= 1 - ended / at_risk
        rows.append((t, surv))
    rows.append((d["t"].max(), surv))
    return pd.DataFrame(rows, columns=["months", "waiting"])


def km_median(months, observed):
    """Months by which half the waits have ended, or NaN if fewer than half have."""
    c = km_curve(months, observed)
    hit = c[c["waiting"] <= 0.5]
    return hit["months"].iloc[0] if len(hit) else np.nan


# --------------------------------------------------------------------------
# 5. Compute versus capability
# --------------------------------------------------------------------------

ERAS = ["2023–24", "2025", "2026"]


def _era(dates):
    """Release-period label: 2023–24, 2025 or 2026."""
    return pd.cut(dates.dt.year, [2000, 2024, 2025, 2100], labels=ERAS).astype(str)


def compute_table(comp):
    """Models with a compute figure, plus log10 FLOP and a release-era label."""
    d = comp.dropna(subset=["flop"]).copy()
    d["log_flop"] = np.log10(d["flop"])
    d["era"] = _era(d["date"])
    return d


def era_counts(comp):
    """Per release period: how many models there are, and how many have a compute figure."""
    every = _era(comp["date"]).value_counts()
    with_figure = _era(comp.loc[comp["flop"].notna(), "date"]).value_counts()
    return (pd.DataFrame({"models": every, "with_figure": with_figure})
            .reindex(ERAS).fillna(0).astype(int))


def compute_fit(comp):
    """Least-squares fit of ECI on log10 compute and release date.

    per_10x: ECI points gained by training with 10x the compute, same year.
    per_year: ECI points gained per year at the same compute.
    """
    d = compute_table(comp)
    years = (d["date"] - pd.Timestamp("2023-01-01")).dt.days / 365.25
    X = np.column_stack([np.ones(len(d)), d["log_flop"], years])
    a, per_10x, per_year = np.linalg.lstsq(X, d["eci"].to_numpy(), rcond=None)[0]
    top30 = comp.nlargest(30, "eci")
    return {"n": len(d), "total": len(comp), "a": a, "per_10x": per_10x,
            "per_year": per_year,
            "top30_missing": int(top30["flop"].isna().sum())}


def compute_missing(comp):
    """Models with no published compute figure, given a spot in a strip on the chart.

    `x` is a seeded random jitter inside the strip so the dots do not overlap. It
    carries no information; only the score (`eci`) does.
    """
    d = comp[comp["flop"].isna()].copy()
    d["era"] = _era(d["date"])
    d["x"] = 27.6 + np.random.default_rng(0).uniform(-0.35, 0.35, len(d))
    return d[["model", "lab", "date", "eci", "era", "x"]]


def compute_lines(comp, fit):
    """The fitted model drawn once per release era, at that era's average date.

    Same slope for every era, shifted up by the per-year gain, so the chart
    shows exactly the model the text quotes.
    """
    d = compute_table(comp)
    years = (d["date"] - pd.Timestamp("2023-01-01")).dt.days / 365.25
    rows = []
    for era, g in d.groupby("era"):
        yr = years[g.index].mean()
        for x in (g["log_flop"].min(), g["log_flop"].max()):
            rows.append({"era": era, "log_flop": x,
                         "eci": fit["a"] + fit["per_10x"] * x + fit["per_year"] * yr})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5-6. Cheapest route to a score, and how well benchmarks separate models
# --------------------------------------------------------------------------

def cheapest_to_reach(comp, level):
    """Models that reached `level`, as a running minimum of published training compute.

    Only models with a compute figure can appear. The leading closed models publish
    none, so the true cheapest route may be lower still. Each row is a model that
    set a new low for compute among models scoring at least `level`.
    """
    d = comp.dropna(subset=["flop"])
    d = d[d["eci"] >= level].sort_values("date")
    low = d["flop"].cummin()
    steps = d[d["flop"] == low].drop_duplicates("flop")
    return steps[["date", "model", "flop", "eci"]].reset_index(drop=True)


BENCH_PERIODS = ["2024 or earlier", "2025", "2026"]


def benchmark_spread(scores, end, min_models=12):
    """For each benchmark, the best and median score of models released in the last year.

    Scores are rescaled so 0 = random guessing and 1 = the benchmark's ceiling. A
    benchmark where the best and the median model sit close together, near the
    ceiling, no longer shows who is ahead. Benchmarks with fewer than `min_models`
    recent models are left out, since a median of a handful is noise.
    """
    recent = scores[scores["date"] > end - pd.DateOffset(years=1)]
    g = recent.groupby("benchmark").agg(models=("norm", "size"), best=("norm", "max"),
                                        median=("norm", "median"), release=("release", "first"))
    g = g[g["models"] >= min_models].copy()
    g["spread"] = g["best"] - g["median"]
    g["period"] = pd.cut(g["release"].dt.year, [2000, 2024, 2025, 2100],
                         labels=BENCH_PERIODS).astype(str)
    return g.sort_values("spread", ascending=False).reset_index()
