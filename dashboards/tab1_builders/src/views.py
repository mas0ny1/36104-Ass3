"""Charts and page layout for the Builders tab.

Data: Epoch AI, 'Data on AI models' (CC-BY). Cleaning is in loading.py,
calculations in analysis.py; the download record is in this folder's README.
"""

import altair as alt
import pandas as pd
import streamlit as st

from core.theme import colours

from . import analysis, loading

LATEST_FULL_YEAR = 2025
BASE_YEAR = 2023             # first year with a meaningful number of large models


@st.cache_data
def load():
    notable = loading.load_notable()
    large = loading.load_large_scale()
    frontier = loading.load_frontier()

    by_count = analysis.org_credit(large)
    by_compute = analysis.org_credit(large, weight="compute")

    return {
        "notable": notable,
        "frontier": frontier,
        "by_count": by_count,
        "by_compute": by_compute,
        "home": analysis.org_countries(by_count),
    }


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def sector_chart(notable, end_year, c):
    d = notable[notable["year"].between(2010, end_year)]
    tbl = d.groupby(["year", "sector"]).size().rename("models").reset_index()
    tbl["share"] = tbl["models"] / tbl.groupby("year")["models"].transform("sum")
    tbl["order"] = tbl["sector"].map(loading.SECTORS.index)

    return alt.Chart(tbl).mark_bar(stroke=c["surface"], strokeWidth=1.5).encode(
        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("models:Q", stack="normalize", title="Share of notable models",
                axis=alt.Axis(format="%", tickCount=5)),
        color=alt.Color("sector:N", title=None,
                        scale=alt.Scale(domain=loading.SECTORS,
                                        range=c["series"] + [c["other"]]),
                        legend=alt.Legend(orient="top", direction="horizontal",
                                          labelLimit=0)),
        order=alt.Order("order:Q", sort="ascending"),
        tooltip=[alt.Tooltip("year:O", title="Year"),
                 alt.Tooltip("sector:N", title="Sector"),
                 alt.Tooltip("models:Q", title="Notable models"),
                 alt.Tooltip("share:Q", title="Share of year", format=".0%")],
    ).properties(height=320)


def leaders_chart(credit, home, start, end_year, rank_by, c, n=15):
    d = credit[credit["year"].between(start, end_year)]
    tot = d.groupby("parent")["credit"].sum()
    tbl = tot.sort_values(ascending=False).head(n).rename("value").reset_index()
    tbl["country"] = tbl["parent"].map(home).fillna("Rest of world")
    if rank_by == "compute":
        tbl["value"] = tbl["value"] / tot.sum()
        fmt, title = ".0%", "Share of large-scale training compute (where known)"
    else:
        fmt, title = ",.1~f", "Large-scale models (shared models split evenly)"

    # An explicit order: "-x" sorting is dropped when the bars and labels are layered.
    y = alt.Y("parent:N", sort=tbl["parent"].tolist(), title=None)
    bars = alt.Chart(tbl).mark_bar(cornerRadiusEnd=4, size=16).encode(
        x=alt.X("value:Q", title=title, axis=alt.Axis(format=fmt, tickCount=6)),
        y=y,
        color=alt.Color("country:N", title=None,
                        scale=alt.Scale(domain=loading.COUNTRY_GROUPS,
                                        range=c["series"]),
                        legend=alt.Legend(orient="top", direction="horizontal",
                                          labelLimit=0)),
        tooltip=[alt.Tooltip("parent:N", title="Lab"),
                 alt.Tooltip("country:N", title="Based in"),
                 alt.Tooltip("value:Q", title=title, format=fmt)],
    )
    labels = alt.Chart(tbl).mark_text(align="left", dx=4, color=c["muted"]).encode(
        x="value:Q", y=y, text=alt.Text("value:Q", format=fmt))
    return (bars + labels).properties(height=28 * len(tbl) + 20)


def cost_chart(frontier, c):
    d = frontier.dropna(subset=["cost_usd"])
    d = d[d["cost_usd"] > 0]
    growth, trend, n = analysis.cost_trend(frontier)

    y = alt.Y("cost_usd:Q", title="Training cost (2023 US$, log scale)",
              scale=alt.Scale(type="log"),
              axis=alt.Axis(format="$~s", values=[10 ** k for k in range(0, 10)],
                            labelExpr="replace(datum.label, 'G', 'B')"))
    x = alt.X("date:T", title=None)
    line = alt.Chart(trend).mark_line(color=c["muted"], strokeDash=[6, 4],
                                      strokeWidth=2).encode(x=x, y=y)
    dots = alt.Chart(d).mark_circle(size=80, color=c["series"][0], opacity=0.85,
                                    stroke=c["surface"], strokeWidth=1.5).encode(
        x=x, y=y,
        tooltip=[alt.Tooltip("Model:N"),
                 alt.Tooltip("parent:N", title="Lab"),
                 alt.Tooltip("date:T", title="Released", format="%b %Y"),
                 alt.Tooltip("cost_usd:Q", title="Training cost (2023 US$)",
                             format="$,.0f")])
    # Label only a few anchor points: the start, GPT-4, and the record.
    first = d[d["Model"] == "AlexNet"]
    later = pd.concat([d[d["Model"] == "GPT-4 (Mar 2023)"],
                       d.nlargest(1, "cost_usd")])
    name_l = alt.Chart(first).mark_text(
        align="left", dx=9, fontSize=11, color=c["muted"]).encode(
        x=x, y=y, text="Model:N")
    name_r = alt.Chart(later).mark_text(
        align="right", dx=-9, fontSize=11, color=c["muted"]).encode(
        x=x, y=y, text="Model:N")
    return (line + dots + name_l + name_r).properties(height=340), growth, n


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

def render():
    c = colours()
    data = load()
    notable = data["notable"]

    st.markdown(
        "Before compute, money or benchmarks, the simplest test of concentration "
        "is to count who actually releases the models. This tab uses Epoch AI's "
        "catalogue of **notable**, **large-scale** (at least 10²³ FLOP of "
        "training compute) and **frontier** models.")

    include_2026 = st.toggle(
        "Include 2026 (January–September, still being catalogued)", value=False,
        key="builders_include_2026",
        help="Epoch adds models with a lag, so 2026 counts are incomplete and "
             "would make the latest year look smaller than it is.")
    end_year = 2026 if include_2026 else LATEST_FULL_YEAR

    # ---- headline numbers (always the latest complete year) ---------------
    y0, y1 = BASE_YEAR, LATEST_FULL_YEAR
    sec = notable[notable["year"].isin([y0, y1])]
    ind = (sec.assign(ind=sec["sector"].eq("Industry"))
           .groupby("year")["ind"].mean())
    priciest = data["frontier"].dropna(subset=["cost_usd"]).nlargest(1, "cost_usd").iloc[0]

    k1, k2 = st.columns(2, border=True)
    k1.metric(f"Industry share of notable models, {y1}", f"{ind[y1]:.0%}",
              f"{(ind[y1] - ind[y0]) * 100:+.0f} pts since {y0}", delta_color="off")
    k2.metric("Most expensive training run so far", f"${priciest['cost_usd'] / 1e6:,.0f}M",
              f"{priciest['Model']}, {priciest['date']:%Y}", delta_color="off",
              delta_arrow="off")

    # ---- 1. sector -----------------------------------------------------------
    st.subheader("1. Institution Type breakdown of developed AI models from 2010 to 2025")
    st.markdown(
        f"In {y0}, {ind[y0]:.0%} of notable models came from companies alone; "
        f"by {y1} it was **{ind[y1]:.0%}**. Academic-only models, which made up "
        "most of the field before 2015, have almost disappeared.")
    st.altair_chart(sector_chart(notable, end_year, c), width="stretch")
    st.caption("Each model is labelled by the sectors of every organisation Epoch "
               "lists for it. Industry + academia together = collaboration. "
               "'Other' = government, non-profit and research collectives.")

    # ---- 2. who --------------------------------------------------------------
    st.subheader("2. Top Companies publishing large scale models")
    rank = st.segmented_control(
        "Rank labs by", ["Number of models", "Share of training compute"],
        default="Share of training compute", key="builders_rank")
    rank_by = "count" if rank == "Number of models" else "compute"
    credit = data["by_count"] if rank_by == "count" else data["by_compute"]
    top_count = analysis.ranking(data["by_count"], y0, end_year)
    top_comp = analysis.ranking(data["by_compute"], y0, end_year)
    lead = top_count.index[0]
    lead_home = data["home"].get(lead, "Rest of world")
    top3 = ", ".join(top_comp.index[:3])
    top3_share = top_comp.head(3).sum()
    st.markdown(
        f"Large-scale models released {y0}–{end_year}. By number of models the "
        f"most prolific lab is **{lead}** ({lead_home}). "
        f"By measured training compute, the top three ({top3}) hold "
        f"**{top3_share:.0%}** between them.")
    st.altair_chart(leaders_chart(credit, data["home"], y0, end_year, rank_by, c),
                    width="stretch")
    st.caption("Sub-labs are merged into their parent (Google Brain and DeepMind "
               "→ Google; FAIR → Meta). Country is the lab's most common country "
               "in Epoch's records. Compute shares leave out models with no "
               "compute figure, so labs that publish less are understated.")

    # ---- 3. cost -------------------------------------------------------------
    st.subheader("3. Price Breakdown to develop Cutting-Edge AI Models")
    chart, growth, n_cost = cost_chart(data["frontier"], c)
    st.markdown(
        f"Across the {n_cost} frontier models with a cost estimate, the cost of "
        f"the training run has grown about **{growth:.1f}× per year**. "
        f"{priciest['Model']} cost roughly ${priciest['cost_usd'] / 1e6:,.0f}M "
        "in compute alone, before staff, data or failed runs.")
    st.altair_chart(chart, width="stretch")
    st.caption("Frontier = in the top 5 by training compute when released. "
               "Costs are Epoch's estimates of cloud-equivalent compute cost in "
               "2023 dollars. Dashed line: log-linear fit.")

    # ---- verdict -------------------------------------------------------------
    with st.container(border=True):
        st.markdown("#### Summary")
        st.markdown(
            f"Companies (as opposed to academia) now make {ind[y1]:.0%} of notable models. Many companies still release large "
            f"models, with {lead} ({lead_home}) the most prolific, however the training compute behind them is concentrated: "
            f"{', '.join(top_comp.index[:2])} and {top_comp.index[2]} account for "
            f"{top3_share:.0%} of it. The cost of a cutting-edge AI training and development "
            f"has grown about {growth:.1f}× a year, reaching "
            f"${priciest['cost_usd'] / 1e6:,.0f}M as a maximum example. **Many companies still build large models, however "
            "only a few can afford the largest ones.**")

    # ---- method --------------------------------------------------------------
    with st.expander("Data and methods:"):
        st.markdown(f"""
**Source:** Epoch AI, *Data on AI models* (CC-BY 4.0), downloaded
{loading.DOWNLOADED} from <https://epoch.ai/data/ai-models>. Raw files are in
`dashboards/tab1_builders/data/raw/epoch_ai_models/`; cleaning is in
`src/loading.py` and calculations in `src/analysis.py`.

| Chart | File | What we did |
|---|---|---|
| Headline: industry share, chart 1 | `notable_ai_models.csv` | Labelled each model by the sectors in *Organization categorization*: all Industry → Industry; all Academia → Academia; both → collaboration; anything else → Other. Share = models per sector ÷ models that year. |
| Chart 2 | `large_scale_ai_models.csv` | Merged sub-labs into parents and split each model equally between its parent organisations. Summed per lab over {y0}–{end_year}, either counting models (all rows) or weighting by *Training compute (FLOP)* (rows with a figure); top 15 shown. |
| Headline: cost, chart 3 | `frontier_ai_models.csv` | *Training compute cost (2023 USD)*; trend = least-squares fit of log₁₀(cost) on release date. |

**Known limits:** Epoch's catalogue is selective and lags new releases by
months. About 40% of large-scale models have no compute figure, mostly recent
flagships from labs that publish little, so compute shares in chart 2 are
indicative. Cost estimates cover compute only.
""")
