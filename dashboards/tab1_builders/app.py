"""Run only this tab:  streamlit run dashboards/tab1_builders/app.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # project root

from core.page import run_standalone  # noqa: E402
from dashboards.tab1_builders import PAGE  # noqa: E402

run_standalone(PAGE)
