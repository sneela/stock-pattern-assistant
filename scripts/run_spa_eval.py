from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Ensure the repository root is available on sys.path for `src` imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.report.charts import plot_price_with_runs, plot_price_with_runs_and_events  # noqa: E402
from src.ui.spa_runner import run_spa_for_single_ticker  # noqa: E402
from src.config_spa import SPA_MAX_EXPLAINED_RUNS_DEFAULT  # noqa: E402


def run_spa_evaluation(
    tickers: List[str],
    start: str,
    end: str,
    output_root: str = "artifacts/eval",
    window_days: int = 2,
    max_news_items: int = 50,
    generate_charts: bool = True,
    generate_explanations: bool = False,
    max_explained_runs: int = 3,
) -> None:
    """
    Run the SPA pipeline for multiple tickers and save artifacts for analysis.

    This is the evaluation harness referenced in the SPA abstract for AAPL, NVDA, SCHW, and PGR.
    """
    output_root_path = Path(output_root)
    output_root_path.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        ticker_upper = ticker.upper()
        ticker_dir = output_root_path / ticker_upper
        ticker_dir.mkdir(parents=True, exist_ok=True)
        print(f"[SPA] Evaluating {ticker_upper} from {start} to {end}...")

        result = run_spa_for_single_ticker(
            ticker=ticker_upper,
            start=start,
            end=end,
            window_days=window_days,
            max_news_items=max_news_items,
            fetch_events=True,
            generate_explanations=generate_explanations,
            max_explained_runs=max_explained_runs,
        )

        if result.get("error"):
            print(f"[SPA] Warning: {result['error']}")
            continue

        prices: pd.DataFrame = result.get("prices") or pd.DataFrame()
        runs_df: pd.DataFrame = result.get("runs") or pd.DataFrame()
        events = result.get("events") or []
        correlations = result.get("correlations") or {}
        explanations = result.get("explanations") or []

        _write_runs(runs_df, ticker_dir)
        _write_events(events, ticker_dir)
        _write_correlations(correlations, ticker_dir)

        if generate_charts and not prices.empty:
            try:
                plot_price_with_runs(prices, runs_df, output_path=ticker_dir / "price_with_runs.png")
                plot_price_with_runs_and_events(
                    prices,
                    runs_df,
                    correlations,
                    output_path=ticker_dir / "price_with_runs_and_events.png",
                )
            except Exception as exc:
                print(f"[SPA] Warning: failed to generate charts for {ticker_upper}: {exc}")

        if generate_explanations and explanations:
            try:
                _write_explanations_md(
                    explanations=explanations,
                    ticker=ticker_upper,
                    start=start,
                    end=end,
                    output_path=ticker_dir / "explanations.md",
                )
            except Exception as exc:
                print(f"[SPA] Warning: failed to write explanations for {ticker_upper}: {exc}")
        if result.get("explanation_error"):
            print(f"[SPA] Warning: {result['explanation_error']}")

        print(f"[SPA] Completed {ticker_upper}. Artifacts in {ticker_dir}")


def _write_runs(runs_df: pd.DataFrame, ticker_dir: Path) -> None:
    """Persist runs dataframe to CSV and Parquet (if supported)."""
    csv_path = ticker_dir / "runs.csv"
    parquet_path = ticker_dir / "runs.parquet"
    runs_df.to_csv(csv_path, index=False)
    try:
        runs_df.to_parquet(parquet_path, index=False)
    except Exception as exc:
        print(f"[SPA] Warning: could not write Parquet ({parquet_path}): {exc}")


def _write_events(events: List[Dict], ticker_dir: Path) -> None:
    """Persist normalized events as JSON."""
    events_path = ticker_dir / "events.json"
    serialized = [_serialize_event(ev) for ev in events]
    events_path.write_text(json.dumps(serialized, indent=2))


def _write_correlations(correlations: Dict[int, List[Dict]], ticker_dir: Path) -> None:
    """Persist run-event correlations as JSON."""
    corr_path = ticker_dir / "correlations.json"
    serialized: Dict[str, List[Dict]] = {}
    for run_id in sorted(correlations.keys()):
        serialized[str(run_id)] = [_serialize_event(ev, include_days=True) for ev in correlations[run_id]]
    corr_path.write_text(json.dumps(serialized, indent=2))


def _serialize_event(event: Dict, include_days: bool = False) -> Dict:
    """Serialize event dict for JSON output."""
    out = {
        "date": _ts_to_iso(event.get("date")),
        "headline": event.get("headline"),
        "source": event.get("source"),
        "url": event.get("url"),
        "summary": event.get("summary"),
        "ticker": event.get("ticker"),
    }
    if include_days:
        out["days_from_run_start"] = event.get("days_from_run_start")
    return out


def _ts_to_iso(value) -> str | None:
    """Convert Timestamp or datetime-like to ISO date string."""
    if value is None:
        return None
    try:
        ts = pd.Timestamp(value)
    except Exception:
        return None
    ts = ts.tz_localize(None) if ts.tzinfo else ts
    return ts.isoformat()


def _write_explanations_md(
    explanations: List[Dict],
    ticker: str,
    start: str,
    end: str,
    output_path: Path,
) -> None:
    """Write explanations to a Markdown file."""
    lines = [
        f"# Explanations for {ticker}",
        f"Date range: {start} to {end}",
        "",
    ]

    for entry in explanations:
        run_id = entry["run_id"]
        lines.append(f"## Run {run_id}")
        lines.append(
            f"- Direction: {entry.get('direction')} | Start: {entry.get('start')} | End: {entry.get('end')} | "
            f"Duration: {entry.get('duration_bars')} bars | Pct change: {entry.get('pct_change')} | "
            f"Max drawdown: {entry.get('max_drawdown_pct')}"
        )
        expl = entry.get("explanation") or "(No explanation generated)"
        lines.append("")
        lines.append(expl)
        lines.append("")

    output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SPA evaluation on multiple tickers.")
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "NVDA", "SCHW", "PGR"])
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-root", default="artifacts/eval")
    parser.add_argument("--window-days", type=int, default=2)
    parser.add_argument("--max-news-items", type=int, default=50)
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    parser.add_argument("--with-explanations", action="store_true", help="Generate LLM-based historical explanations")
    parser.add_argument(
        "--max-explained-runs",
        type=int,
        default=SPA_MAX_EXPLAINED_RUNS_DEFAULT,
        help=f"Requested runs per ticker to explain (effective cap: {SPA_MAX_EXPLAINED_RUNS_DEFAULT})",
    )
    args = parser.parse_args()

    run_spa_evaluation(
        tickers=args.tickers,
        start=args.start,
        end=args.end,
        output_root=args.output_root,
        window_days=args.window_days,
        max_news_items=args.max_news_items,
        generate_charts=not args.no_charts,
        generate_explanations=args.with_explanations,
        max_explained_runs=args.max_explained_runs,
    )
