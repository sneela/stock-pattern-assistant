from __future__ import annotations

from typing import Any, Dict, List, Union

import pandas as pd

from src.config_spa import (
    SPA_LLM_MODEL_DEFAULT,
    SPA_MAX_EXPLANATION_TOKENS_DEFAULT,
)

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


def explain_run_with_events(
    ticker: str,
    run_row: pd.Series,
    events: List[Dict[str, Any]],
    max_tokens: int = 400,
) -> str:
    """
    Generate a historical-only explanation for a single run and its correlated events.

    This must never include predictions or investment advice; it should only describe
    past price behavior and contextual public events.
    """
    run_dict = run_row.to_dict() if isinstance(run_row, pd.Series) else dict(run_row)
    run_dict["ticker"] = ticker

    prompt = build_run_explanation_prompt(run_dict, events or [])
    try:
        effective_tokens = min(max_tokens, SPA_MAX_EXPLANATION_TOKENS_DEFAULT)
        return generate_explanation_from_prompt(
            prompt,
            max_tokens=effective_tokens,
            temperature=0.0,
            model=SPA_LLM_MODEL_DEFAULT,
        )
    except Exception as exc:
        print(f"[SPA] Warning: explanation skipped for {ticker} run_id={run_dict.get('run_id')}: {exc}")
        return ""
