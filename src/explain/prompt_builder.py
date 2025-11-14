from __future__ import annotations

from typing import Dict, List


def build_run_explanation_prompt(run: Dict, events: List[Dict]) -> str:
    """Build a historical-only prompt describing a price run and related events."""
    direction = run.get("direction", "unknown")
    start = run.get("start", "unknown")
    end = run.get("end", "unknown")
    duration = run.get("duration_bars", "unknown")
    pct_change = run.get("pct_change", "unknown")
    max_drawdown = run.get("max_drawdown_pct", "unknown")

    run_section = (
        f"Run direction: {direction}\n"
        f"Start date: {start}\n"
        f"End date: {end}\n"
        f"Duration (bars): {duration}\n"
        f"Percent change: {pct_change}%\n"
        f"Max adverse move: {max_drawdown}%\n"
    )

    if events:
        event_lines = []
        for event in events:
            date = event.get("date", "unknown date")
            headline = event.get("headline", "(headline missing)")
            url = event.get("url")
            if url:
                event_lines.append(f"- {date}: {headline} ({url})")
            else:
                event_lines.append(f"- {date}: {headline}")
        events_section = "\n".join(event_lines)
    else:
        events_section = "- No public events were linked to this run."

    instructions = (
        "You are a neutral financial historian. Summarize the historical run in 2–3 sentences.\n"
        "Mention public events only as possible context, not guaranteed causes.\n"
        "Do not provide predictions, outlook statements, or buy/sell/hold language.\n"
        "Use phrases like 'during this period', 'historically', or 'the stock experienced...'."
    )

    prompt = (
        "Summarize the following historical price run:\n\n"
        f"{instructions}\n\n"
        "Run details:\n"
        f"{run_section}\n"
        "Relevant public events:\n"
        f"{events_section}\n"
    )

    return prompt
