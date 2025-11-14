from __future__ import annotations

from datetime import datetime
import pandas as pd
import yfinance as yf


def fetch_daily_prices(
    ticker: str,
    start: str,
    end: str,
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """Fetch daily OHLCV data for the ticker between start and end."""
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)

    if start_dt >= end_dt:
        raise ValueError(
            f"start ({start_dt.date()}) must be earlier than end ({end_dt.date()})."
        )

    raw = yf.download(
        tickers=ticker,
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        interval="1d",
        auto_adjust=auto_adjust,
        progress=False,
        actions=False,
    )

    if raw.empty:
        raise ValueError(
            f"No price data returned for {ticker} between {start_dt.date()} and {end_dt.date()}."
        )

    cleaned = (
        raw.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        [["open", "high", "low", "close", "volume"]]
        .sort_index()
    )

    if isinstance(cleaned.columns, pd.MultiIndex):
        cleaned.columns = cleaned.columns.get_level_values(0)

    cleaned.index = pd.to_datetime(cleaned.index)
    cleaned.index.name = "date"
    return cleaned


def _parse_date(value: str | datetime | pd.Timestamp) -> pd.Timestamp:
    """Parse input into a timezone-naive pandas Timestamp."""
    if isinstance(value, pd.Timestamp):
        return value.tz_localize(None)
    if isinstance(value, datetime):
        return pd.Timestamp(value).tz_localize(None)
    try:
        return pd.Timestamp(value).tz_localize(None)
    except ValueError as exc:  # pragma: no cover - pandas message is descriptive
        raise ValueError(f"Invalid date value: {value}") from exc
