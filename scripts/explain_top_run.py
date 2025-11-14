from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src` imports resolve.
ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from data.fetch_prices import fetch_daily_prices  # noqa: E402
from patterns.runs import detect_price_runs  # noqa: E402
from explain.explain_run import explain_single_run  # noqa: E402


def main() -> None:
    ticker = "PGR"
    start = "2024-09-01"
    end = "2024-10-01"

    prices = fetch_daily_prices(ticker, start, end)
    runs = detect_price_runs(prices)

    if runs.empty:
        print("No runs detected for the selected window.")
        return

    runs = runs.copy()
    runs["abs_pct_change"] = runs["pct_change"].abs()
    runs = runs.sort_values("abs_pct_change", ascending=False)

    top_run = runs.iloc[0]
    events_for_top_run: list[dict] = []

    explanation = explain_single_run(top_run, events_for_top_run)
    print("Historical explanation for the top run:\n")
    print(explanation or "(No explanation returned)")


if __name__ == "__main__":
    main()
