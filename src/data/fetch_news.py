from __future__ import annotations

from typing import Dict, List

import pandas as pd

# Deterministic sample headlines per ticker to avoid network dependencies.
_SAMPLE_NEWS: Dict[str, List[Dict]] = {
    "PGR": [
        {"date": "2024-09-03", "headline": "Progressive announces monthly catastrophe loss estimate", "source": "Press release", "url": None, "summary": None},
        {"date": "2024-09-12", "headline": "Analyst notes steady auto claims trends at Progressive", "source": "Analyst", "url": None, "summary": None},
        {"date": "2024-09-24", "headline": "Progressive reports Q3 premium growth figures", "source": "Newswire", "url": None, "summary": None},
    ],
    "AAPL": [
        {"date": "2024-09-10", "headline": "Apple unveils new iPhone lineup at fall event", "source": "Newswire", "url": None, "summary": None},
        {"date": "2024-09-20", "headline": "Early reviews highlight camera upgrades", "source": "Blog", "url": None, "summary": None},
    ],
    "NVDA": [
        {"date": "2024-09-05", "headline": "NVIDIA announces new data center GPU roadmap", "source": "Newswire", "url": None, "summary": None},
        {"date": "2024-09-18", "headline": "Report: Cloud providers expand NVIDIA GPU orders", "source": "Analyst", "url": None, "summary": None},
    ],
    "SCHW": [
        {"date": "2024-09-09", "headline": "Charles Schwab reports client asset flows for August", "source": "Press release", "url": None, "summary": None},
        {"date": "2024-09-27", "headline": "Schwab completes platform migration milestone", "source": "Newswire", "url": None, "summary": None},
    ],
}


def fetch_news_for_ticker(ticker: str, start: str, end: str, max_items: int = 100) -> List[Dict]:
    """Return deterministic public-news items for a ticker within [start, end]."""
    start_ts = _parse_date(start)
    end_ts = _parse_date(end)
    raw_items = _SAMPLE_NEWS.get(ticker.upper(), [])
    return _standardize_news_items(raw_items, start_ts, end_ts, max_items, ticker=ticker.upper())


def _standardize_news_items(
    raw_items: List[Dict],
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    max_items: int,
    ticker: str,
) -> List[Dict]:
    """Normalize, filter, and sort raw items to a stable schema."""
    normalized: List[Dict] = []
    for item in raw_items:
        try:
            event_ts = _parse_date(item.get("date"))
        except Exception:
            continue

        if event_ts < start_ts or event_ts > end_ts:
            continue

        normalized.append(
            {
                "date": event_ts,
                "headline": str(item.get("headline", "")).strip(),
                "source": item.get("source"),
                "url": item.get("url"),
                "summary": item.get("summary"),
                "ticker": ticker,
            }
        )

    # Deterministic ordering: date ascending, then headline.
    normalized.sort(key=lambda x: (x["date"], x["headline"]))
    return normalized[:max_items]


def _parse_date(value: str | pd.Timestamp) -> pd.Timestamp:
    """Parse input into a timezone-naive pandas Timestamp."""
    if isinstance(value, pd.Timestamp):
        return value.tz_localize(None)
    parsed = pd.Timestamp(value)
    return parsed.tz_localize(None)
