from __future__ import annotations

from typing import Any, Dict, List, Union

import pandas as pd

from .prompt_builder import build_run_explanation_prompt
from .llm_client import generate_explanation_from_prompt


def explain_single_run(
    run: Union[Dict[str, Any], pd.Series],
    events: List[Dict[str, Any]],
) -> str:
    """Generate a historical-only explanation for a detected price run."""
    run_dict = run.to_dict() if isinstance(run, pd.Series) else dict(run)

    prompt = build_run_explanation_prompt(run_dict, events or [])
    explanation = generate_explanation_from_prompt(prompt)
    return explanation
