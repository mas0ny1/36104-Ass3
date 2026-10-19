"""Charts and page layout for the Capital tab.

Data: Epoch AI, 'Data on AI chip sales' (CC-BY). Cleaning is in loading.py and
calculations are in analysis.py. The download record is in this folder's README.

The page has three questions, each with one chart:
    1. How big is the bill, and who is paid?   (stacked bars by designer)
    2. Is the money moving to newer chips?     (heat map of chips by year)
    3. Which chips take the money?             (bar chart of the top chips)

One filter row (years and chip designers) sits under question 1 and applies to
all three charts. The cards at the top and the summary at the bottom do not use
the filters: they always use all chips, from the first year to the latest full year.
"""

import altair as alt
import streamlit as st

from core.theme import colours

from . import analysis, loading

# ---- Settings you may want to change ---------------------------------------
BILLION = 1e9
TOP_CHIPS_SHOWN = 15         # question 3: number of chips in the bar chart
HEAT_MAP_CHIPS = 12          # question 2: number of chips in the heat map
SPEND_CHART_HEIGHT = 480     # question 1: chart height in pixels
HEAT_MAP_ROW_HEIGHT = 30     # question 2: pixels per chip row
TOP_CHIPS_ROW_HEIGHT = 22    # question 3: pixels per chip row
MIN_LABEL_SHARE = 0.03       # share view: no % label on slices thinner than 3%

# The shared theme (core/theme.py) has three colours. Nvidia, Google and AMD use those.
# Huawei and Amazon get two more, set here, so every designer has its own colour.
EXTRA_COLOURS_LIGHT = {"Huawei": "#7b4fd0", "Amazon": "#b8860b"}
EXTRA_COLOURS_DARK = {"Huawei": "#a67cf0", "Amazon": "#e3b83a"}

# Epoch's note on these two chips (from its chip_types.csv file).
B200_NOTE = ("Epoch notes that most B200 and B300 chips shipped inside GB200 and GB300 "
             "systems, so it uses the GB200 and GB300 specifications to estimate their cost.")


@st.cache_data
def load_data():
    return loading.load_chip_sales()


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def esc(text):
    """Escape dollar signs. Streamlit reads two '$' in one text as a maths formula."""
    return text.replace("$", r"\$")


def money(dollars):
    """US dollars as billions: one decimal under $100B (so $10.5B is not shown as $11B), none above."""
    billions = dollars / BILLION
    if billions < 100:
        return f"${billions:,.1f}B"
    return f"${billions:,.0f}B"


def join_names(names):
    """['a', 'b', 'c'] becomes 'a, b and c'."""
    names = list(names)
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def money_and_share(dollars, share):
    """'$64B (34%)': the amount and its share, so the text matches the numbers in the charts."""
    return f"{money(dollars)} ({share:.0%})"


def latest_full_year(chips):
    """The last year that has all four quarters in the data."""
    last_date = chips["date"].max()
    if last_date.month == 12:
        return last_date.year
    return last_date.year - 1


def designer_colours(c, designers):
    """One colour per chip designer, in the same order as the `designers` list."""
    colour_of = {"Nvidia": c["series"][0], "Google": c["series"][1], "AMD": c["series"][2]}
    if c["surface"] == "#ffffff":
        colour_of.update(EXTRA_COLOURS_LIGHT)
    else:
        colour_of.update(EXTRA_COLOURS_DARK)
    # A designer without a colour of its own (none today) falls back to grey.
    colours_in_order = [colour_of.get(name, c["other"]) for name in designers]
    return alt.Scale(domain=designers, range=colours_in_order)


def top_legend():
    return alt.Legend(orient="top", direction="horizontal", labelLimit=0)


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------

def filter_row(chips, designers):
    """Show the years slider and the designer box.

    Returns (first year, last year, rows) or None if nothing is left to draw.
    """
    first_data_year = int(chips["year"].min())
    last_data_year = int(chips["year"].max())

    col_years, col_makers = st.columns([1, 2])
    first_year, last_year = col_years.slider(
        "Years", first_data_year, last_data_year, (first_data_year, last_data_year),
        key="capital_years")
    chosen_makers = col_makers.multiselect(
        "Chip designers", designers, default=designers, key="capital_designers")

    # One year alone has nothing to compare with, so widen it to two years.
    widened = first_year == last_year
    if widened and last_year < last_data_year:
        last_year = last_year + 1
    elif widened:
        first_year = first_year - 1

    if not chosen_makers:
        st.warning("Select at least one chip designer.")
        return None

    rows = analysis.filter_chips(chips, (first_year, last_year), chosen_makers)
    if rows["spend"].sum() == 0:
        st.warning("None of the chips in this selection have a cost estimate. "
                   "Widen the years or add designers.")
        return None

    # A line under the filters saying what is selected.
    parts = [f"{first_year}–{last_year}"]
    if widened:
        parts[0] += " (a range needs two years)"
    if len(chosen_makers) == len(designers):
        parts.append("all designers")
    else:
        parts.append(join_names(chosen_makers))
    last_date = chips["date"].max()
    if last_year == last_date.year and last_date.month < 12:
        parts.append(f"{last_year} is a partial year (January–{last_date.strftime('%B')})")
    st.caption(esc(":material/filter_alt: Filters apply to all three charts: " + " · ".join(parts)))

    return first_year, last_year, rows


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def designer_chart(table, show_share, designers, c):
    """Question 1: bars for each year, split by designer, in dollars or as a share."""
    d = table.copy()
    d["order"] = d["maker"].map(designers.index)
    d = d.sort_values(["year", "order"])

    # Work out where each slice starts and ends so we can put labels in the middle.
    if show_share:
        d["value"] = d["share"]
    else:
        d["value"] = d["spend"] / BILLION
    d["end"] = d.groupby("year")["value"].cumsum()
    d["start"] = d["end"] - d["value"]
    d["middle"] = (d["start"] + d["end"]) / 2

    if show_share:
        y_title = "Share of the year's chip value shipped"
        y_format = "%"
        y_top = 1
        tooltip_value = alt.Tooltip("value:Q", title="Share of the year", format=".0%")
    else:
        y_title = "Estimated value of chips shipped (US$ billions)"
        y_format = "$,.0f"
        y_top = max(d["end"].max(), 1e-9) * 1.1      # leave room for the total above each bar
        tooltip_value = alt.Tooltip("value:Q", title="US$ billions", format=",.1f")

    x = alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0))
    bars = alt.Chart(d).mark_bar(stroke=c["surface"], strokeWidth=1.5).encode(
        x=x,
        y=alt.Y("start:Q", title=y_title, scale=alt.Scale(domain=[0, y_top]),
                axis=alt.Axis(format=y_format, tickCount=6)),
        y2="end:Q",
        color=alt.Color("maker:N", title=None, scale=designer_colours(c, designers),
                        legend=top_legend()),
        tooltip=[alt.Tooltip("year:O", title="Year"),
                 alt.Tooltip("maker:N", title="Designer"),
                 tooltip_value])

    if show_share:
        # A % label inside each slice that is thick enough to hold it.
        d["label"] = ""
        thick = d["value"] >= MIN_LABEL_SHARE
        d.loc[thick, "label"] = (d.loc[thick, "value"] * 100).round().astype(int).astype(str) + "%"
        labels = alt.Chart(d).mark_text(fontSize=10, fontWeight="bold", color=c["surface"]).encode(
            x=x, y="middle:Q", text="label:N")
    else:
        # The year's total above each bar.
        totals = d.groupby("year", as_index=False)["end"].max()
        totals["label"] = [money(v * BILLION) for v in totals["end"]]
        labels = alt.Chart(totals).mark_text(dy=-8, fontSize=11, color=c["muted"]).encode(
            x=x, y="end:Q", text="label:N")

    return (bars + labels).properties(height=SPEND_CHART_HEIGHT)


def heat_map(table, chip_order, c):
    """Question 2: one row per chip (oldest at the top), one column per year."""
    d = table.copy()
    d["value"] = d["spend"] / BILLION
    d["label"] = [money(v * BILLION) if v >= 0.05 else "" for v in d["value"]]
    biggest = max(d["value"].max(), 1e-9)

    x = alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0, orient="top"))
    y = alt.Y("chip:N", sort=chip_order, title=None,
              axis=alt.Axis(labelLimit=250, labelOverlap=False))

    # Darker blue = more spending.
    colour_scale = alt.Scale(domain=[0, biggest], range=[c["surface"], c["series"][0]],
                             interpolate="rgb")
    cells = alt.Chart(d).mark_rect(stroke=c["surface"], strokeWidth=2).encode(
        x=x, y=y,
        color=alt.Color("value:Q", legend=None, scale=colour_scale),
        tooltip=[alt.Tooltip("chip:N", title="Chip"),
                 alt.Tooltip("maker:N", title="Designer"),
                 alt.Tooltip("year:O", title="Year"),
                 alt.Tooltip("value:Q", title="US$ billions", format=",.1f")])

    # White text on dark cells, grey text on light cells.
    light_theme = c["surface"] == "#ffffff"
    white_from = biggest * (0.75 if light_theme else 0.5)
    text = alt.Chart(d).mark_text(fontSize=11).encode(
        x=x, y=y, text="label:N",
        color=alt.condition(alt.datum.value > white_from, alt.value("#ffffff"), alt.value(c["muted"])))

    return (cells + text).properties(height=alt.Step(HEAT_MAP_ROW_HEIGHT))


def top_chips_chart(top, designers, c):
    """Question 3: horizontal bars for the chips with the most spend."""
    d = top.copy()
    d["billions"] = d["spend"] / BILLION
    d["label"] = [f"{money(spend)} · {share:.0%}" for spend, share in zip(d["spend"], d["share"])]

    y = alt.Y("chip:N", sort=d["chip"].tolist(), title=None,
              axis=alt.Axis(labelLimit=250, labelOverlap=False))
    bars = alt.Chart(d).mark_bar(cornerRadiusEnd=4, size=15).encode(
        x=alt.X("billions:Q", title="Estimated value of chips shipped in the selected years (US$ billions)",
                axis=alt.Axis(format="$,.0f", tickCount=6)),
        y=y,
        color=alt.Color("maker:N", title=None, scale=designer_colours(c, designers),
                        legend=top_legend()),
        tooltip=[alt.Tooltip("chip:N", title="Chip"),
                 alt.Tooltip("maker:N", title="Designer"),
                 alt.Tooltip("label:N", title="Total · share")])
    labels = alt.Chart(d).mark_text(align="left", dx=4, fontSize=11, color=c["muted"]).encode(
        x="billions:Q", y=y, text="label:N")

    return (bars + labels).properties(height=alt.Step(TOP_CHIPS_ROW_HEIGHT))


# --------------------------------------------------------------------------
# The three questions: text, chart and caption for each
# --------------------------------------------------------------------------

def question_1(rows, first_year, last_year, c, designers, no_cost_designers):
    """How big is the bill, and who is paid?"""
    view = st.segmented_control("Show", ["US$ value", "Share of total"], default="US$ value",
                                required=True, key="capital_metric",
                                label_visibility="collapsed")
    table = analysis.spend_by_designer(rows, (first_year, last_year), designers)

    # One or two sentences above the chart.
    total_first = analysis.year_total(rows, first_year)
    total_last = analysis.year_total(rows, last_year)
    if total_first > 0:
        text = (f"The estimated value of AI chips shipped went from {money(total_first)} in {first_year} "
                f"to **{money(total_last)} in {last_year}**.")
    else:
        text = f"The estimated value of AI chips shipped was **{money(total_last)} in {last_year}**."

    leader, share_last = analysis.biggest_designer(rows, last_year)
    designers_in_last_year = rows.loc[rows["year"] == last_year, "maker"].nunique()
    if leader and designers_in_last_year > 1:
        text += (f" {leader} took **{money_and_share(share_last * total_last, share_last)}** "
                 f"of the {last_year} total")
        share_first = analysis.designer_share(rows, first_year, leader)
        if share_first > 0:
            text += (f", compared with {money_and_share(share_first * total_first, share_first)} "
                     f"in {first_year}")
        text += "."
    st.markdown(esc(text))

    # Designers with no cost estimate at all cannot be drawn, so say so.
    not_shown = ""
    if no_cost_designers:
        not_shown = f"Not shown (no cost estimate in the data): {join_names(no_cost_designers)}. "
    st.altair_chart(designer_chart(table, view == "Share of total", designers, c), width="stretch",
                    alt="Stacked bar chart of the estimated value of AI chips shipped each year, "
                        "split by chip designer, in dollars or as a share.")

    st.caption(esc(
        "Value = estimated chips shipped × Epoch's approximate cost per chip. The file does not say "
        "whether that is the price a buyer paid or the cost of making the chip, so read it as Epoch's "
        "estimated value of the chips. Each chip designer has its own colour. Chips with no cost estimate count as $0. "
        + not_shown + "In the share view, slices under 3% have no label."))


def question_2(rows, first_year, last_year, c):
    """Is the money moving to newer chips?"""
    st.subheader("2. Is the money moving to newer chips?")

    chip_first, spend_first, share_first = analysis.top_chip_of_year(rows, first_year)
    chip_last, spend_last, share_last = analysis.top_chip_of_year(rows, last_year)
    if chip_first and chip_last:
        text = (f"In {first_year} the most money went to **{chip_first}** "
                f"({money(spend_first)}, {share_first:.0%} of the year). ")
        if chip_first == chip_last:
            text += f"In {last_year} it still went to **{chip_last}** "
        else:
            text += f"In {last_year} it went to **{chip_last}** "
        text += f"({money(spend_last)}, {share_last:.0%} of the year)."
        st.markdown(esc(text))

    table, chip_order = analysis.spend_by_chip_year(rows, (first_year, last_year), HEAT_MAP_CHIPS)
    st.altair_chart(heat_map(table, chip_order, c), width="stretch",
                    alt="Heat map of the value of each of the top AI chips shipped by year, oldest chip first.")
    st.caption(esc(
        f"The {HEAT_MAP_CHIPS} chips with the most value shipped in the selected years, listed from oldest "
        "to newest (by when most of their value was shipped). A darker cell means more money. "
        "Same measure as question 1: chips shipped × Epoch's approximate cost per chip, split by chip. "
        + B200_NOTE))


def question_3(rows, first_year, last_year, c, designers):
    """Which chips take the money?"""
    st.subheader("3. Which chips take the money?")
    groups = st.pills("Designer", designers, selection_mode="multi",
                      default=designers, key="capital_chip_groups")

    rows = rows[rows["maker"].isin(groups)]
    if rows["spend"].sum() == 0:
        if not groups:
            st.info("Pick at least one designer above.")
        else:
            st.info("None of the chips from the selected designers have a cost estimate. "
                    "Pick another designer above or widen the filters under question 1.")
        return

    top = analysis.top_chips(rows, TOP_CHIPS_SHOWN)
    top3 = top.head(3)

    if len(groups) == len(designers):
        what = "the value of all chips shipped"
    else:
        what = "the value of chips shipped by the selected designers"
    text = (f"From {first_year} to {last_year}, the top {len(top3)} chips took "
            f"**{money_and_share(top3['spend'].sum(), top3['share'].sum())}** of {what}: "
            f"{join_names(top3['chip'])}")
    top3_makers = top3["maker"].unique()
    if len(top3_makers) == 1 and len(top3) > 1:
        text += f" (all {top3_makers[0]})"
    st.markdown(esc(text + "."))

    st.altair_chart(top_chips_chart(top, designers, c), width="stretch",
                    alt=f"Bar chart of the {len(top)} AI chips with the highest value shipped.")
    st.caption(B200_NOTE)


# --------------------------------------------------------------------------
# Cards, summary and methods (always use all chips, no filters)
# --------------------------------------------------------------------------

def headline_facts(chips):
    """The numbers for the cards and the summary: first year to the latest full year."""
    first = int(chips["year"].min())
    last = latest_full_year(chips)
    full = chips[chips["year"] <= last]

    facts = {
        "first": first,
        "last": last,
        "total_first": analysis.year_total(full, first),
        "total_last": analysis.year_total(full, last),
        "nvidia_first": analysis.designer_share(full, first),
        "nvidia_last": analysis.designer_share(full, last),
        "next_designers": analysis.next_designers(full, last),
        "top3_chips": analysis.top_chips(full, 3),
        "newest2_chips": analysis.top_chips(full[full["year"] == last], 2),
    }
    facts["nvidia_first_spend"] = facts["nvidia_first"] * facts["total_first"]
    facts["nvidia_last_spend"] = facts["nvidia_last"] * facts["total_last"]
    facts["chip_first"], _, facts["chip_first_share"] = analysis.top_chip_of_year(full, first)
    facts["chip_last"], facts["chip_last_spend"], facts["chip_last_share"] = \
        analysis.top_chip_of_year(full, last)

    # The biggest chip of every year, e.g. "A100 in 2022, H100/H200 in 2023 ..."
    each_year = []
    for year in range(first, last + 1):
        chip, _, _ = analysis.top_chip_of_year(full, year)
        each_year.append(f"{chip} in {year}")
    facts["chip_each_year"] = join_names(each_year)

    # A partial year after the last full one (for example January to September).
    last_date = chips["date"].max()
    facts["partial_year"] = last_date.year if last_date.year > last else None
    facts["partial_months"] = last_date.month
    facts["partial_month_name"] = last_date.strftime("%B")
    facts["total_partial"] = analysis.year_total(chips, last_date.year)
    return facts


def show_cards(f):
    cards = [
        (f"Estimated value of AI chips shipped, {f['last']}", money(f["total_last"]),
         f"{f['total_last'] / f['total_first']:.0f}× the {money(f['total_first'])} of {f['first']}"),
        (f"Estimated value of Nvidia chips shipped, {f['last']}", money(f["nvidia_last_spend"]),
         f"{f['nvidia_last']:.0%} of the year's total ({f['nvidia_first']:.0%} in {f['first']})"),
        (f"Biggest chip, {f['last']}", f["chip_last"],
         f"{money(f['chip_last_spend'])}, {f['chip_last_share']:.0%} of the year's total"),
    ]
    if f["partial_year"]:
        cards.append((f"{f['partial_year']} so far (to {f['partial_month_name']})",
                      money(f["total_partial"]),
                      f"{f['total_partial'] / f['total_last']:.0%} of the {money(f['total_last'])} "
                      f"for all of {f['last']}"))

    columns = st.columns(len(cards), border=True)
    for column, (label, value, note) in zip(columns, cards):
        column.metric(label, value, note, delta_color="off", delta_arrow="off")


def show_summary(f):
    first, last = f["first"], f["last"]
    with st.container(border=True):
        st.markdown(f"#### Summary (all chips, {first}–{last})")

        next_two = [f"{maker} ({money(share * f['total_last'])}, {share:.0%})"
                    for maker, share in f["next_designers"]]
        newest2 = f["newest2_chips"]
        top3 = f["top3_chips"]

        bullets = [
            f"**Bill and who is paid:** about **{money(f['total_last'])} in {last}**, up from "
            f"{money(f['total_first'])} in {first} ({f['total_last'] / f['total_first']:.0f} times as much). "
            f"Nvidia took **{money_and_share(f['nvidia_last_spend'], f['nvidia_last'])}**, compared with "
            f"{money_and_share(f['nvidia_first_spend'], f['nvidia_first'])} in {first}. "
            f"Next biggest: {join_names(next_two)}.",

            f"**Newer chips:** the biggest chip each year was {f['chip_each_year']}. "
            f"In {last}, {join_names(newest2['chip'])} together took "
            f"{money_and_share(newest2['spend'].sum(), newest2['share'].sum())}.",

            f"**Which chips:** {join_names(top3['chip'])} took "
            f"{money_and_share(top3['spend'].sum(), top3['share'].sum())} of the value shipped from {first} to {last}.",
        ]
        if f["partial_year"]:
            bullets.append(
                f"**{f['partial_year']} so far:** about {money(f['total_partial'])} from January to "
                f"{f['partial_month_name']}, which is {f['total_partial'] / f['total_last']:.0%} of the "
                f"{money(f['total_last'])} for the whole of {last}, reached in {12 - f['partial_months']} "
                f"fewer months.")

        bullet_list = ""
        for line in bullets:
            bullet_list += "- " + line + "\n"
        st.markdown(esc(bullet_list))
        st.markdown(esc("These are Epoch's cost estimates for the chips shipped, so they show which "
                        "designers' chips the money is attached to, not who bought them. The file does not "
                        "say whether a figure is a price paid or a cost to make."))


def show_methods(chips):
    no_cost = analysis.chips_without_cost(chips)
    units_share = analysis.units_share_without_cost(chips)
    last_date = chips["date"].max()

    with st.expander("Data and methods:"):
        st.markdown(esc(f"""
**Source:** Epoch AI, *Data on AI chip sales* (CC-BY 4.0), downloaded
{loading.DOWNLOADED} from <https://epoch.ai/data/ai-chip-sales>
(`timelines_by_chip.csv`). Cleaning is in `src/loading.py` and calculations in
`src/analysis.py`.

- **Value shipped** ("spend" in the code) is Epoch's *Cost Estimate* column (units shipped ×
  approximate cost per chip), added up by the year each quarter ends. The file does not say whether
  this is the price a buyer paid or the cost of making the chip.
  Every chip designer is shown separately. A designer whose chips have no cost estimate at all
  is left out of the charts and the filters.
- **Question 2** keeps the {HEAT_MAP_CHIPS} chips with the most value shipped in the selected years and lists
  them from oldest to newest by the average year of their shipments.
- **Question 3** adds up value shipped per chip over the selected years and keeps the top {TOP_CHIPS_SHOWN}.
  The bar length is dollars; the label shows dollars and share.
- **Filters** (years, chip designers) apply to all three charts. The cards and the summary
  always use all chips for the first year to the latest full year.

**Known limits:**
- Costs are Epoch's estimates. Epoch also gives lower and upper unit estimates (5th and 95th
  percentile); this tab uses the main estimate only.
- {len(no_cost)} chips have no cost estimate ({join_names(no_cost)}). They are about
  {units_share:.0%} of all chips shipped and count as $0.
- Some costs come from outside reports. Epoch's notes say the Huawei Ascend 910B and 910C
  costs are based on press reports of selling prices and order values (Epoch rounds them to $15k
  and $20k per chip), and that the Trainium2 cost is about $4k per chip according to SemiAnalysis. {B200_NOTE}
- Epoch flags the latest quarter as incomplete for several chips, and {last_date.year} only covers
  January to {last_date.strftime('%B')}.
- The file lists chips shipped by designer. It has no column for who bought them, so it cannot
  say how much any one company spent.
"""))


# --------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------

def render():
    c = colours()
    chips = load_data()
    designers = analysis.designers_with_spend(chips)
    no_cost_designers = analysis.designers_without_spend(chips)
    facts = headline_facts(chips)

    last_date = chips["date"].max()
    st.markdown(
        "This tab uses Epoch AI's estimates of how many AI chips were shipped each quarter "
        f"({int(chips['year'].min())} to {last_date.strftime('%B %Y')}) and Epoch's cost estimate for those chips. "
        "It asks **how big the bill is and who is paid**, **whether the money is moving to "
        "newer chips** and **which chips take the money**.")

    show_cards(facts)

    # Question 1 comes first, and the shared filters sit right under its heading.
    st.subheader("1. How big is the bill, and who is paid?")
    selection = filter_row(chips, designers)
    if selection:
        first_year, last_year, rows = selection
        question_1(rows, first_year, last_year, c, designers, no_cost_designers)
        question_2(rows, first_year, last_year, c)
        question_3(rows, first_year, last_year, c, designers)

    show_summary(facts)
    show_methods(chips)
