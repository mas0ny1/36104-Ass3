import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.page import run_standalone  # noqa: E402
from dashboards.tab4_capability import PAGE  # noqa: E402

run_standalone(PAGE)
