from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
import tempfile
import json

import pandas as pd
import streamlit as st

# Ensure the repository root is available on sys.path for `src` imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.report.charts import plot_price_with_runs_and_events  # noqa: E402
from src.ui.spa_runner import run_spa_for_single_ticker  # noqa: E402
from src.config_spa import SPA_MAX_EXPLAINED_RUNS_DEFAULT  # noqa: E402


st.set_page_config(page_title="Stock Pattern Assistant (SPA)", layout="wide")
st.title("Stock Pattern Assistant (SPA)")


@st.cache_data(show_spinner=False)
def cached_run_spa_for_single_ticker(
    ticker: str,
    start: str,
    end: str,
    window_days: int,
    max_news_items: int,
    fetch_events: bool,
    generate_explanations: bool,
    max_explained_runs: int,
):
    """Cached wrapper around run_spa_for_single_ticker."""
    return run_spa_for_single_ticker(
        ticker=ticker,
        start=start,
        end=end,
        window_days=window_days,
        max_news_items=max_news_items,
        fetch_events=fetch_events,
        generate_explanations=generate_explanations,
        max_explained_runs=max_explained_runs,
    )


def main() -> None:
    today = date.today()
    default_start = today - timedelta(days=60)

    with st.sidebar:
        tickers_input = st.text_input("Tickers (comma-separated)", value="AAPL,NVDA")
        start_date = st.date_input("Start Date", value=default_start)
        end_date = st.date_input("End Date", value=today)
        window_days = st.number_input("Event correlation window (days)", min_value=0, max_value=10, value=2, step=1)
        fetch_events = st.checkbox("Fetch & correlate news/events", value=True)
        generate_explanations = st.checkbox("Generate explanations (if LLM configured)", value=False)
        max_allowed = max(0, SPA_MAX_EXPLAINED_RUNS_DEFAULT)
        default_expl = 1 if max_allowed >= 1 else 0
        max_explained_runs = st.slider(
            "Max explained runs",
            min_value=0,
            max_value=max_allowed,
            value=default_expl,
        )
        run_button = st.button("Run Analysis", type="primary")

    if run_button:
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        if not tickers:
            st.warning("Please enter at least one ticker.")
            return
        if start_date >= end_date:
            st.warning("Start date must be before end date.")
            return

        tabs = st.tabs(tickers)
        for tab, tk in zip(tabs, tickers):
            with tab:
                with st.spinner(f"Running SPA pipeline for {tk}..."):
                    result = cached_run_spa_for_single_ticker(
                        ticker=tk,
                        start=str(start_date),
                        end=str(end_date),
                        window_days=int(window_days),
                        max_news_items=50,
                        fetch_events=fetch_events,
                        generate_explanations=generate_explanations,
                        max_explained_runs=int(max_explained_runs),
                    )
                render_results_for_ticker(
                    ticker=tk,
                    result=result,
                    start_date=start_date,
                    end_date=end_date,
                    fetch_events=fetch_events,
                    generate_explanations=generate_explanations,
                )


def render_results_for_ticker(
    ticker: str,
    result: dict,
    start_date: date,
    end_date: date,
    fetch_events: bool,
    generate_explanations: bool,
) -> None:
    """Render summary, runs, chart, events, and explanations for a single ticker."""
    if result.get("error"):
        st.error(result["error"])
        return

    prices: pd.DataFrame = result["prices"]
    runs: pd.DataFrame = result["runs"]
    events = result["events"]
    correlations = result["correlations"]
    explanations = result["explanations"]
    if result.get("explanation_error"):
        st.warning(result["explanation_error"])

    st.subheader("Summary")
    st.write(
        f"**Ticker:** {ticker}  |  **Date range:** {start_date} → {end_date}  |  "
        f"**Runs detected:** {len(runs)}  |  **Events fetched:** {len(events)}"
    )

    if runs is None or runs.empty:
        st.info("No runs detected for the selected window.")
        return

    st.subheader("Detected Runs")
    st.dataframe(runs)

    if prices is not None and not prices.empty:
        st.subheader("Price with Runs and Events")
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                plot_price_with_runs_and_events(
                    df=prices,
                    runs_df=runs,
                    events_by_run=correlations if fetch_events else {},
                    output_path=tmpfile.name,
                )
                st.image(tmpfile.name, width="stretch", caption="Price with runs and events")
        except Exception as exc:
            st.warning(f"Could not render chart: {exc}")

    if fetch_events and events:
        st.subheader("Events (normalized)")
        events_df = pd.DataFrame(events)
        st.dataframe(events_df)

    if generate_explanations and explanations:
        st.subheader("Explanations (historical-only)")
        for entry in explanations:
            header = f"Run {entry.get('run_id')} ({entry.get('start')} → {entry.get('end')})"
            with st.expander(header, expanded=False):
                st.markdown(
                    f"- Direction: {entry.get('direction')}\n"
                    f"- Duration (bars): {entry.get('duration_bars')}\n"
                    f"- Pct change: {entry.get('pct_change')}\n"
                    f"- Max drawdown: {entry.get('max_drawdown_pct')}"
                )
                st.markdown(entry.get("explanation") or "_No explanation generated_")

    # Downloads
    st.subheader("Export")
    st.download_button(
        label="Download runs as CSV",
        data=runs.to_csv(index=False),
        file_name=f"{ticker}_runs.csv",
        mime="text/csv",
    )

    if fetch_events and events:
        st.download_button(
            label="Download events as JSON",
            data=json.dumps(events, default=str, indent=2),
            file_name=f"{ticker}_events.json",
            mime="application/json",
        )
        st.download_button(
            label="Download correlations as JSON",
            data=json.dumps(correlations, default=str, indent=2),
            file_name=f"{ticker}_correlations.json",
            mime="application/json",
        )

    if generate_explanations and explanations:
        md_lines = [f"# Explanations for {ticker}", ""]
        for entry in explanations:
            md_lines.append(f"## Run {entry.get('run_id')} ({entry.get('start')} → {entry.get('end')})")
            md_lines.append(
                f"- Direction: {entry.get('direction')}\n"
                f"- Duration (bars): {entry.get('duration_bars')}\n"
                f"- Pct change: {entry.get('pct_change')}\n"
                f"- Max drawdown: {entry.get('max_drawdown_pct')}\n"
            )
            md_lines.append(entry.get("explanation") or "_No explanation generated_")
            md_lines.append("")
        md_content = "\n".join(md_lines)
        st.download_button(
            label="Download explanations as Markdown",
            data=md_content,
            file_name=f"{ticker}_explanations.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
