from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is available on sys.path for `src` imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.cli import analyze_ticker


if __name__ == "__main__":
    analyze_ticker(ticker="PGR", start="2024-09-01", end="2024-10-01")
