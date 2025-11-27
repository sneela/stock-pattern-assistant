from __future__ import annotations

from typing import Dict, List

import pandas as pd


def correlate_runs_with_events(
    runs_df: pd.DataFrame,
    events: List[dict],
    window_days: int = 2,
) -> Dict[int, List[dict]]:
    """Match events to runs within a symmetric +/- window_days around run start."""
    if runs_df is None or runs_df.empty:
        return {}

    correlations: Dict[int, List[dict]] = {}
    normalized_events = [_ensure_timestamp_event(e) for e in events or []]

    for _, run in runs_df.iterrows():
        run_id = int(run.get("run_id"))
        run_start = _get_run_ts(run, "start", "run_start")
        run_end = _get_run_ts(run, "end", "run_end")

        if run_start is None or run_end is None:
            correlations[run_id] = []
            continue

        window_start = run_start - pd.Timedelta(days=window_days)
        window_end = run_start + pd.Timedelta(days=window_days)

        matched: List[dict] = []
        for event in normalized_events:
            if _event_falls_in_window(event, window_start, window_end):
                days_from_run_start = int((event["date"].normalize() - run_start.normalize()).days)
                enriched = dict(event)
                enriched["days_from_run_start"] = days_from_run_start
                matched.append(enriched)

        correlations[run_id] = _score_and_sort_events(matched, run_start)

    return correlations


def _event_falls_in_window(event: dict, window_start: pd.Timestamp, window_end: pd.Timestamp) -> bool:
    """Check if an event date lies within [window_start, window_end]."""
    event_date = event.get("date")
    if not isinstance(event_date, pd.Timestamp):
        return False
    return window_start.normalize() <= event_date.normalize() <= window_end.normalize()


def _score_and_sort_events(events: List[dict], run_start: pd.Timestamp) -> List[dict]:
    """Sort events deterministically by proximity to run start, then date, then headline."""
    def _key(ev: dict) -> tuple:
        delta_days = int((ev["date"].normalize() - run_start.normalize()).days)
        return (abs(delta_days), ev["date"], ev.get("headline", ""))

    return sorted(events, key=_key)


def _ensure_timestamp_event(event: dict) -> dict:
    """Return a shallow copy of an event with its date coerced to Timestamp if possible."""
    copied = dict(event)
    date_val = copied.get("date")
    try:
        copied["date"] = pd.Timestamp(date_val).tz_localize(None) if not isinstance(date_val, pd.Timestamp) else date_val.tz_localize(None)
    except Exception:
        copied["date"] = None
    return copied


def _get_run_ts(run: pd.Series, primary_key: str, fallback_key: str) -> pd.Timestamp | None:
    """Get a timezone-naive Timestamp for run start/end from possible column names."""
    if primary_key in run:
        raw = run[primary_key]
    elif fallback_key in run:
        raw = run[fallback_key]
    else:
        return None
    try:
        return pd.Timestamp(raw).tz_localize(None)
    except Exception:
        return None
