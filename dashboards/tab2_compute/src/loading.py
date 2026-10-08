"""Read and clean Epoch AI 'GPU Clusters' and 'AI Chip Sales' datasets.

Every number in this tab comes from:
1. dashboards/tab2_compute/data/raw/epoch_gpu_clusters/gpu_clusters.csv
   (Downloaded from https://epoch.ai/data/gpu_clusters.csv on 8 October 2026)
2. dashboards/tab2_compute/data/raw/epoch_chip_sales/cumulative_timelines_by_designer.csv
   (Downloaded from https://epoch.ai/data/ai_chip_sales.zip on 8 October 2026)

Cleaning and normalization happen strictly in this file. Calculations are in
analysis.py and rendering in views.py.
"""

from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_CLUSTERS_DIR = DATA_DIR / "raw" / "epoch_gpu_clusters"
RAW_CHIP_SALES_DIR = DATA_DIR / "raw" / "epoch_chip_sales"
DOWNLOADED = "8 October 2026"

PARENT_MAPPING = {
    "Meta AI": "Meta",
    "Meta": "Meta",
    "Microsoft": "Microsoft / OpenAI",
    "Microsoft,OpenAI": "Microsoft / OpenAI",
    "Google": "Google",
    "Amazon": "Amazon",
    "xAI": "xAI",
    "Oracle": "Oracle Cloud",
    "Tesla": "Tesla",
    "CoreWeave": "CoreWeave",
    "Nvidia,CoreWeave": "CoreWeave",
    "Nebius AI": "Nebius AI",
    "Lambda": "Lambda Labs",
    "Lambda Labs": "Lambda Labs",
    "Sesterce": "Sesterce",
    "NexGen Cloud": "NexGen Cloud",
    "Northern Data Group": "Northern Data Group",
    "US Department of Energy": "US Dept of Energy",
    "EuroHPC JU,Julich Supercomputing Center": "EuroHPC",
    "EuroHPC JU": "EuroHPC",
    "ETH Domain": "ETH Zurich",
    "National Institute of Advanced Industrial Science and Technology (AIST)": "AIST",
    "UK Research and Innovation": "UKRI",
    "GENCI": "GENCI",
    "RIKEN": "RIKEN",
    "Nvidia": "NVIDIA",
    "ByteDance": "ByteDance",
    "Alibaba": "Alibaba",
    "Tencent": "Tencent",
    "Baidu": "Baidu",
    "Softbank": "SoftBank",
}

EUROPE_COUNTRIES = {
    "France", "Germany", "Italy", "United Kingdom", "Switzerland", "Finland",
    "Sweden", "Poland", "Norway", "Netherlands", "Iceland", "Spain", "Denmark",
    "Luxembourg", "Czechia", "Slovenia", "Ireland", "Austria", "Belgium"
}

COUNTRY_GROUPS = [
    "United States",
    "China",
    "Europe",
    "Rest of world",
]


def clean_parent(owner):
    """Normalize raw cluster owner strings into standardized parent entities."""
    if pd.isna(owner) or not str(owner).strip():
        return "Undisclosed / Export-Restricted"
    o = str(owner).strip()
    for raw_name, parent_name in PARENT_MAPPING.items():
        if raw_name.lower() in o.lower():
            return parent_name
    return o.split(",")[0].strip()


def classify_country_group(row):
    """Map cluster location and owner into 4 geopolitical regions:
    United States, China, Europe, and Rest of world.
    """
    c = str(row["Country"]).strip() if pd.notna(row["Country"]) else ""
    o = str(row["Owner"]).strip() if pd.notna(row["Owner"]) else ""
    name = str(row["Name"]).strip() if pd.notna(row["Name"]) else ""

    if c == "United States of America" or "United States" in c:
        return "United States"
    if c == "China" or "Hong Kong" in c or "Chinese" in name:
        return "China"
    if c in EUROPE_COUNTRIES or "EuroHPC" in o or "ETH" in o or "Jülich" in o:
        return "Europe"
    if c and c != "nan":
        return "Rest of world"

    # Fallbacks for unspecified country based on confirmed owner HQ
    if any(k in o for k in ["xAI", "Meta", "Microsoft", "OpenAI", "Google", "Amazon", "Oracle", "Tesla", "CoreWeave", "Energy"]):
        return "United States"
    if any(k in o for k in ["EuroHPC", "ETH", "GENCI", "Nebius", "Sesterce"]):
        return "Europe"
    return "Rest of world"


def load_clusters():
    """Load and clean the Epoch AI GPU clusters database."""
    csv_path = RAW_CLUSTERS_DIR / "gpu_clusters.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing cluster dataset at {csv_path}")

    df = pd.read_csv(csv_path)

    # 1. Clean operational dates
    df["date"] = pd.to_datetime(df["First Operational Date"], errors="coerce")
    df["year"] = df["date"].dt.year

    # 2. Coerce numeric metrics
    df["h100_equiv"] = pd.to_numeric(df["H100 equivalents"], errors="coerce").fillna(0.0)
    df["power_mw"] = pd.to_numeric(df["Power Capacity (MW)"], errors="coerce")
    df["calc_power_mw"] = pd.to_numeric(df["Calculated Power Capacity (MW)"], errors="coerce")
    df["total_chips"] = pd.to_numeric(df["Total number of AI chips"], errors="coerce")
    df["power_mw"] = df["power_mw"].fillna(df["calc_power_mw"])

    # 3. Standardize parent owners and geopolitical country groupings
    df["parent"] = df["Owner"].map(clean_parent)
    df["country_group"] = df.apply(classify_country_group, axis=1)

    # 4. Filter excluded duplicates if flagged
    if "Exclude" in df.columns:
        df = df[df["Exclude"] != True].copy()

    return df


def load_chip_sales_timeline():
    """Load and clean the Epoch AI quarterly AI chip sales timeline."""
    csv_path = RAW_CHIP_SALES_DIR / "cumulative_timelines_by_designer.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing chip sales dataset at {csv_path}")

    df = pd.read_csv(csv_path)

    df["date"] = pd.to_datetime(df["End date"], errors="coerce")
    df["designer"] = df["Chip manufacturer"].str.strip()
    df["cumulative_h100"] = pd.to_numeric(df["Compute estimate in H100e (median)"], errors="coerce").fillna(0.0)
    df["units"] = pd.to_numeric(df["Number of units (median)"], errors="coerce").fillna(0.0)
    df["power_mw"] = pd.to_numeric(df["Power in MW (median)"], errors="coerce").fillna(0.0)

    # Retain primary designers with substantial volume
    major_designers = ["Nvidia", "Google", "AMD", "Huawei", "Amazon"]
    df = df[df["designer"].isin(major_designers)].dropna(subset=["date"]).copy()
    df = df.sort_values(by=["date", "designer"]).reset_index(drop=True)
    return df
