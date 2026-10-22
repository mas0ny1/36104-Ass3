"""Charts and page layout for the Capability tab.

Data: Epoch AI, 'Capabilities & benchmarking' (CC-BY). Cleaning is in
loading.py, calculations in analysis.py; the download record is in this
folder's README.
"""

import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from core.theme import colours

from . import analysis, loading

MIN_BENCHMARKS = 20          # earlier snapshots have too few benchmarks to compare
ERAS = analysis.ERAS


@st.cache_data
def load():
    eci = loading.load_eci()
    bench = loading.load_benchmarks()
    return {
        "eci": eci,
        "scores": loading.load_scores(eci, bench),
        "comp": loading.load_compute(eci),
        "snaps": analysis.snapshots(eci),
    }


def _legend():
    return alt.Legend(orient="top", direction="horizontal", labelLimit=0)


def _date_axis():
    """A tick every 6 months, labelled with the year so 'April' is never ambiguous."""
    return alt.Axis(format="%b %Y", labelAngle=0,
                    tickCount={"interval": "month", "step": 6})


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def _access_colours(c):
    """Two colours for closed and open weights, used only for that pair.

    The labs in charts 1 and 2 already use the three theme colours, so closed and
    open weights take the purple and gold that Tab 3 adds for the same reason.
    That way no colour means two things on this page.
    """
    if c["surface"] == "#ffffff":
        return ["#7b4fd0", "#b8860b"]
    return ["#a67cf0", "#e3b83a"]


def _era_ramp(c):
    """One blue hue from light to dark for release periods, which are ordered.

    Closed and open weights have their own two colours in chart 4, so periods
    get a ramp instead of category colours.
    """
    if c["surface"] == "#ffffff":
        return ["#9dc3f1", "#4a91e0", "#1b56a5"]
    return ["#5b86c4", "#7db0f0", "#c4dcfa"]


def _ink(c):
    """Colour for chart annotations: darker than the gridline grey so small labels stay legible."""
    return "#55534e" if c["surface"] == "#ffffff" else "#c9c7c0"


def share_bars(df, count_col, leaders, c, y_title, count_title, notes, x_title=None):
    """Stacked 100% bars: the leading labs plus everyone else, one bar per snapshot.

    The count for each lab is printed inside its segment, and `notes` maps each
    snapshot label to the text printed above its bar. Showing the counts matters: a
    100% bar on its own hides how many models or benchmarks it is made of.
    """
    labs = leaders + ["Other labs"]
    d = df.copy()
    d["share"] = d[count_col] / d["total"]
    d["order"] = d["lab"].map(labs.index)
    labels = d.sort_values("snapshot")["label"].drop_duplicates().tolist()

    # Middle of each segment, stacking in `labs` order from the bottom of the bar.
    d = d.sort_values(["snapshot", "order"])
    d["mid"] = d.groupby("label")["share"].cumsum() - d["share"] / 2

    x = alt.X("label:O", sort=labels, title=x_title, axis=alt.Axis(labelAngle=0))
    bars = alt.Chart(d).mark_bar(stroke=c["surface"], strokeWidth=1.5).encode(
        x=x,
        y=alt.Y(f"{count_col}:Q", stack="normalize", title=y_title,
                axis=alt.Axis(format="%", tickCount=5)),
        color=alt.Color("lab:N", title=None,
                        scale=alt.Scale(domain=labs,
                                        range=c["series"][:len(leaders)] + [c["other"]]),
                        legend=_legend()),
        order=alt.Order("order:Q", sort="ascending"),
        tooltip=[alt.Tooltip("label:O", title="As of"),
                 alt.Tooltip("lab:N", title="Lab"),
                 alt.Tooltip(f"{count_col}:Q", title=count_title),
                 alt.Tooltip("share:Q", title="Share", format=".0%")],
    )
    # Each count needs contrast against its own fill: white on the blue, dark on the
    # lighter orange, green and grey (in dark mode every fill takes white). Two plain
    # layers rather than a colour encoding, which would share the bars' colour scale.
    light = c["surface"] == "#ffffff"
    visible = d[d["share"] >= 0.045]     # a count in a segment too thin to hold it is clutter
    on_blue = visible["lab"] == labs[0]

    def count_layer(rows, colour):
        return alt.Chart(rows).mark_text(fontSize=11, fontWeight="bold", color=colour).encode(
            x=x, y=alt.Y("mid:Q", title=y_title),
            text=alt.Text(f"{count_col}:Q", format="d"))

    counts = [count_layer(visible[on_blue], "white"),
              count_layer(visible[~on_blue], "#1b1b1b" if light else "white")]

    top = pd.DataFrame({"label": labels, "one": 1.0,
                        "text": [notes[lab] for lab in labels]})
    layers = [bars, *counts,
              alt.Chart(top).mark_text(dy=-9, fontSize=11, color=_ink(c)).encode(
                  x=x, y=alt.Y("one:Q", title=y_title), text="text:N")]
    return alt.layer(*layers).properties(
        height=320, padding={"left": 5, "right": 5, "top": 20, "bottom": 5})


def field_chart(f, c):
    """The best model against the typical one: best line, median line, middle-half band."""
    strong = "#1b1b1b" if c["surface"] == "#ffffff" else "#f2f2f2"
    start, end = f["date"].min(), f["date"].max()
    xs = alt.Scale(domain=[start, end])
    ys = alt.Scale(domain=[float(np.floor(f["p25"].min() / 10) * 10),
                           float(np.ceil((f["best"].max() + 6) / 5) * 5)])
    title = ["ECI score of models released", "in the 12 months before the date"]
    x = alt.X("date:T", title="Snapshot date", axis=_date_axis(), scale=xs)

    def y(field):
        return alt.Y(f"{field}:Q", title=title, scale=ys, axis=alt.Axis(minExtent=45))

    tip = [alt.Tooltip("date:T", title="Snapshot", format="%d %b %Y"),
           alt.Tooltip("models:Q", title="Models in the year"),
           alt.Tooltip("best:Q", title="Best", format=".1f"),
           alt.Tooltip("p75:Q", title="75th percentile", format=".1f"),
           alt.Tooltip("median:Q", title="Median", format=".1f"),
           alt.Tooltip("p25:Q", title="25th percentile", format=".1f")]
    base = alt.Chart(f)
    band = base.mark_area(color=c["muted"], opacity=0.25).encode(x=x, y=y("p25"), y2="p75:Q")
    median = base.mark_line(color=c["muted"], strokeWidth=2.5, point=alt.OverlayMarkDef(
        color=c["muted"], size=45)).encode(x=x, y=y("median"), tooltip=tip)
    best = base.mark_line(color=strong, strokeWidth=3, point=alt.OverlayMarkDef(
        color=strong, size=55)).encode(x=x, y=y("best"), tooltip=tip)

    last, first = f.iloc[[-1]], f.iloc[[0]]

    def label(row, field, text, align, dx, dy):
        data = row.assign(t=text)
        return alt.Chart(data).mark_text(align=align, dx=dx, dy=dy, fontSize=12,
                                         fontWeight="bold", color=_ink(c)).encode(
            x=alt.X("date:T", scale=xs), y=alt.Y(f"{field}:Q", scale=ys), text="t:N")

    labels = [label(last, "best", "Best model", "right", -8, -10),
              label(last, "median", "Median model", "right", -8, -12),
              label(first, "p25", "Middle half of models", "left", 8, -10)]
    return alt.layer(band, median, best, *labels).properties(height=320)


def frontier_chart(steps, level, closed, open_, wait, end, c, n_access=None):
    """Best score so far for closed and open weights, with the catch-up lag drawn in.

    `n_access` maps each group to its number of models, printed in the legend.
    """
    domain = ["Closed weights", "Open weights"]
    legend = _legend()
    if n_access:
        names = json.dumps({g: f"{g} ({n_access[g]} models)" for g in domain})
        legend = alt.Legend(orient="top", direction="horizontal", labelLimit=0,
                            labelExpr=f"{names}[datum.label]")
    colour = alt.Color("access:N", title=None,
                       scale=alt.Scale(domain=domain, range=_access_colours(c)),
                       legend=legend)
    x = alt.X("date:T", title="Model release date", axis=_date_axis())
    y = alt.Y("eci:Q", title="Best ECI score so far", scale=alt.Scale(zero=False),
              axis=alt.Axis(minExtent=45))
    lines = alt.Chart(steps).mark_line(interpolate="step-after", strokeWidth=2.5).encode(
        x=x, y=y, color=colour)
    dots = alt.Chart(steps[~steps.duplicated(["access", "eci"])]).mark_circle(
        size=45, opacity=0.9).encode(
        x=x, y=y, color=colour,
        tooltip=[alt.Tooltip("model:N", title="Model"),
                 alt.Tooltip("date:T", title="Released", format="%b %Y"),
                 alt.Tooltip("eci:Q", title="ECI", format=".1f")])

    layers = [lines, dots]
    if closed is not None:
        stop = open_[0] if open_ is not None else end
        seg = pd.DataFrame({"start": [closed[0]], "stop": [stop], "y": [level],
                            "mid": [closed[0] + (stop - closed[0]) / 2]})
        layers.append(alt.Chart(seg).mark_rule(
            strokeWidth=3, color=c["muted"],
            strokeDash=[] if open_ is not None else [6, 4]).encode(
            x="start:T", x2="stop:T", y="y:Q"))
        seg["text"] = (f"{wait:.1f} months" if open_ is not None
                       else f"not matched after {wait:.1f} months")
        layers.append(alt.Chart(seg).mark_text(
            align="right", dx=-10, dy=-9, fontSize=12, fontWeight="bold",
            color=_ink(c)).encode(x="start:T", y="y:Q", text="text:N"))
        ends = pd.DataFrame({"date": [closed[0]] + ([open_[0]] if open_ else []),
                             "y": [level] * (2 if open_ else 1),
                             "access": domain[:2 if open_ else 1]})
        layers.append(alt.Chart(ends).mark_point(
            size=110, filled=True, stroke=c["surface"], strokeWidth=1.5).encode(
            x="date:T", y="y:Q", color=colour))
    return alt.layer(*layers).properties(height=340)


def gap_chart(gap, noise, start, end, c):
    """The closed-minus-open gap in score, with the 'within the noise' band shaded.

    Shares its date range and left margin with the frontier chart above it, so the
    two line up.
    """
    xs = alt.Scale(domain=[start, end])
    ys = alt.Scale(domain=[0, float(np.ceil(gap["gap"].max() * 1.1))])
    x = alt.X("date:T", title=None, axis=_date_axis(), scale=xs)
    y = alt.Y("gap:Q", title="Gap (ECI points)", scale=ys, axis=alt.Axis(minExtent=45))
    band = alt.Chart(pd.DataFrame({"x": [start], "x2": [end], "y0": [0.0], "y1": [noise]})
                     ).mark_rect(color=c["muted"], opacity=0.15).encode(
        x=alt.X("x:T", scale=xs), x2="x2:T", y=alt.Y("y0:Q", scale=ys), y2="y1:Q")
    label = alt.Chart(pd.DataFrame({"x": [end], "y": [noise / 2], "t": ["within the noise"]})
                      ).mark_text(align="right", dx=-6, fontSize=11, color=_ink(c)).encode(
        x=alt.X("x:T", scale=xs), y=alt.Y("y:Q", scale=ys), text="t:N")
    line = alt.Chart(gap).mark_line(interpolate="step-after", strokeWidth=2.5,
                                    color=c["muted"]).encode(
        x=x, y=y,
        tooltip=[alt.Tooltip("date:T", title="From", format="%d %b %Y"),
                 alt.Tooltip("gap:Q", title="Gap (ECI points)", format=".1f")])
    return (band + label + line).properties(height=150)


def lag_chart(lag, median, c):
    """Months open weights took to match each closed-weights record."""
    d = lag.copy()
    n_matched = int(d["matched"].sum())
    status = [f"Matched by an open model ({n_matched})",
              f"Not matched yet ({len(d) - n_matched}; months waited so far)"]
    d["status"] = np.where(d["matched"], status[0], status[1])
    x = alt.X("date:T", title="Release date of the closed-weights record",
              axis=_date_axis(), scale=alt.Scale(padding=15))
    y = alt.Y("lag:Q", title="Months until open weights matched it",
              scale=alt.Scale(zero=True))
    pts = alt.Chart(d).mark_point(filled=True, size=90, opacity=0.9).encode(
        x=x, y=y,
        color=alt.Color("status:N", title=None,
                        scale=alt.Scale(domain=status, range=[_access_colours(c)[1], c["muted"]]),
                        legend=_legend()),
        shape=alt.Shape("status:N", scale=alt.Scale(domain=status,
                                                    range=["circle", "triangle-up"]),
                        legend=None),
        tooltip=[alt.Tooltip("model:N", title="Closed record"),
                 alt.Tooltip("eci:Q", title="ECI", format=".1f"),
                 alt.Tooltip("date:T", title="Released", format="%b %Y"),
                 alt.Tooltip("lag:Q", title="Months", format=".1f"),
                 alt.Tooltip("matched_by:N", title="Matched by")])
    rule = alt.Chart(pd.DataFrame({"y": [median]})).mark_rule(
        strokeDash=[6, 4], color=c["muted"]).encode(y="y:Q")
    label = alt.Chart(pd.DataFrame({
        "y": [median], "t": [f"typical wait {median:.1f} months (unmatched counted)"]})
    ).mark_text(align="left", dx=6, dy=-8, color=_ink(c), fontSize=11,
                x=4).encode(y="y:Q", text="t:N")
    return (rule + pts + label).properties(height=260)


def compute_chart(d, lines, missing, era_labels, c):
    """Score against training compute, with the fitted model drawn for each release era.

    Models with no published compute figure sit in a shaded strip on the right,
    at their score, so the chart shows who is missing rather than hiding them.
    """
    # The legend says how many models each period rests on: the 2026 line has few.
    d, lines, missing = (t.assign(era_label=t["era"].map(era_labels))
                         for t in (d, lines, missing))
    colour = alt.Color("era_label:N", title="Released",
                       scale=alt.Scale(domain=[era_labels[e] for e in ERAS],
                                       range=_era_ramp(c)),
                       legend=_legend())
    low = int(d["log_flop"].min())
    ticks = list(range(low, int(d["log_flop"].max()) + 1))
    # Every layer must share one explicit x scale, or Vega-Lite widens it to include 0.
    xs = alt.Scale(domain=[low - 0.2, 28.2])
    y_low = float(np.floor(min(d["eci"].min(), missing["eci"].min()) / 10) * 10)
    y_top = 188.0       # headroom above the best score, for the strip's label
    ys = alt.Scale(domain=[y_low, y_top])
    base = alt.Chart(d).encode(
        x=alt.X("log_flop:Q", title="Training compute (FLOP, log scale)", scale=xs,
                axis=alt.Axis(values=ticks, labelExpr="'1e' + datum.value")),
        y=alt.Y("eci:Q", title="ECI score", scale=ys),
        color=colour)
    pts = base.mark_circle(size=60, opacity=0.7).encode(
        tooltip=[alt.Tooltip("model:N", title="Model"),
                 alt.Tooltip("lab:N", title="Lab"),
                 alt.Tooltip("date:T", title="Released", format="%b %Y"),
                 alt.Tooltip("flop:Q", title="Training compute (FLOP)", format=".1e"),
                 alt.Tooltip("eci:Q", title="ECI", format=".1f")])
    fit = alt.Chart(lines).mark_line(strokeWidth=2.5).encode(
        x=alt.X("log_flop:Q", scale=xs), y=alt.Y("eci:Q", scale=ys), color=colour)
    height = 340
    # The strip and its label are placed in data coordinates, not pixels: a mark
    # sized in pixels can stick out of the plot, and Streamlit then shrinks the
    # plot to fit it.
    strip = alt.Chart(pd.DataFrame({"x": [27.2], "x2": [28.0], "y0": [y_low], "y1": [y_top]})
                      ).mark_rect(color=c["muted"], opacity=0.12).encode(
        x=alt.X("x:Q", scale=xs), x2="x2:Q", y=alt.Y("y0:Q", scale=ys), y2="y1:Q")
    title = alt.Chart(pd.DataFrame({"x": [27.6], "y": [y_top - 4], "t": ["Compute not published"]})
                      ).mark_text(fontSize=11, color=_ink(c)).encode(
        x=alt.X("x:Q", scale=xs), y=alt.Y("y:Q", scale=ys), text="t:N")
    gone = alt.Chart(missing).mark_point(
        filled=False, size=45, strokeWidth=1.6, opacity=0.85).encode(
        x=alt.X("x:Q", scale=xs), y=alt.Y("eci:Q", scale=ys), color=colour,
        tooltip=[alt.Tooltip("model:N", title="Model"),
                 alt.Tooltip("lab:N", title="Lab"),
                 alt.Tooltip("date:T", title="Released", format="%b %Y"),
                 alt.Tooltip("eci:Q", title="ECI", format=".1f")])
    return (strip + title + pts + fit + gone).properties(height=height)


def reach_chart(steps, end, c):
    """Lowest published compute among models that reached a score, over release date."""
    d = pd.concat([steps, steps.iloc[[-1]].assign(date=end)], ignore_index=True)
    xs = alt.Scale(domain=[steps["date"].min(), end])
    lo, hi = steps["flop"].min(), steps["flop"].max()
    ys = alt.Scale(type="log", domain=[10 ** np.floor(np.log10(lo) - 0.3),
                                       10 ** np.ceil(np.log10(hi) + 0.3)])
    ticks = [10.0 ** k for k in range(20, 29)]
    title = ["Lowest published training compute (FLOP)", "of a model at that score"]
    x = alt.X("date:T", title="Model release date", axis=_date_axis(), scale=xs)
    y = alt.Y("flop:Q", title=title, scale=ys,
              axis=alt.Axis(values=ticks, minExtent=45,
                            labelExpr="'1e' + round(log(datum.value) / LN10)"))
    colour = _ink(c)    # one series that is not closed or open weights: a neutral ink
    line = alt.Chart(d).mark_line(interpolate="step-after", strokeWidth=2.5,
                                  color=colour).encode(x=x, y=y)
    dots = alt.Chart(steps).mark_circle(size=70, color=colour).encode(
        x=x, y=y,
        tooltip=[alt.Tooltip("model:N", title="Model"),
                 alt.Tooltip("date:T", title="Released", format="%b %Y"),
                 alt.Tooltip("flop:Q", title="Training compute (FLOP)", format=".1e"),
                 alt.Tooltip("eci:Q", title="ECI", format=".1f")])

    def label(row, align, dx, dy):
        return alt.Chart(row.assign(t=row["model"])).mark_text(
            align=align, dx=dx, dy=dy, fontSize=11, fontWeight="bold", color=_ink(c)).encode(
            x=alt.X("date:T", scale=xs), y=alt.Y("flop:Q", scale=ys), text="t:N")

    layers = [line, dots, label(steps.iloc[[0]], "left", 8, -10)]
    if len(steps) > 1:
        layers.append(label(steps.iloc[[-1]], "right", -8, 16))
    return alt.layer(*layers).properties(height=300)


def spread_chart(g, c):
    """Best and median score of recent models on each benchmark, one row per benchmark."""
    xs = alt.Scale(domain=[-0.3, 1.25])
    xt = "Score (0 = guessing, 1 = the benchmark's ceiling)"

    def x(field):
        return alt.X(f"{field}:Q", title=xt, scale=xs, axis=alt.Axis(format=".1f"))

    y = alt.Y("benchmark:N", sort=g["benchmark"].tolist(), title=None,
              axis=alt.Axis(labelLimit=300))
    colour = alt.Color("period:N", title="Benchmark released",
                       scale=alt.Scale(domain=analysis.BENCH_PERIODS, range=_era_ramp(c)),
                       legend=_legend())
    tip = [alt.Tooltip("benchmark:N", title="Benchmark"),
           alt.Tooltip("release:T", title="Released", format="%b %Y"),
           alt.Tooltip("models:Q", title="Recent models"),
           alt.Tooltip("best:Q", title="Best", format=".2f"),
           alt.Tooltip("median:Q", title="Median", format=".2f"),
           alt.Tooltip("spread:Q", title="Best minus median", format=".2f")]
    ceiling = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(
        strokeDash=[6, 4], color=c["muted"]).encode(x=alt.X("x:Q", scale=xs, title=xt))
    bar = alt.Chart(g).mark_rule(strokeWidth=3).encode(
        y=y, x=x("median"), x2="best:Q", color=colour)
    median = alt.Chart(g).mark_point(filled=False, size=70, strokeWidth=2).encode(
        y=y, x=x("median"), color=colour, tooltip=tip)
    best = alt.Chart(g).mark_point(filled=True, size=70).encode(
        y=y, x=x("best"), color=colour, tooltip=tip)
    return (ceiling + bar + median + best).properties(height=alt.Step(18))


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

def _names(counts, n=3):
    """'OpenAI (4), Anthropic (3) and Google (1)' from a Series of counts."""
    items = [f"{lab} ({k})" for lab, k in counts.head(n).items()]
    return ", ".join(items[:-1]) + " and " + items[-1] if len(items) > 1 else items[0]


def _join(names):
    """['a', 'b', 'c'] becomes 'a, b and c'."""
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _since(points, label):
    """'+5 pts since Oct 2024', or 'no change since Oct 2024' when it is under half a point."""
    return f"no change since {label}" if abs(points) < 0.5 else f"{points:+.0f} pts since {label}"


def _flop(x):
    """2.7e25 rather than Python's 2.7e+25."""
    return f"{x:.1e}".replace("e+", "e")


def _named(when, model):
    """'GPT-5 (Aug 2025)', without repeating a date the model name already has."""
    stamp = f"{when:%b %Y}"
    return model if stamp in model else f"{model} ({stamp})"


def render():
    c = colours()
    data = load()
    eci, scores, comp, snaps = data["eci"], data["scores"], data["comp"], data["snaps"]
    end = eci["date"].max()
    n_no_org, n_other = int(eci["lab"].isna().sum()), int((eci["access"] == "Other").sum())

    st.markdown(
        "Tabs 1 to 3 followed the inputs: who builds models, who owns the chips, "
        "where the money goes. This tab asks what that buys. The "
        "**Epoch Capabilities Index (ECI)** gives every model one score built from about "
        "60 benchmarks (higher means more capable). We use it to ask whether the "
        "leaders are pulling away, how far behind open-weight models are, and "
        "whether our tests can still tell the difference.")

    # ---- calculations used by the cards and several charts ------------------
    top_n = st.slider("How many top models count as the top tier?", 5, 20, 10,
                      key="capability_top_n",
                      help="The top tier is the N highest-scoring models released in the "
                           "12 months to each date; the chart prints how many models that "
                           "was. A smaller N is a stricter 'frontier'.")
    tier = analysis.top_tier(eci, snaps, top_n)
    leaders = analysis.top_labs(tier)
    hh = analysis.hhi(tier)
    last_label, first_label = tier["label"].iloc[-1], tier["label"].iloc[0]
    pools = tier.drop_duplicates("label").set_index("label")["pool"]
    last = tier[tier["label"] == last_label].set_index("lab")["models"]
    top3 = analysis.top_k_share(tier, "models")
    share_last, share_first = top3["share"].iloc[-1], top3["share"].iloc[0]
    names_last, names_first = top3["labs"].iloc[-1], top3["labs"].iloc[0]

    bl = analysis.benchmark_leaders(scores, snaps)
    bl = bl[bl["total"] >= MIN_BENCHMARKS]
    bl_first, bl_last = bl["label"].iloc[0], bl["label"].iloc[-1]
    n_bench = bl.groupby("label")["total"].first()
    bl3 = analysis.top_k_share(bl, "benchmarks")
    held_last, held_first = bl3["share"].iloc[-1], bl3["share"].iloc[0]

    lag = analysis.lag_table(eci)
    median_lag = analysis.km_median(lag["lag"], lag["matched"])
    unmatched = int((~lag["matched"]).sum())
    matched_median = lag.loc[lag["matched"], "lag"].median()

    k1, k2, k3 = st.columns(3, border=True)
    k1.metric(f"Share of the top {top_n} models held by the 3 biggest labs, {last_label}",
              f"{share_last:.0%}",
              _since((share_last - share_first) * 100, first_label),
              delta_color="off", delta_arrow="off")
    k2.metric("Typical wait for open weights to match a closed record",
              f"{median_lag:.1f} months",
              f"{unmatched} of {len(lag)} closed records still unmatched",
              delta_color="off", delta_arrow="off")
    k3.metric(f"Best benchmark scores held by the 3 biggest labs, {bl_last}",
              f"{held_last:.0%}",
              f"{round(held_last * n_bench[bl_last])} of {n_bench[bl_last]} benchmarks · "
              + _since((held_last - held_first) * 100, bl_first),
              delta_color="off", delta_arrow="off")

    # ---- 1. top tier ------------------------------------------------------------
    st.subheader("1. Who holds the top tier?")
    st.markdown(
        f"In the 12 months to {last_label}, {pools[last_label]} models from named labs were "
        f"released ({pools[first_label]} in the 12 months to {first_label}). The top {top_n} by ECI came from "
        f"**{len(last)} labs**: {_names(last.sort_values(ascending=False), 4)}. "
        f"The concentration index (HHI, 0 to 10,000) was **{hh[last_label]:,.0f}** "
        f"against {hh[first_label]:,.0f} in {first_label}. It is noisy: since "
        f"{first_label} it has ranged from {hh.min():,.0f} to {hh.max():,.0f}, and "
        f"today's reading is {'the highest' if hh[last_label] == hh.max() else 'near the top'} "
        f"of that range. The three biggest labs held {share_first:.0%} of the top {top_n} in "
        f"{first_label} ({_join(names_first)}) and hold {share_last:.0%} now "
        f"({_join(names_last)}). Move the slider to see how much the answer depends on how "
        "wide you draw 'the frontier'.")
    st.altair_chart(share_bars(analysis.group_labs(tier, leaders, "models"), "models",
                               leaders, c,
                               [f"Share of the {top_n} highest-scoring models",
                                "released in the 12 months before the date"], "Models",
                               {lab: f"HHI {v:,.0f}" for lab, v in hh.items()},
                               x_title="Snapshot date"),
                    width="stretch",
                    alt=f"Stacked bar chart of which labs made the top {top_n} models by ECI "
                        f"score, for {tier['label'].nunique()} dates six months apart. "
                        f"{', '.join(leaders)} are shown separately and every other lab is "
                        "grouped. The concentration index is printed above each bar.")
    st.caption("Numbers inside the bars are models per lab; the figure above each bar is the "
               "concentration index (HHI). Colours follow today's three biggest labs; every "
               "other lab, including ones that were big earlier, is grouped as Other labs. With "
               "only 10 models per bar, one new release can move the index a lot.")

    top = analysis.top_models(eci, snaps[-1][0], top_n)
    with st.expander(f"Check it: the {top_n} models behind the {hh[last_label]:,.0f}"):
        window_start = snaps[-1][0] - pd.DateOffset(years=1)
        st.markdown(
            f"The last bar is the {top_n} highest-scoring models released after "
            f"{window_start:%d %b %Y} up to {snaps[-1][0]:%d %b %Y}. Each row is one row of "
            "`eci_scores.csv`: find the model in the *Model* column and read its *eci*, "
            "*date* and *Organization*.")
        st.dataframe(
            top.rename(columns={"rank": "Rank", "model": "Model",
                                "organization": "Organisation (as listed)",
                                "lab": "Counted as", "date": "Released", "eci": "ECI score"}),
            hide_index=True, width="stretch",
            column_config={"Released": st.column_config.DateColumn(format="DD MMM YYYY"),
                           "ECI score": st.column_config.NumberColumn(format="%.1f")})
        work = analysis.hhi_working(top)
        st.markdown("The concentration index adds up each lab's squared share of those models:")
        st.dataframe(
            work.rename(columns={"lab": "Lab", "models": "Models",
                                 "share_pct": "Share (%)", "squared": "Share squared"}),
            hide_index=True, width="stretch",
            column_config={"Share (%)": st.column_config.NumberColumn(format="%.1f"),
                           "Share squared": st.column_config.NumberColumn(format="%.0f")})
        st.markdown(f"Sum of the last column: **{work['squared'].sum():,.0f}**. "
                    "(Shares are rounded for display.)")

    # ---- 2. task by task -----------------------------------------------------------
    st.subheader("2. Does one lab lead every task?")
    last_b = bl[bl["label"] == bl_last].set_index("lab")["benchmarks"].sort_values(ascending=False)
    top_cov, all_cov = analysis.eval_coverage(scores, eci)
    st.markdown(
        f"The ECI hides which model is best at what. Of the {n_bench[bl_last]} "
        f"benchmarks with at least 5 scored models, the best score is held by "
        f"{_names(last_b)}. The three biggest labs hold **{held_last:.0%}** of them, "
        f"against {held_first:.0%} in {bl_first}.")
    st.altair_chart(share_bars(analysis.group_labs(bl, leaders, "benchmarks"), "benchmarks",
                               leaders, c,
                               ["Share of benchmarks led", "(highest score up to the date)"],
                               "Benchmarks led",
                               {lab: f"n = {n}" for lab, n in n_bench.items()},
                               x_title="Snapshot date"),
                    width="stretch",
                    alt="Stacked bar chart of which lab holds the best score on each benchmark, "
                        f"for {bl['label'].nunique()} dates six months apart. "
                        f"{', '.join(leaders)} are shown separately and every other lab is "
                        "grouped. The number of benchmarks counted is printed above each bar.")
    st.caption(f"Numbers inside the bars are benchmarks led; n is the benchmarks counted. "
               f"Labs tested on more benchmarks have more chances to lead: the top 10 models "
               f"are scored on a median of {top_cov:.0f}, against {all_cov:.0f} for a typical "
               "model.")

    # ---- 3. the leader against the field ------------------------------------------------
    st.subheader("3. Is the field keeping pace with the leader?")
    field = analysis.field_series(eci)
    field_steady = analysis.field_series(eci, labs=analysis.steady_labs(eci))
    mix = analysis.field_mix(eci, field)
    now, ago, first_row = field.iloc[-1], field.iloc[-5], field.iloc[0]
    lead, lead_ago, lead_first = (r["best"] - r["median"] for r in (now, ago, first_row))
    lead75 = field["best"] - field["p75"]
    lead_steady = field_steady["best"] - field_steady["median"]
    if abs(lead - lead_ago) < 2:
        verdict = "About the same, so the rest of the field is rising about as fast as the leader."
    elif lead < lead_ago:
        verdict = "Narrower, so the field is catching up."
    else:
        verdict = "Wider, so the field is falling behind."
    st.markdown(
        f"The leader is the best model of a year's releases; the field is the typical one. In the "
        f"12 months to {now['date']:%d %b %Y} the best model scored **{now['best']:.1f}** and the "
        f"median model **{now['median']:.1f}**, a lead of **{lead:.1f} points**. A year earlier "
        f"the lead was {lead_ago:.1f}. {verdict}")
    st.altair_chart(field_chart(field, c), width="stretch",
                    alt="Line chart of the best model, the median model and the middle half of "
                        "models, for each 12-month window from 2024 to 2026. All three rise "
                        "together, so the gap between the best and the typical model stays "
                        "roughly constant.")
    st.caption(
        f"The band is the middle half of models. The best model's lead over the 75th "
        f"percentile stays between {lead75.min():.0f} and {lead75.max():.0f} points. The early "
        f"narrowing of its lead over the median is partly a change in which models were "
        f"scored (open-weights share {mix['first']['open']:.0%} to {mix['last']['open']:.0%}).")

    # ---- 4. open versus closed ---------------------------------------------------------
    st.subheader("4. How far behind is open-weight AI?")
    top_closed = int(eci.loc[eci["access"] == "Closed weights", "eci"].max())
    level = st.slider("Score level to compare (ECI)", 126, top_closed, 150,
                      key="capability_level",
                      help="Shows when the first closed model and the first open-weights "
                           "model reached this score.")
    closed, open_, wait, matched = analysis.lag_at(eci, level)
    if matched and open_[0] <= closed[0]:
        sentence = (f"The first open-weights model to reach {level} was "
                    f"**{_named(*open_)}**, no later than the first closed model, "
                    f"**{_named(*closed)}**.")
    elif matched:
        sentence = (f"The first closed model to reach {level} was **{_named(*closed)}**; "
                    f"the first open-weights model was **{_named(*open_)}**, "
                    f"**{wait:.1f} months** later.")
    else:
        sentence = (f"The first closed model to reach {level} was **{_named(*closed)}**. "
                    f"No open-weights model has reached it yet, after "
                    f"**{wait:.1f} months** and counting.")
    st.markdown(sentence)
    st.altair_chart(frontier_chart(analysis.frontier_steps(eci), level, closed, open_,
                                   wait, end, c,
                                   n_access=eci["access"].value_counts().to_dict()),
                    width="stretch",
                    alt="Step chart of the best ECI score so far for closed-weights and "
                        "open-weights models since 2023, with a bar showing how many months "
                        "open weights took to reach the selected score level.")

    gap = analysis.gap_series(eci)
    noise = analysis.gap_noise(eci)
    recent_gap, before_gap = analysis.gap_averages(gap, end)
    gap_now = gap["gap"].iloc[-1]
    st.markdown(
        f"The same two lines, as one number: the best closed model is **{gap_now:.1f} points** "
        f"ahead of the best open model today. Over the last 12 months the gap averaged "
        f"{recent_gap:.1f} points, against {before_gap:.1f} in the 12 months before.")
    st.altair_chart(gap_chart(gap, noise, eci["date"].min(), end, c), width="stretch",
                    alt="Step chart of the gap in ECI points between the best closed-weights "
                        "and the best open-weights model since 2023. A shaded band near zero "
                        "marks gaps too small to tell apart from noise.")
    st.caption(f"Gap = best closed score minus best open score so far. A gap under about "
               f"{noise:.0f} points (shaded) cannot be told from zero at the 90% level.")

    best = {a: eci[eci["access"] == a].nlargest(1, "eci").iloc[0]
            for a in ("Closed weights", "Open weights")}
    cb, ob = best["Closed weights"], best["Open weights"]
    overlap = ob["ci_high"] >= cb["ci_low"]
    st.markdown(
        f"Today's best closed model, {cb['model']}, scores {cb['eci']:.1f} "
        f"(90% interval {cb['ci_low']:.1f} to {cb['ci_high']:.1f}); the best open model, "
        f"{ob['model']}, scores {ob['eci']:.1f} ({ob['ci_low']:.1f} to {ob['ci_high']:.1f}). "
        f"The intervals {'overlap, so the gap could be noise' if overlap else 'do not overlap, so the gap is real'}.")
    st.altair_chart(lag_chart(lag, median_lag, c), width="stretch",
                    alt="Dot chart with one point per closed-weights record, showing the months "
                        "until an open-weights model matched it. Triangles are records not "
                        "matched yet. A dashed line marks the typical wait.")
    st.caption("Each point is a closed-weights record; its height is the months until an "
               "open model matched it. Triangles are not matched yet (height = the wait so "
               "far). The dashed line counts those waits; averaging matched records alone "
               f"gives {matched_median:.1f} months.")

    # ---- 5. compute ---------------------------------------------------------------------------
    st.subheader("5. Does compute still decide capability?")
    reach = st.slider("Score to reach (ECI)", 110, 145, 130, step=5,
                      key="capability_reach",
                      help="The chart follows the cheapest model that reached at least this score.")
    steps = analysis.cheapest_to_reach(comp, reach)
    first_s, last_s = steps.iloc[0], steps.iloc[-1]
    if len(steps) > 1:
        sentence = (f"The lowest published training compute of a model scoring at least {reach} "
                    f"fell from **{_flop(first_s['flop'])} FLOP** ({first_s['model']}, "
                    f"{first_s['date']:%b %Y}) to **{_flop(last_s['flop'])}** ({last_s['model']}, "
                    f"{last_s['date']:%b %Y}): about **{first_s['flop'] / last_s['flop']:.0f}× "
                    "less**. ")
    else:
        sentence = (f"Only {first_s['model']} ({first_s['date']:%b %Y}, {_flop(first_s['flop'])} "
                    f"FLOP) has reached {reach} with a published compute figure. ")
    st.markdown(sentence + "Only models that publish a figure count, so the true cheapest "
                "route may be lower still.")
    st.altair_chart(reach_chart(steps, end, c), width="stretch",
                    alt="Step chart of the lowest published training compute among models that "
                        f"reached an ECI score of at least {reach}, by release date, on a log "
                        "scale. It falls over time, so smaller labs can reach the same score "
                        "with less compute.")

    fit = analysis.compute_fit(comp)
    ec = analysis.era_counts(comp)
    era_labels = {era: f"{era} ({ec.loc[era, 'with_figure']} of {ec.loc[era, 'models']} have a figure)"
                  for era in ERAS}
    st.markdown(
        f"Across all {fit['n']} models with a published figure, 10× more training compute goes "
        f"with about **{fit['per_10x']:.0f} more ECI points**, and at the same compute scores "
        f"rose about **{fit['per_year']:.0f} points a year**. The highest scorers publish no "
        "figure:")
    st.altair_chart(compute_chart(analysis.compute_table(comp),
                                  analysis.compute_lines(comp, fit),
                                  analysis.compute_missing(comp), era_labels, c),
                    width="stretch",
                    alt="Scatter chart of ECI score against training compute on a log scale, "
                        "coloured by release period, with a fitted line for each period. A "
                        "shaded strip on the right holds the models with no published compute "
                        "figure, including most of the highest-scoring models.")
    st.caption(f"Only {fit['n']} of {fit['total']} models have a compute figure. The "
               f"{fit['total'] - fit['n']} hollow dots have none, including "
               f"{fit['top30_missing']} of the top 30 by score, so this chart cannot show "
               "what the frontier costs. Their sideways spread is random; only height means "
               "anything.")

    # ---- 6. do benchmarks still separate the best from the rest ---------------------------------
    st.subheader("6. Can benchmarks still tell leaders from the pack?")
    spread = analysis.benchmark_spread(scores, end)
    old_g = spread[spread["period"] == analysis.BENCH_PERIODS[0]]
    new_g = spread[spread["period"] != analysis.BENCH_PERIODS[0]]
    tight = old_g.nsmallest(1, "spread").iloc[0] if len(old_g) else None
    sentence = (f"Take the models released in the last year. On the {len(spread)} benchmarks "
                f"with at least 12 of them, the best model beats the median model by a median "
                f"of **{spread['spread'].median():.2f}** of the score range.")
    if len(old_g) >= 3 and len(new_g) >= 3:
        sentence += (f" On benchmarks released in 2024 or earlier it is "
                     f"**{old_g['spread'].median():.2f}** ({len(old_g)} benchmarks); on newer ones "
                     f"**{new_g['spread'].median():.2f}** ({len(new_g)}).")
    if tight is not None:
        sentence += (f" {tight['benchmark']} is the extreme: median {tight['median']:.2f}, best "
                     f"{tight['best']:.2f}.")
    st.markdown(sentence + " Where the two sit together near the ceiling, a test no longer "
                "shows who is ahead.")
    st.altair_chart(spread_chart(spread, c), width="stretch",
                    alt="Dumbbell chart with one row per benchmark, joining the median score to "
                        "the best score of models released in the last year, sorted from the "
                        "widest spread to the narrowest. A dashed line marks the ceiling. Older "
                        "benchmarks sit at the bottom, with the two close together near the "
                        "ceiling.")
    st.caption("● best model, ○ median model, for models released in the last 12 months. "
               "Some scores sit above 1 or below 0 because of how Epoch sets a benchmark's "
               "ceiling and chance level.")

    # ---- verdict --------------------------------------------------------------------------------------
    with st.container(border=True):
        st.markdown("#### Summary: is the gap between the leaders and everyone else closing?")
        st.markdown(
            f"**No sign that the gap at the top is closing.** The three biggest labs hold {share_last:.0%} of the top "
            f"{top_n} models ({_join(names_last)}), against {share_first:.0%} in {first_label} "
            f"({_join(names_first)}), and {held_last:.0%} of the best benchmark scores, against "
            f"{held_first:.0%} in {bl_first}. The best model leads the median model by {lead:.0f} points, "
            f"against {lead_ago:.0f} a year earlier. Open-weight models trail the "
            f"closed frontier by about {median_lag:.0f} months, and that wait has not clearly "
            f"shrunk; the gap in score averaged {recent_gap:.0f} points over the last year, "
            f"against {before_gap:.0f} the year before, and {unmatched} recent closed records "
            "are still unmatched. Smaller labs can now reach a given score with far less "
            "compute. And a "
            "gap that looks small on a test strong models have already beaten does not "
            "prove a small gap in capability.")

    # ---- method ---------------------------------------------------------------------------------------------
    with st.expander("Data and methods:"):
        st.markdown(f"""
**Source:** Epoch AI, *Capabilities & benchmarking* (CC-BY 4.0), downloaded
{loading.DOWNLOADED} from <https://epoch.ai/benchmarks>. Raw files are in
`dashboards/tab4_capability/data/raw/epoch_capabilities/`; cleaning is in
`src/loading.py` and calculations in `src/analysis.py`.

| Chart | File | What we did |
|---|---|---|
| Cards, charts 1 and 2 | `eci_scores.csv`, `processed_data_for_eci.csv` | Lab = first organisation listed, sub-labs merged. Chart 1: the {top_n} highest-ECI models released in the 12 months to each date; HHI = sum of squared lab shares (in %). Chart 2: for each benchmark with 5+ scored models, the lab of the highest-scoring model (ties to the earliest). |
| Chart 3 | `eci_scores.csv` | Every model released in the 12 months to each date (quarterly, from the first full year), any lab: the best score, the median, and the 25th and 75th percentiles. Lead = best minus median. Checked against the 75th percentile and against labs with 10+ models. |
| Chart 4 | `eci_scores.csv` | Running best ECI score for *Open weights* and *Closed weights* (Epoch's accessibility group). Lag = months from a closed record to the first open model scoring at least as high; the typical lag is a Kaplan–Meier median, which counts records still unmatched. |
| Chart 5 | `eci_scores.csv`, `model_metadata.csv` | Matched models by name to a published training-compute figure. Step chart: among models with ECI at or above the chosen score, the running minimum of compute, by release date. Scatter: ECI = a + b·log₁₀(FLOP) + c·years, by least squares. |
| Chart 6 | `processed_data_for_eci.csv`, `benchmark_metadata.csv` | Each score rescaled to (score − random baseline) ÷ (ceiling − baseline). For each benchmark with at least 12 models released in the last 12 months: the best and the median rescaled score. |

**Notes by chart:**
- **Chart 1:** a lab is the first organisation Epoch lists for a model, with sub-labs merged
  (Google DeepMind → Google); the {n_no_org} models with no organisation are left out. Bars are exactly
  6 months apart, ending on the last date in the data; the first bar is the earliest date with a
  full 12 months of data behind it.
- **Chart 2:** a tie goes to the model released first; n grows as more benchmarks reach 5 scored
  models.
- **Chart 3:** points are every 3 months. Counting only labs with 10 or more models in the file,
  the best model's lead over the median stays between {lead_steady.min():.0f} and
  {lead_steady.max():.0f} points. The lead over the median fell from {lead_first:.0f} in
  {first_row['date']:%b %Y} to {lead:.0f}; over the same time the share of Chinese labs' models
  in the window went from {mix['first']['china']:.0%} to {mix['last']['china']:.0%}.
- **Chart 4, gap:** it steps up when a closed model sets a record and down when an open model
  catches up. The noise level is √2 times the median half-width of a model's 90% interval. It
  starts on the first date both groups have a model.
- **Chart 4, lag:** a record no open model has matched is kept with the wait so far, so the true
  lag is at least that long (Kaplan–Meier). Models Epoch labels 'Other' (unknown or limited
  access, {n_other} of {len(eci)}) are in neither group.
- **Chart 5:** a model with no compute figure cannot appear in the step chart, and the leading
  closed models publish none, so the true cheapest route may be lower. The scatter's lines are the
  fitted model behind the numbers in the text: the same slope for every period, shifted up for
  later releases.
- **Chart 6:** the spread is the best score minus the median, in rescaled units. Benchmarks are
  grouped by their own release year. Some scores exceed 1 because Epoch sets a ceiling below a
  perfect score, and some fall below 0 when models do worse than guessing.

**Known limits:** The ECI is Epoch's own composite and carries uncertainty (90%
intervals in `eci_scores.csv`). {n_no_org} models with no organisation and {n_other} with
'Other' access are left out of lab and open-versus-closed comparisons. Only {fit['n'] / fit['total']:.0%}
of models have a compute figure, and almost none of the top 30. Labs that get
tested on more benchmarks have more chances to hold a best score. A model's release
date comes from `eci_scores.csv`; 54 score rows (12 models) carry a different date in
`processed_data_for_eci.csv`, by a median of 6 days. The data runs from Feb 2023 to
{end:%d %B %Y}. Benchmarks without a file in the download (29 of 91) are not used.
""")
