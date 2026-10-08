"""Analytical calculations for Tab 2: Compute Infrastructure.

Input: Cleaned DataFrames from loading.py.
Output: Summary tables, concentration indices (CR4, CR8, HHI), regional
breakdowns, chip sales timelines, and power ranking tables for views.py.
Nothing in this module draws or reads raw files directly.
"""

import numpy as np
import pandas as pd

from .loading import COUNTRY_GROUPS


def calculate_concentration_stats(df, end_year=2025):
    """Compute overall compute concentration metrics and regional breakdowns."""
    d = df[df["year"].fillna(end_year) <= end_year].copy()
    total_clusters = len(d)
    total_h100 = d["h100_equiv"].sum()
    total_power = d["power_mw"].dropna().sum()

    if total_h100 <= 0:
        return {
            "total_clusters": 0,
            "total_h100": 0.0,
            "total_power": 0.0,
            "cr4": 0.0,
            "cr8": 0.0,
            "hhi": 0.0,
            "us_share": 0.0,
            "china_share": 0.0,
            "europe_share": 0.0,
            "row_share": 0.0,
        }

    parent_totals = d.groupby("parent")["h100_equiv"].sum().sort_values(ascending=False)
    shares = parent_totals / total_h100
    shares_pct = shares * 100.0

    cr4 = float(shares.head(4).sum())
    cr8 = float(shares.head(8).sum())
    hhi = float((shares_pct ** 2).sum())

    country_totals = d.groupby("country_group")["h100_equiv"].sum()
    c_shares = (country_totals / total_h100).to_dict()

    return {
        "total_clusters": total_clusters,
        "total_h100": total_h100,
        "total_power": total_power,
        "cr4": cr4,
        "cr8": cr8,
        "hhi": hhi,
        "us_share": c_shares.get("United States", 0.0),
        "china_share": c_shares.get("China", 0.0),
        "europe_share": c_shares.get("Europe", 0.0),
        "row_share": c_shares.get("Rest of world", 0.0),
    }


def owner_ranking_table(df, end_year=2025, n=12):
    """Aggregate total compute and cluster counts by parent organization up to end_year."""
    d = df[df["year"].fillna(end_year) <= end_year].copy()
    if d.empty or d["h100_equiv"].sum() <= 0:
        return pd.DataFrame(columns=["parent", "country_group", "h100_equiv", "share"])

    total = d["h100_equiv"].sum()
    grouped = (
        d.groupby("parent")
        .agg(
            h100_equiv=("h100_equiv", "sum"),
            clusters=("Name", "count"),
            country_group=("country_group", lambda s: s.mode()[0] if not s.empty else "Rest of world"),
        )
        .reset_index()
    )
    grouped["share"] = grouped["h100_equiv"] / total
    return grouped.sort_values(by="h100_equiv", ascending=False).head(n)


def country_share_table(df, end_year=2025):
    """Summarize compute share and cluster count by geopolitical country group up to end_year."""
    d = df[df["year"].fillna(end_year) <= end_year].copy()
    if d.empty or d["h100_equiv"].sum() <= 0:
        return pd.DataFrame(columns=["country_group", "h100_equiv", "share", "clusters"])

    total = d["h100_equiv"].sum()
    summary = (
        d.groupby("country_group")
        .agg(
            h100_equiv=("h100_equiv", "sum"),
            clusters=("Name", "count"),
        )
        .reindex(COUNTRY_GROUPS)
        .fillna(0.0)
        .reset_index()
    )
    summary["share"] = summary["h100_equiv"] / total if total > 0 else 0.0
    return summary


def chip_share_timeline(chips_df):
    """Prepare quarterly delivered compute shares for 100% stacked area visualization."""
    if chips_df.empty:
        return pd.DataFrame()

    df = chips_df.copy()
    # Compute quarterly total to get share
    quarterly_totals = df.groupby("date")["cumulative_h100"].transform("sum")
    df["share"] = df["cumulative_h100"] / quarterly_totals
    return df


def top_power_clusters(df, end_year=2025, n=10):
    """Identify top distinct AI supercomputing installations by dedicated power demand (MW)."""
    d = df[df["year"].fillna(end_year) <= end_year].copy()
    # Filter out superseded phases so each physical supercomputer appears once
    if "Superseded by" in d.columns:
        d = d[d["Superseded by"].isna()].copy()

    valid = d.dropna(subset=["power_mw"]).copy()
    valid = valid[valid["power_mw"] > 0].copy()

    if valid.empty:
        return pd.DataFrame()

    top = valid.sort_values(by="power_mw", ascending=False).head(n).copy()
    # Equivalent households powered (approx. 800 homes per MW)
    top["homes_equivalent"] = top["power_mw"] * 800.0
    return top[
        [
            "Name",
            "parent",
            "country_group",
            "Country",
            "year",
            "power_mw",
            "h100_equiv",
            "homes_equivalent",
        ]
    ]


def chip_designer_shares(chip_sales_df):
    """Calculate the latest delivered compute share per chip designer."""
    if chip_sales_df.empty:
        return {}
    latest_date = chip_sales_df["date"].max()
    latest_df = chip_sales_df[chip_sales_df["date"] == latest_date]
    total_compute = latest_df["cumulative_h100"].sum()
    if total_compute <= 0:
        return {}
    return (latest_df.set_index("designer")["cumulative_h100"] / total_compute).to_dict()
