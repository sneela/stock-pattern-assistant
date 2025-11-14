from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.data.fetch_prices import fetch_daily_prices
from src.patterns.runs import detect_price_runs
from src.report.charts import plot_price_with_runs


def analyze_ticker(ticker: str, start: str, end: str, top_n: int = 5) -> None:
    """Fetch prices for a ticker, detect runs, and print the top movers."""
    prices = fetch_daily_prices(ticker=ticker, start=start, end=end)
    runs = detect_price_runs(prices)

    if runs.empty:
        print("No qualifying up/down runs detected in the provided window.")
        return

    runs = runs.copy()
    runs["abs_pct_change"] = runs["pct_change"].abs()
    top_runs = runs.sort_values("abs_pct_change", ascending=False).head(top_n)

    display_cols: Iterable[str] = (
        "direction",
        "start",
        "end",
        "duration_bars",
        "pct_change",
        "max_drawdown_pct",
    )

    printable = top_runs.loc[:, list(display_cols)]

    pd.set_option("display.width", 120)
    pd.set_option("display.max_rows", None)
    print("Top runs for", ticker)
    print(
        printable.to_string(
            index=False,
            formatters={
                "pct_change": "{:.2f}".format,
                "max_drawdown_pct": "{:.2f}".format,
            },
        )
    )

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{ticker}_{start}_{end}.png"
    plot_price_with_runs(prices, top_runs, str(output_file))
    print(f"Saved chart to {output_file}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze historical price runs for a ticker.")
    parser.add_argument("ticker", help="Ticker symbol, e.g., PGR")
    parser.add_argument("start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--top-n", type=int, default=5, dest="top_n", help="Number of runs to display")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    analyze_ticker(ticker=args.ticker, start=args.start, end=args.end, top_n=args.top_n)


if __name__ == "__main__":
    main()
