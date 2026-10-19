"""Read and clean the Epoch AI 'Data on AI chip sales' file.

Every number in this tab comes from one CSV in data/raw/epoch_ai_chip_sales/
(downloaded from https://epoch.ai/data/ai-chip-sales):

    timelines_by_chip.csv  quarterly shipments of each AI chip, with an
                           estimated cost per chip and total cost

Cleaning only happens here. Calculations are in analysis.py, charts in views.py.
"""

from pathlib import Path

import pandas as pd

DATA_FILE = (Path(__file__).resolve().parents[1]
             / "data" / "raw" / "epoch_ai_chip_sales" / "timelines_by_chip.csv")
DOWNLOADED = "13 October 2026"


def load_chip_sales():
    """One row per chip type per quarter.

    Columns: chip, maker (the chip designer), date (the last day of the
    quarter), year, units shipped and spend in US dollars.

    Spend is Epoch's "Cost Estimate (USD)", which is units shipped x an
    approximate cost per chip. Some chips have no cost estimate in the file, so
    their spend is 0 here. That means "unknown", not "free".
    """
    df = pd.read_csv(DATA_FILE)

    df["date"] = pd.to_datetime(df["End date"])
    df["year"] = df["date"].dt.year
    df["chip"] = df["Chip type"]
    df["maker"] = df["Chip manufacturer"]
    df["units"] = df["Number of Units"]
    df["spend"] = df["Cost Estimate (USD)"]

    return df[["chip", "maker", "date", "year", "units", "spend"]]
