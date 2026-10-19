"""Charts and page layout for Tab 2: Compute Infrastructure.

Visualizes physical supercomputer clusters and upstream AI chip shipments,
following the layout and visual structure established in Tab 1.
"""

import altair as alt
import pandas as pd
import streamlit as st

from core.theme import colours
from . import analysis, loading

LATEST_FULL_YEAR = 2025


@st.cache_data
def load():
    """Load cluster and chip sales datasets."""
    clusters = loading.load_clusters()
    chips = loading.load_chip_sales_timeline()
    return {
        "clusters": clusters,
        "chips": chips,
    }


# --------------------------------------------------------------------------
# Charts (Visualizations matching Mason's Tab 1 styling & padding)
# --------------------------------------------------------------------------

def owners_chart(tbl, c):
    """Horizontal bar chart: Top cluster owners by H100 equivalents.
    Visual Family: Magnitude & Ranking.
    """
    y = alt.Y("parent:N", sort=tbl["parent"].tolist(), title=None,
              axis=alt.Axis(labelLimit=250, labelOverlap=False))
    bars = alt.Chart(tbl).mark_bar(cornerRadiusEnd=4, size=16).encode(
        x=alt.X("h100_equiv:Q", title="Frontier compute capacity (H100-equivalent GPUs)",
                axis=alt.Axis(format="~s", tickCount=6)),
        y=y,
        color=alt.Color("country_group:N", title=None,
                        scale=alt.Scale(domain=loading.COUNTRY_GROUPS,
                                        range=c["series"] + [c["other"]]),
                        legend=alt.Legend(orient="top", direction="horizontal",
                                          labelLimit=0)),
        tooltip=[alt.Tooltip("parent:N", title="Organization"),
                 alt.Tooltip("country_group:N", title="Based in"),
                 alt.Tooltip("h100_equiv:Q", title="Capacity (H100 eq)", format=",.0f"),
                 alt.Tooltip("share:Q", title="Share of compute", format=".1%"),
                 alt.Tooltip("clusters:Q", title="Tracked clusters")],
    )
    labels = alt.Chart(tbl).mark_text(align="left", dx=4, color=c["muted"], fontSize=11).encode(
        x="h100_equiv:Q", y=y, text=alt.Text("h100_equiv:Q", format="~s"))
    return (bars + labels).properties(height=28 * len(tbl) + 24)


def country_chart(tbl, c):
    """Horizontal bar chart: Global compute share by Country / Region.
    Visual Family: Part-to-Whole.
    """
    y = alt.Y("country_group:N", sort=loading.COUNTRY_GROUPS, title=None,
              axis=alt.Axis(labelLimit=250, labelOverlap=False))
    bars = alt.Chart(tbl).mark_bar(cornerRadiusEnd=4, size=18).encode(
        x=alt.X("share:Q", title="Share of global frontier compute capacity",
                axis=alt.Axis(format="%", tickCount=6)),
        y=y,
        color=alt.Color("country_group:N", title=None,
                        scale=alt.Scale(domain=loading.COUNTRY_GROUPS,
                                        range=c["series"] + [c["other"]]),
                        legend=None),
        tooltip=[alt.Tooltip("country_group:N", title="Country / Region"),
                 alt.Tooltip("share:Q", title="Share of compute", format=".1%"),
                 alt.Tooltip("h100_equiv:Q", title="Capacity (H100 eq)", format=",.0f"),
                 alt.Tooltip("clusters:Q", title="Tracked clusters")],
    )
    labels = alt.Chart(tbl).mark_text(align="left", dx=4, color=c["muted"], fontSize=11).encode(
        x="share:Q", y=y, text=alt.Text("share:Q", format=".1%"))
    return (bars + labels).properties(height=36 * len(tbl) + 30)


def silicon_chart(chips, c):
    """100% Normalized Stacked Area: Share of AI accelerator compute delivered (2022–2026).
    Visual Family: Change Over Time.
    """
    tbl = analysis.chip_share_timeline(chips)
    return alt.Chart(tbl).mark_area(opacity=0.85, stroke=c["surface"], strokeWidth=1).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%b %Y", tickCount=6)),
        y=alt.Y("cumulative_h100:Q", stack="normalize",
                title="Share of delivered AI accelerator compute",
                axis=alt.Axis(format="%", tickCount=5)),
        color=alt.Color("designer:N", title=None,
                        scale=alt.Scale(domain=["Nvidia", "Google", "AMD", "Huawei", "Amazon"],
                                        range=c["series"] + [c["other"], c["muted"]]),
                        legend=alt.Legend(orient="top", direction="horizontal",
                                          labelLimit=0)),
        tooltip=[alt.Tooltip("date:T", title="Quarter end", format="%B %Y"),
                 alt.Tooltip("designer:N", title="Chip designer"),
                 alt.Tooltip("share:Q", title="Market share", format=".1%"),
                 alt.Tooltip("cumulative_h100:Q", title="Delivered compute (H100 eq)", format=",.0f")],
    ).properties(height=320)


def power_chart(top_power, c):
    """Horizontal bar chart: Top power-hungry AI clusters in Megawatts (MW).
    Visual Family: Correlation & Distribution.
    """
    d = top_power.copy()
    d["mw_label"] = d["power_mw"].round().astype(int).astype(str) + " MW"
    d["power_tooltip"] = d["power_mw"].apply(lambda v: f"{v:,.1f} MW")
    d["homes_tooltip"] = d["homes_equivalent"].apply(lambda v: f"{v:,.0f} homes")
    y = alt.Y("Name:N", sort=d["Name"].tolist(), title=None,
              axis=alt.Axis(labelLimit=280, labelOverlap=False))
    bars = alt.Chart(d).mark_bar(cornerRadiusEnd=4, size=16).encode(
        x=alt.X("power_mw:Q", title="Dedicated electrical power capacity (Megawatts MW)",
                axis=alt.Axis(format=",.0f", tickCount=6)),
        y=y,
        color=alt.Color("country_group:N", title=None,
                        scale=alt.Scale(domain=loading.COUNTRY_GROUPS,
                                        range=c["series"] + [c["other"]]),
                        legend=alt.Legend(orient="top", direction="horizontal",
                                          labelLimit=0)),
        tooltip=[alt.Tooltip("Name:N", title="Cluster name"),
                 alt.Tooltip("parent:N", title="Operator"),
                 alt.Tooltip("country_group:N", title="Based in"),
                 alt.Tooltip("power_tooltip:N", title="Power capacity"),
                 alt.Tooltip("homes_tooltip:N", title="Equivalent households")],
    )
    labels = alt.Chart(d).mark_text(align="left", dx=4, color=c["muted"], fontSize=11).encode(
        x="power_mw:Q", y=y, text=alt.Text("mw_label:N"))
    return (bars + labels).properties(height=28 * len(d) + 24)


# --------------------------------------------------------------------------
# Page Render
# --------------------------------------------------------------------------

def render():
    c = colours()
    data = load()
    clusters_raw = data["clusters"]
    chips_raw = data["chips"]

    st.markdown(
        "Model weights can be downloaded anywhere, but training cutting-edge AI requires "
        "enormous physical hardware: specialized accelerator chips, high-speed interconnects, "
        "and gigawatt-scale electrical infrastructure. This tab tracks who owns the **physical "
        "supercomputers** and the **silicon supply chain** powering frontier AI.")

    include_2026 = st.toggle(
        "Include 2026 (still being catalogued)", value=False,
        key="compute_include_2026",
        help="Epoch adds clusters with a lag, so 2026 records are incomplete.")
    end_year = 2026 if include_2026 else LATEST_FULL_YEAR

    # ---- Headline metrics (Bordered cards matching Mason's style) ----------
    stats = analysis.calculate_concentration_stats(clusters_raw, end_year=end_year)
    top_power = analysis.top_power_clusters(clusters_raw, end_year=end_year, n=10)
    priciest_power = top_power.iloc[0] if not top_power.empty else None

    k1, k2 = st.columns(2, border=True)
    k1.metric(
        f"US share of frontier cluster compute, {end_year}",
        f"{stats['us_share']:.0%}",
        f"CR4: {stats['cr4']:.0%} across Top 4 labs",
        delta_color="off",
    )
    if priciest_power is not None:
        k2.metric(
            "Largest single cluster power draw",
            f"{priciest_power['power_mw']:.0f} MW",
            f"{priciest_power['Name']} (~{priciest_power['homes_equivalent']:,.0f} homes)",
            delta_color="off",
            delta_arrow="off",
        )

    # ---- 1. Top Cluster Owners ---------------------------------------------
    st.subheader("1. Institutional Concentration: Who Owns the Supercomputers?")
    top_owners = analysis.owner_ranking_table(clusters_raw, end_year=end_year, n=10)
    lead = top_owners.iloc[0]["parent"]
    lead_share = top_owners.iloc[0]["share"]
    top3_names = ", ".join(top_owners.iloc[:3]["parent"].tolist())
    top3_share = top_owners.iloc[:3]["share"].sum()

    st.markdown(
        f"Across tracked facilities operational by {end_year}, the largest individual cluster operator is "
        f"**{lead}**, holding **{lead_share:.0%}** of measured frontier compute. The top three owners "
        f"({top3_names}) control **{top3_share:.0%}** between them.")
    st.altair_chart(owners_chart(top_owners, c), width="stretch")
    st.caption("Normalized to NVIDIA H100 SXM5 80GB peak 16-bit FLOP/s. Sub-clusters are combined under "
               "their parent operator (e.g. Microsoft Azure and OpenAI Goodyear clusters grouped).")

    # ---- 2. Geopolitical Distribution --------------------------------------
    st.subheader("2. Geopolitical Breakdown: Where Does the Compute Reside?")
    country_tbl = analysis.country_share_table(clusters_raw, end_year=end_year)
    us_share = stats["us_share"]
    eu_share = stats["europe_share"]
    cn_share = stats["china_share"]
    row_share = stats["row_share"]

    st.markdown(
        f"The United States hosts **{us_share:.0%}** of global frontier cluster capacity, "
        f"leaving Europe (**{eu_share:.0%}**), China (**{cn_share:.0%}**), and the Rest of World "
        f"(**{row_share:.0%}**) far behind in physical infrastructure.")
    st.altair_chart(country_chart(country_tbl, c), width="stretch")
    st.caption("Country reflects the physical host facility location and operator headquarters. "
               "European sovereign clusters include EuroHPC JU (Jupiter, LUMI) and national supercomputers.")

    # ---- 3. Silicon Supply Monopoly ----------------------------------------
    st.subheader(f"3. Silicon Supply Monopoly: AI Chip Delivery by Designer (2022–{end_year})")
    chips_filtered = chips_raw[chips_raw["date"].dt.year <= end_year].copy()
    latest_chip_shares = analysis.chip_designer_shares(chips_filtered)
    nv_share = latest_chip_shares.get("Nvidia", 0.76)
    google_share = latest_chip_shares.get("Google", 0.20)

    st.markdown(
        f"Upstream silicon manufacturing reveals an even tighter choke point: **Nvidia commands "
        f"{nv_share:.0%}** of all delivered AI accelerator compute shipped between 2022 and {end_year}. "
        f"Google TPU represents the only significant proprietary ASIC alternative (**{google_share:.0%}**), while "
        "AMD, Huawei, and Amazon together account for the remaining sliver.")
    st.altair_chart(silicon_chart(chips_filtered, c), width="stretch")
    st.caption(f"Data source: Epoch AI, 'Data on AI chip sales' (quarterly estimates, 2022–{end_year}). "
               "Normalized 100% share of delivered 16-bit compute (H100 equivalents).")

    # ---- 4. The Energy Moat ------------------------------------------------
    st.subheader("4. The Energy Moat: Most Power-Hungry AI Megaclusters")
    if not top_power.empty:
        st.markdown(
            f"Frontier training runs have moved from server rooms to utility-scale substations. "
            f"**{priciest_power['Name']}** draws **{priciest_power['power_mw']:.0f} MW**—comparable "
            f"to a small nuclear reactor or the electricity consumption of **~{priciest_power['homes_equivalent']:,.0f} homes**.")
        st.altair_chart(power_chart(top_power, c), width="stretch")
        st.caption("Dedicated power capacity in Megawatts (MW). A standard commercial data center draws "
                   "15–30 MW; frontier megaclusters exceed 100–350 MW, creating massive capital and grid moats.")

    # ---- Verdict -----------------------------------------------------------
    with st.container(border=True):
        st.markdown("#### Summary: Is Compute Concentrating?")
        st.markdown(
            f"Frontier compute is intensely concentrated across both geographic and hardware supply layers. "
            f"The United States hosts **{us_share:.0%}** of global supercomputing capacity, with the four "
            f"largest US operators controlling **{stats['cr4']:.0%}** of all tracked compute. Upstream, "
            f"**Nvidia controls {nv_share:.0%}** of delivered accelerator compute. Furthermore, megaclusters "
            f"now require between 50 MW and 350 MW of dedicated electrical capacity, making physical power "
            "and electrical grid access the ultimate barrier to entry.")

    # ---- Method ------------------------------------------------------------
    with st.expander("Data and methods:"):
        st.markdown(f"""
**Sources:**
- **Supercomputing Clusters:** Epoch AI, *GPU Clusters / AI Supercomputers* (CC-BY 4.0), downloaded {loading.DOWNLOADED} from <https://epoch.ai/data/gpu_clusters.csv> (482 clusters).
- **AI Chip Sales & Deliveries:** Epoch AI, *Data on AI chip sales* (CC-BY 4.0), downloaded {loading.DOWNLOADED} from <https://epoch.ai/data/ai-chip-sales> (74 quarterly records, 2022–{end_year}).

Raw files are stored in `dashboards/tab2_compute/data/raw/`; cleaning and entity mappings are in `src/loading.py`, and calculations in `src/analysis.py`.

| Chart / Metric | File | What we did |
|---|---|---|
| Headline: US share & CR4, Chart 1 (Top Owners), Chart 2 (Geopolitical Share) | `gpu_clusters.csv` | Normalized cluster capacity to NVIDIA H100 SXM5 80GB peak 16-bit FLOP/s (`H100 equivalents`). Mapped sub-clusters and cloud instances to parent corporate owners (e.g. Microsoft Azure and OpenAI Goodyear grouped). Categorized sovereign host facilities into 4 geopolitical regions. Summed compute capacity per owner and region operational up to {end_year}. Calculated market concentration ratios (CR4: {stats['cr4']:.1%}, CR8: {stats['cr8']:.1%}, HHI: {stats['hhi']:,.0f}). |
| Headline: Largest cluster power, Chart 4 (Power Moat) | `gpu_clusters.csv` | Filtered dedicated electrical capacity in *Power Capacity (MW)* for landmark facilities (>10 MW). Converted to residential equivalencies assuming 1 MW continuously powers ~800 average US homes. |
| Headline: Nvidia dominance, Chart 3 (Silicon Supply) | `cumulative_timelines_by_designer.csv` | Filtered quarterly cumulative delivered compute by hardware designer (2022–{end_year}). Normalized quarterly totals into 100% market shares (`stack="normalize"`) across Nvidia, Google, AMD, Huawei, and Amazon. |

**Known limits:**
- **Export controls and anonymized facilities:** Trade restrictions and national security sensitivities cause Chinese developers to conceal cluster specifications; Epoch tracks 190 clusters in China anonymously.
- **Undisclosed proprietary hardware:** Private clusters that hyperscalers do not disclose publicly (e.g., proprietary internal TPU research pods or undisclosed internal enterprise deployments) are absent from public records.
- **Theoretical peak vs. realized MFU:** H100 equivalents measure theoretical peak 16-bit tensor performance; real-world Model FLOPs Utilization (MFU) averages 30–50% due to distributed interconnect bottlenecks and memory latency.
- **Defense installations:** Classified government and intelligence supercomputers are omitted.
""")

