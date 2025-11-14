from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

_client: Optional[OpenAI] = None


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


def generate_explanation_from_prompt(prompt: str) -> str:
    """Send a prompt to the configured OpenAI model and return the assistant's text."""
    client = _get_client()

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.3,
        max_tokens=300,
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

    if not response.choices:
        return ""

    content = response.choices[0].message.get("content", "")
    return content.strip() if content else ""
