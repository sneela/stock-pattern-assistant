from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_price_with_runs(
    df: pd.DataFrame,
    runs_df: pd.DataFrame,
    output_path: str,
    price_col: str = "close",
) -> None:
    """Plot closing prices with transparent overlays for up/down runs."""
    if price_col not in df.columns:
        raise ValueError(f"DataFrame must contain '{price_col}' column.")
    if df.empty:
        raise ValueError("Price DataFrame is empty; nothing to plot.")

    price_series = df[price_col]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(price_series.index, price_series, label=price_col.capitalize(), color="black")

    if not runs_df.empty:
        for _, run in runs_df.iterrows():
            start = pd.Timestamp(run["start"])
            end = pd.Timestamp(run["end"])
            direction = str(run["direction"]).lower()
            color = "#2ca02c" if direction == "up" else "#d62728"
            ax.axvspan(start, end, color=color, alpha=0.15)

    ax.set_title("Price with Detected Runs")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.15, linewidth=0.5)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig.subplots_adjust(left=0.08, right=0.98)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_price_with_runs_and_events(
    df: pd.DataFrame,
    runs_df: pd.DataFrame,
    events_by_run: dict[int, list[dict]],
    output_path: str,
    price_col: str = "close",
) -> None:
    """Plot prices with run overlays and event markers."""
    if price_col not in df.columns:
        raise ValueError(f"DataFrame must contain '{price_col}' column.")
    if df.empty:
        raise ValueError("Price DataFrame is empty; nothing to plot.")

    price_series = df[price_col]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(price_series.index, price_series, label=price_col.capitalize(), color="black")

    if runs_df is not None and not runs_df.empty:
        for _, run in runs_df.iterrows():
            start = pd.Timestamp(run["start"])
            end = pd.Timestamp(run["end"])
            direction = str(run["direction"]).lower()
            color = "#2ca02c" if direction == "up" else "#d62728"
            ax.axvspan(start, end, color=color, alpha=0.08)

    # Collect unique event dates for markers.
    event_dates = []
    if events_by_run:
        for ev_list in events_by_run.values():
            for ev in ev_list:
                date_val = ev.get("date")
                if isinstance(date_val, pd.Timestamp):
                    event_dates.append(date_val.normalize())

    if event_dates:
        unique_dates = sorted({d for d in event_dates})
        for d in unique_dates:
            ax.axvline(d, color="#1f77b4", linestyle="--", alpha=0.15, linewidth=0.75)
        for d in unique_dates:
            if d in price_series.index:
                ax.scatter(d, price_series.loc[d], color="#1f77b4", s=18, zorder=3, label="_nolegend_")

    ax.set_title("Price with Runs and Events")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.15, linewidth=0.5)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig.subplots_adjust(left=0.08, right=0.98)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
