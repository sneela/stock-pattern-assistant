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
    ax.grid(True, linestyle="--", alpha=0.3)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
