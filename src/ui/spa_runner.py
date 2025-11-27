from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from src.data.fetch_news import fetch_news_for_ticker
from src.data.fetch_prices import fetch_daily_prices
from src.events.correlate import correlate_runs_with_events
from src.explain.explain_run import explain_run_with_events
from src.explain.llm_client import LLMQuotaExceededError
from src.patterns.runs import detect_price_runs
from src.config_spa import SPA_MAX_EXPLAINED_RUNS_DEFAULT


def run_spa_for_single_ticker(
    ticker: str,
    start: str,
    end: str,
    window_days: int = 2,
    max_news_items: int = 50,
    fetch_events: bool = True,
    generate_explanations: bool = False,
    max_explained_runs: int = 3,
) -> Dict[str, Optional[object]]:
    """
    Run the SPA pipeline for a single ticker: fetch prices, detect runs, fetch/correlate events,
    and optionally generate historical-only explanations.
    """
    result: Dict[str, Optional[object]] = {
        "prices": None,
        "runs": pd.DataFrame(),
        "events": [],
        "correlations": {},
        "explanations": [],
        "error": None,
        "explanation_error": None,
    }

    try:
        prices = fetch_daily_prices(ticker, start, end)
        result["prices"] = prices
    except Exception as exc:  # pragma: no cover - runtime path
        result["error"] = f"Failed to fetch prices for {ticker}: {exc}"
        return result

    try:
        runs_df = detect_price_runs(result["prices"])
        result["runs"] = runs_df
    except Exception as exc:  # pragma: no cover - runtime path
        result["error"] = f"Failed to detect runs for {ticker}: {exc}"
        return result

    if fetch_events:
        try:
            events = fetch_news_for_ticker(ticker, start, end, max_items=max_news_items)
            result["events"] = events
        except Exception as exc:  # pragma: no cover - runtime path
            result["error"] = f"Failed to fetch events for {ticker}: {exc}"
            return result
    else:
        events = []

    correlations = correlate_runs_with_events(result["runs"], events, window_days=window_days)
    result["correlations"] = correlations

    if generate_explanations and not result["runs"].empty:
        try:
            explanations = _generate_explanations_for_runs(
                ticker=ticker,
                runs_df=result["runs"],
                correlations=result["correlations"],
                max_explained_runs=max_explained_runs,
            )
            result["explanations"] = explanations
        except LLMQuotaExceededError as exc:  # pragma: no cover - runtime path
            result["explanation_error"] = str(exc)
        except Exception as exc:  # pragma: no cover - runtime path
            result["explanation_error"] = f"Explanation generation failed: {exc}"

    return result


def _generate_explanations_for_runs(
    ticker: str,
    runs_df: pd.DataFrame,
    correlations: Dict[int, List[Dict]],
    max_explained_runs: int,
) -> List[Dict]:
    """Select runs and generate LLM explanations with correlated events."""
    runs = runs_df.copy()
    runs["abs_pct_change"] = runs["pct_change"].abs()
    effective_max = min(max_explained_runs, SPA_MAX_EXPLAINED_RUNS_DEFAULT)
    selected = runs.sort_values("abs_pct_change", ascending=False).head(effective_max)

    explanations: List[Dict] = []
    for _, run_row in selected.iterrows():
        run_id = int(run_row.get("run_id"))
        events = correlations.get(run_id, [])
        try:
            text = explain_run_with_events(ticker, run_row, events)
        except Exception as exc:  # pragma: no cover - runtime path
            print(f"[SPA] Warning: explanation skipped for {ticker} run_id={run_id}: {exc}")
            text = ""
        explanations.append(
            {
                "run_id": run_id,
                "start": _ts_to_iso(run_row.get("start")),
                "end": _ts_to_iso(run_row.get("end")),
                "direction": run_row.get("direction"),
                "duration_bars": run_row.get("duration_bars"),
                "pct_change": run_row.get("pct_change"),
                "max_drawdown_pct": run_row.get("max_drawdown_pct"),
                "explanation": text,
            }
        )
    return explanations


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
