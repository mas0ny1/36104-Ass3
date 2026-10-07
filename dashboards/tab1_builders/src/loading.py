"""Read and clean the Epoch AI 'Data on AI models' files.

Every number in this tab comes from one of three CSVs in
data/raw/epoch_ai_models/ (downloaded from https://epoch.ai/data/ai_models.zip):

    notable_ai_models.csv      models meeting Epoch's notability criteria
    large_scale_ai_models.csv  models trained with at least 1e23 FLOP
    frontier_ai_models.csv     models in the top 5 by training compute at release

Cleaning only happens here; calculations are in analysis.py and charts in views.py.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw" / "epoch_ai_models"
DOWNLOADED = "7 October 2026"

# Labs that Epoch lists under several names are merged into their parent
# company, so Google Brain + DeepMind + Google Research all count as Google.
PARENT_ORG = {
    "Google": "Google", "Google DeepMind": "Google", "DeepMind": "Google",
    "Google Research": "Google", "Google Brain": "Google",
    "Google AI": "Google", "Google Cloud": "Google",
    "Meta AI": "Meta", "Facebook AI Research": "Meta", "Facebook AI": "Meta",
    "Facebook": "Meta",
    "Microsoft": "Microsoft", "Microsoft Research": "Microsoft",
    "Microsoft Research Asia": "Microsoft",
    "Microsoft Research AI for Science": "Microsoft",
    "Alibaba": "Alibaba", "Alibaba DAMO Academy": "Alibaba",
    "Amazon": "Amazon", "Amazon Web Services (AWS)": "Amazon",
    "Amazon Machine Learning Solutions Lab": "Amazon",
    "IBM": "IBM", "IBM Research": "IBM",
    "Huawei": "Huawei", "Huawei Noah's Ark Lab": "Huawei",
    "Baidu": "Baidu", "Baidu Research - Silicon Valley AI Lab": "Baidu",
    "Salesforce": "Salesforce", "Salesforce Research": "Salesforce",
    "Cohere": "Cohere", "Cohere Labs (formerly Cohere for AI)": "Cohere",
    "G42": "G42", "Inception G42": "G42",
    "LG": "LG", "LG AI Research": "LG",
    "Z.ai (Zhipu AI)": "Zhipu AI",
    "Beijing Academy of Artificial Intelligence / BAAI": "BAAI",
}

# One organisation name contains a comma, which would otherwise be split in two.
COMMA_NAMES = {"Qilin Hesheng Network Technology Co.,Ltd. (APUS)":
               "Qilin Hesheng (APUS)"}

SECTORS = ["Industry", "Industry–academia collaboration", "Academia", "Other"]
COUNTRY_GROUPS = ["United States", "China", "Rest of world"]


def split_list(cell):
    """Split a comma-separated Epoch field into a clean list of names."""
    if pd.isna(cell):
        return []
    text = str(cell)
    for long_name, short_name in COMMA_NAMES.items():
        text = text.replace(long_name, short_name)
    return [t.strip() for t in text.split(",") if t.strip()]


def country_group(country):
    if country == "United States of America":
        return "United States"
    if country == "China":
        return "China"
    return "Rest of world"


def _sector(categories):
    """Classify a model by the sectors of all its listed organisations."""
    kinds = set(categories)
    if kinds == {"Industry"}:
        return "Industry"
    if kinds == {"Academia"}:
        return "Academia"
    if {"Industry", "Academia"} <= kinds:
        return "Industry–academia collaboration"
    return "Other"   # government, non-profit, research collective and mixes


def _read(name):
    df = pd.read_csv(RAW_DIR / f"{name}.csv")
    df["date"] = pd.to_datetime(df["Publication date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df["year"] = df["date"].dt.year
    df["orgs"] = df["Organization"].map(split_list)
    df["parents"] = df["orgs"].map(
        lambda orgs: list(dict.fromkeys(PARENT_ORG.get(o, o) for o in orgs)))
    return df


def load_notable():
    """Notable models with a sector label (Industry / Academia / ...)."""
    df = _read("notable_ai_models")
    df["sector"] = df["Organization categorization"].map(split_list).map(_sector)
    return df


def load_large_scale():
    """Models Epoch judges were trained with >= 1e23 FLOP.

    About 40% of rows have no compute figure: Epoch includes them because they
    are very likely above 1e23 FLOP (e.g. recent OpenAI, Google and Anthropic
    flagships) but their developers have not published enough to estimate it.
    `compute` is left blank for those rows rather than guessed.
    """
    df = _read("large_scale_ai_models")
    df["compute"] = df["Training compute (FLOP)"]
    return df


def load_frontier():
    """Frontier models (top 5 by compute when released) with a cost estimate."""
    df = _read("frontier_ai_models")
    df["cost_usd"] = df["Training compute cost (2023 USD)"]
    df["parent"] = df["parents"].map(lambda p: " / ".join(p) or "Not listed")
    return df
