from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass(frozen=True)
class PriceRun:
    """Container describing a consecutive up or down price run."""

    run_id: int
    direction: str
    start: pd.Timestamp
    end: pd.Timestamp
    duration_bars: int
    pct_change: float
    max_drawdown_pct: float


def detect_price_runs(df: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
    """Detect consecutive up or down runs within a price series."""
    if price_col not in df.columns:
        raise ValueError(f"DataFrame must contain '{price_col}' column.")
    if len(df) < 2:
        raise ValueError("Need at least two rows to compute price runs.")
    if not df.index.is_monotonic_increasing:
        raise ValueError("DataFrame index must be sorted ascending by date.")
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        raise ValueError("DataFrame index must be a DatetimeIndex.")

    price_series = df[price_col].astype(float)
    returns = price_series.pct_change()
    direction = returns.fillna(0.0)
    direction_flags = direction.gt(0).astype(int) - direction.lt(0).astype(int)

    nonzero_mask = direction_flags != 0
    if not nonzero_mask.any():
        return pd.DataFrame(columns=[field for field in PriceRun.__dataclass_fields__])

    label_source = direction_flags.where(nonzero_mask, 0)
    run_labels = label_source.ne(label_source.shift()).cumsum()

    run_rows = df.loc[nonzero_mask].copy()
    run_rows["direction_flag"] = direction_flags[nonzero_mask].astype(int)
    run_rows["run_id"] = run_labels[nonzero_mask].astype(int)

    runs: List[PriceRun] = []
    for run_id, slice_df in run_rows.groupby("run_id"):
        dir_flag = int(slice_df["direction_flag"].iat[0])
        run_direction = "up" if dir_flag > 0 else "down"
        segment_index = slice_df.index
        start_ts = segment_index[0]
        end_ts = segment_index[-1]
        duration = len(slice_df)
        start_price = price_series.loc[start_ts]
        end_price = price_series.loc[end_ts]
        pct_change = ((end_price / start_price) - 1.0) * 100.0
        segment_prices = price_series.loc[segment_index]
        max_drawdown_pct = _max_adverse_move(segment_prices, dir_flag)

        runs.append(
            PriceRun(
                run_id=int(run_id),
                direction=run_direction,
                start=start_ts,
                end=end_ts,
                duration_bars=duration,
                pct_change=pct_change,
                max_drawdown_pct=max_drawdown_pct,
            )
        )

    return pd.DataFrame([run.__dict__ for run in runs])


def _max_adverse_move(prices: pd.Series, direction_flag: int) -> float:
    """Compute the worst move against a run in percentage terms."""
    if direction_flag > 0:
        cumulative_high = prices.cummax()
        drawdowns = (prices / cumulative_high) - 1.0
        return float(drawdowns.min() * 100.0)

    cumulative_low = prices.cummin()
    runups = (prices / cumulative_low) - 1.0
    return float(runups.max() * 100.0)
