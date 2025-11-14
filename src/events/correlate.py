from __future__ import annotations

from typing import Dict, List

import pandas as pd


def correlate_runs_with_events(
    runs_df: pd.DataFrame,
    events: List[dict],
    window_days: int = 2,
) -> Dict[int, List[dict]]:
    """Placeholder correlation between runs and events.

    Future implementation will match news events to each run within a time window.
    """
    correlations: Dict[int, List[dict]] = {}
    for run_id in runs_df.get("run_id", []):
        correlations[int(run_id)] = []  # TODO: populate with relevant events.
    return correlations
