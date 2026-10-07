"""Calculations behind the Builders tab.

Input: the cleaned tables from loading.py. Output: small summary tables that
views.py turns into charts. Nothing here draws or reads files.
"""

import numpy as np
import pandas as pd

from .loading import PARENT_ORG, country_group, split_list


def org_credit(models, weight=None):
    """One row per (model, parent organisation).

    A model built by several organisations is split equally between them
    (fractional counting), so a model is never counted more than once.
    If `weight` names a column (e.g. training compute), each organisation's
    share of that model's value is used instead of a count of 1.
    """
    rows = models[["Model", "year", "parents", "Organization",
                   "Country (of organization)"]
                  + ([weight] if weight else [])].copy()
    rows["countries"] = rows["Country (of organization)"].map(split_list)
    rows["org_country"] = rows.apply(_org_countries, axis=1)
    rows = rows.explode("org_country").dropna(subset=["org_country"])
    rows["parent"] = rows["org_country"].str[0]
    rows["country"] = rows["org_country"].str[1]
    rows["n_parents"] = rows.groupby(level=0)["parent"].transform("size")
    base = rows[weight] if weight else 1.0
    rows["credit"] = base / rows["n_parents"]
    return rows[["Model", "year", "parent", "country", "credit"]]


def _org_countries(row):
    """Pair each parent organisation with its country.

    Epoch lists one country per organisation, in the same order, so the two
    lists are zipped together before the organisations are merged into parents.
    """
    orgs = split_list(row["Organization"])
    countries = row["countries"]
    if len(countries) != len(orgs):
        countries = (countries or ["Unknown"]) * len(orgs)
        countries = countries[:len(orgs)]
    seen = {}
    for org, country in zip(orgs, countries):
        parent = PARENT_ORG.get(org, org)
        seen.setdefault(parent, country)
    return [(p, c) for p, c in seen.items()] or None


def org_countries(credit):
    """Most common country for each parent organisation, grouped into 3 bins."""
    home = (credit.groupby("parent")["country"]
            .agg(lambda s: s.value_counts().index[0]))
    return home.map(country_group)


def ranking(credit, start, end):
    """Each lab's share of the total over a period, largest first."""
    tot = credit[credit["year"].between(start, end)].groupby("parent")["credit"].sum()
    return (tot / tot.sum()).sort_values(ascending=False)


def cost_trend(frontier):
    """Log-linear fit of frontier training cost against publication date.

    Returns the growth multiple per year and the fitted line for plotting.
    """
    known = frontier.dropna(subset=["cost_usd"])
    known = known[known["cost_usd"] > 0]
    t = known["date"].dt.year + (known["date"].dt.dayofyear - 1) / 365.25
    slope, intercept = np.polyfit(t, np.log10(known["cost_usd"]), 1)
    grid = np.linspace(t.min(), t.max(), 50)
    line = pd.DataFrame({
        "date": pd.to_datetime((grid - 1970) * 365.25, unit="D", origin="unix"),
        "cost_usd": 10 ** (intercept + slope * grid),
    })
    return 10 ** slope, line, len(known)
