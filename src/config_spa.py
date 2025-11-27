from __future__ import annotations

import os


def _int_env(name: str, default: int) -> int:
    try:
        val = int(os.getenv(name, default))
        return val
    except Exception:
        return default


def _str_env(name: str, default: str | None) -> str | None:
    val = os.getenv(name)
    return val if val else default


# Max number of runs to explain, capped globally.
SPA_MAX_EXPLAINED_RUNS_DEFAULT: int = _int_env("SPA_MAX_EXPLAINED_RUNS", 2)

# Max tokens per explanation request.
SPA_MAX_EXPLANATION_TOKENS_DEFAULT: int = _int_env("SPA_MAX_EXPLANATION_TOKENS", 350)

# Optional override for LLM model used in SPA explanations.
SPA_LLM_MODEL_DEFAULT: str | None = _str_env("SPA_LLM_MODEL", None)
