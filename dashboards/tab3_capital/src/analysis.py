"""Calculations behind the Capital tab.

Input: the cleaned chip table from loading.py (one row per chip per quarter).
Output: small numbers and tables that views.py turns into text and charts.
Nothing in this file draws anything or reads files.
"""

import pandas as pd


# --------------------------------------------------------------------------
# Picking rows
# --------------------------------------------------------------------------

def filter_chips(chips, years, makers):
    """Rows from the chosen years (first, last) and the chosen chip designers."""
    first_year, last_year = years
    in_years = chips["year"].between(first_year, last_year)
    from_makers = chips["maker"].isin(makers)
    return chips[in_years & from_makers]


def designers_with_spend(chips):
    """Chip designers that have a cost estimate in the data, biggest total spend first."""
    totals = chips.groupby("maker")["spend"].sum().sort_values(ascending=False)
    return totals[totals > 0].index.tolist()


def designers_without_spend(chips):
    """Chip designers with no cost estimate at all in the data (their spend is 0)."""
    totals = chips.groupby("maker")["spend"].sum()
    return sorted(totals[totals == 0].index)


# --------------------------------------------------------------------------
# Totals and shares
# --------------------------------------------------------------------------

def year_total(chips, year):
    """Total spend in one year."""
    return chips.loc[chips["year"] == year, "spend"].sum()


def designer_share(chips, year, maker="Nvidia"):
    """One designer's share (0 to 1) of the spend in a year."""
    total = year_total(chips, year)
    if total == 0:
        return 0.0
    maker_spend = chips.loc[(chips["year"] == year) & (chips["maker"] == maker), "spend"].sum()
    return maker_spend / total


def biggest_designer(chips, year):
    """The designer with the most spend in a year, and its share of that year."""
    by_maker = chips[chips["year"] == year].groupby("maker")["spend"].sum()
    if by_maker.sum() == 0:
        return None, 0.0
    return by_maker.idxmax(), by_maker.max() / by_maker.sum()


def next_designers(chips, year, skip="Nvidia", n=2):
    """The `n` biggest designers after `skip`, as a list of (designer, share of the year)."""
    total = year_total(chips, year)
    rows = chips[(chips["year"] == year) & (chips["maker"] != skip)]
    by_maker = rows.groupby("maker")["spend"].sum().sort_values(ascending=False).head(n)
    return [(maker, spend / total) for maker, spend in by_maker.items()]


def spend_by_designer(chips, years, designers):
    """Spend per year for each chip designer in `designers`.

    Every designer appears in every year, even with 0 spend. `share` is the
    designer's part (0 to 1) of that year's spend.
    """
    spend = chips.groupby(["year", "maker"])["spend"].sum()
    every_row = pd.MultiIndex.from_product(
        [range(years[0], years[1] + 1), designers], names=["year", "maker"])
    table = spend.reindex(every_row, fill_value=0).reset_index()

    year_totals = table.groupby("year")["spend"].transform("sum")
    table["share"] = 0.0
    has_spend = year_totals > 0
    table.loc[has_spend, "share"] = table["spend"] / year_totals
    return table


# --------------------------------------------------------------------------
# Chips
# --------------------------------------------------------------------------

def top_chips(chips, n):
    """The `n` chips with the most spend, each with its share of all the spend given."""
    total = chips["spend"].sum()
    by_chip = chips.groupby(["chip", "maker"])["spend"].sum().reset_index()
    top = by_chip.sort_values("spend", ascending=False).head(n).reset_index(drop=True)
    top["share"] = top["spend"] / total if total > 0 else 0.0
    return top


def top_chip_of_year(chips, year):
    """The chip with the most spend in a year: (chip, its spend, its share of that year)."""
    by_chip = chips[chips["year"] == year].groupby("chip")["spend"].sum()
    if by_chip.sum() == 0:
        return None, 0.0, 0.0
    return by_chip.idxmax(), by_chip.max(), by_chip.max() / by_chip.sum()


def spend_by_chip_year(chips, years, n):
    """Spend per year for the `n` biggest chips (one row per chip per year).

    Returns (table, order). `order` lists the chips from oldest to newest, using
    the average year of each chip's spending (weighted by the dollars), so a
    chart reads top to bottom as the money moves from one chip to the next.
    """
    top = top_chips(chips, n)
    names = top["chip"].tolist()

    spend = chips[chips["chip"].isin(names)].groupby(["chip", "year"])["spend"].sum()
    every_row = pd.MultiIndex.from_product(
        [names, range(years[0], years[1] + 1)], names=["chip", "year"])
    table = spend.reindex(every_row, fill_value=0).reset_index()
    table = table.merge(top[["chip", "maker"]], on="chip")

    average_year = {}
    for name in names:
        rows = table[table["chip"] == name]
        if rows["spend"].sum() > 0:
            average_year[name] = (rows["spend"] * rows["year"]).sum() / rows["spend"].sum()
        else:
            average_year[name] = years[1] + 1   # no cost estimate: list it last
    order = sorted(names, key=lambda name: average_year[name])
    return table, order


# --------------------------------------------------------------------------
# Data quality
# --------------------------------------------------------------------------

def chips_without_cost(chips):
    """Names of chips that have no cost estimate in any quarter."""
    by_chip = chips.groupby("chip")["spend"].sum()
    return sorted(by_chip[by_chip == 0].index)


def units_share_without_cost(chips):
    """Share (0 to 1) of all chips shipped that belong to chips with no cost estimate."""
    no_cost = chips_without_cost(chips)
    return chips.loc[chips["chip"].isin(no_cost), "units"].sum() / chips["units"].sum()
