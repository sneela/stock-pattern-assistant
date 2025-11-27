from __future__ import annotations

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

_client: Optional[OpenAI] = None


class LLMQuotaExceededError(RuntimeError):
    """Raised when the LLM provider reports insufficient quota (HTTP 429)."""


def _get_client() -> OpenAI:
    """Return a shared OpenAI client instance, ensuring configuration is present."""
    global _client

    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Populate it in your .env file before requesting explanations."
        )

    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)

    return _client


def generate_explanation_from_prompt(
    prompt: str,
    max_tokens: int = 400,
    temperature: float = 0.0,
    model: str | None = None,
) -> str:
    """Send a prompt to the configured OpenAI model and return the assistant's text."""
    client = _get_client()

    model_name = model or OPENAI_MODEL

    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a neutral financial historian. Only describe historical price movements. "
                        "Never predict future performance or offer investment recommendations. "
                        "Avoid directives such as 'you should buy/sell/hold.'"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        message = str(exc)
        if "insufficient_quota" in message or "429" in message:
            warn = "OpenAI quota exceeded (429 insufficient_quota). Skipping explanations for this run."
            print(f"[SPA] Warning: {warn}", file=sys.stderr)
            raise LLMQuotaExceededError(warn) from exc
        raise

    if not response.choices:
        return ""

    message = response.choices[0].message
    content = getattr(message, "content", None)
    return content.strip() if content else ""
