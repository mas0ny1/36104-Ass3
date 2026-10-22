"""Read and clean the Epoch AI 'Capabilities & benchmarking' files.

Every number in this tab comes from one of four CSVs in
data/raw/epoch_capabilities/ (downloaded from https://epoch.ai/benchmarks):

    eci_scores.csv              one Epoch Capabilities Index (ECI) score per model
    processed_data_for_eci.csv  every (model, benchmark) score used to build the ECI
    benchmark_metadata.csv      benchmark release date, random baseline and ceiling
    model_metadata.csv          training compute (FLOP) for some models

Cleaning only happens here; calculations are in analysis.py and charts in views.py.
"""

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw" / "epoch_capabilities"
DOWNLOADED = "18 October 2026"

# Epoch lists some labs under several names. Merge them into one parent so a lab
# is counted once. The names match Tab 1 (Google DeepMind and Google -> Google).
PARENT_ORG = {
    "Google DeepMind": "Google", "Google": "Google",
    "Meta AI": "Meta",
    "Microsoft Research": "Microsoft",
    "Z.ai (Zhipu AI)": "Zhipu AI",
}

ACCESS = ["Open weights", "Closed weights"]


def _key(name):
    """Lower-case letters and digits only, so 'GPT-5 (high)' matches 'gpt5high'."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def lead_lab(organization):
    """The first organisation Epoch lists, merged into its parent company.

    A few models list several organisations ("DeepSeek,Peking University").
    Using the first keeps every model counted exactly once. Models with no
    organisation return None and are left out of every lab-level chart.
    """
    if pd.isna(organization) or not str(organization).strip():
        return None
    first = str(organization).split(",")[0].strip()
    return PARENT_ORG.get(first, first)


def load_eci():
    """One row per model with its ECI score, 90% interval, lab and weights type."""
    df = pd.read_csv(RAW_DIR / "eci_scores.csv")
    df = df.rename(columns={
        "Model": "model", "Display name": "display",
        "eci_ci_low": "ci_low", "eci_ci_high": "ci_high",
        "Organization": "organization",
        "Country (of organization)": "country",
        "Accessibility group": "access",
    })
    df["date"] = pd.to_datetime(df["date"])
    df["lab"] = df["organization"].map(lead_lab)
    # "Other" = Epoch could not tell, or access is limited. Kept out of the
    # open-versus-closed comparison rather than guessed.
    df["access"] = df["access"].where(df["access"].isin(ACCESS), "Other")
    cols = ["model", "display", "eci", "ci_low", "ci_high", "date",
            "organization", "lab", "country", "access"]
    return df[cols].sort_values("date").reset_index(drop=True)


def load_benchmarks():
    """Benchmark release date, random-guess baseline and score ceiling."""
    df = pd.read_csv(RAW_DIR / "benchmark_metadata.csv")
    df = df.rename(columns={"random_baseline": "baseline",
                            "score_ceiling": "ceiling"})
    df["release"] = pd.to_datetime(df["release_date"])
    df["baseline"] = df["baseline"].fillna(0.0)
    df["ceiling"] = df["ceiling"].fillna(1.0)
    return df[["benchmark", "release", "baseline", "ceiling"]]


def load_scores(eci, benchmarks):
    """Every (model, benchmark) score, joined to the model's lab and release date.

    `norm` rescales a score so 0 = random guessing and 1 = the benchmark's
    ceiling, which lets different benchmarks be compared. It is not capped, so a
    model can score above 1 where Epoch's ceiling is below a perfect score.
    """
    p = pd.read_csv(RAW_DIR / "processed_data_for_eci.csv",
                    usecols=["Model", "benchmark", "performance"])
    p = p.dropna(subset=["performance"]).rename(columns={"Model": "model"})
    p = p.merge(eci[["model", "date", "lab", "access"]], on="model", how="inner")
    p = p.merge(benchmarks, on="benchmark", how="left")
    p["norm"] = (p["performance"] - p["baseline"]) / (p["ceiling"] - p["baseline"])
    return p


def load_compute(eci):
    """ECI models that have a published training-compute figure (FLOP).

    Names are matched after stripping punctuation and case, trying Epoch's
    model_version, model_group and display_name columns in that order. Models
    with no match keep a missing value rather than a guess.
    """
    mm = pd.read_csv(RAW_DIR / "model_metadata.csv")
    mm = mm.dropna(subset=["training_compute_flop"])
    lookup = {}
    for col in ["model_version", "model_group", "display_name"]:
        for name, flop in zip(mm[col], mm["training_compute_flop"]):
            if pd.notna(name):
                lookup.setdefault(_key(name), float(flop))
    out = eci.copy()
    flop = out["model"].map(lambda m: lookup.get(_key(m)))
    by_display = out["display"].map(lambda m: lookup.get(_key(m)))
    out["flop"] = flop.fillna(by_display)
    return out
