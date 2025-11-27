- [ ] Build event/news ingestion and correlation pipeline
  - Related requirement(s): Correlate price runs with public market events; interpretability/practical utility
  - Files/modules to touch (suggested): `src/data/fetch_news.py`, `src/events/correlate.py`, new tests under `tests/events/`
  - High-level description of what needs to be implemented or fixed: Implement fetching of public news/events for tickers and date ranges, and match events to runs within a configurable window; return structured correlations and handle empty/noisy data deterministically.

- [ ] Integrate LLM explanations into the main analysis/reporting flow
  - Related requirement(s): Natural-language summaries via constrained LLMs; interpretability/practical utility
  - Files/modules to touch (suggested): `src/ui/cli.py`, `src/explain/*`, `src/report/charts.py` or new report generator
  - High-level description of what needs to be implemented or fixed: After detecting runs (and correlating events), generate explanations for selected runs and emit them alongside charts/outputs; ensure graceful fallback when LLM is unavailable.

- [ ] Add compliance safeguards for explanations (historical-only, no advice)
  - Related requirement(s): Compliance-safe explanations; explicit NO prediction / NO investment advice
  - Files/modules to touch (suggested): `src/explain/llm_client.py`, `src/explain/prompt_builder.py`, new validation utility/tests
  - High-level description of what needs to be implemented or fixed: Strengthen system/user prompts, set `temperature` to 0, and post-validate LLM output to strip/reject predictive/advisory language; add tests to enforce constraints and include explicit disclaimers in output.

- [ ] Expand documentation and CLI outputs with disclaimers
  - Related requirement(s): Compliance-safe explanations; explicit NO prediction / NO investment advice
  - Files/modules to touch (suggested): `README.md`, `src/ui/cli.py`, any report generation module
  - High-level description of what needs to be implemented or fixed: Add visible disclaimers to CLI/report outputs and docs reinforcing historical-only scope and no investment advice.

- [ ] Implement evaluation harness for AAPL, NVDA, SCHW, PGR
  - Related requirement(s): Evaluation on four equities; reproducibility/practical utility
  - Files/modules to touch (suggested): `scripts/` (new evaluation script), `docs/` for results, possible `tests/`
  - High-level description of what needs to be implemented or fixed: Create repeatable scripts to run the pipeline on the four equities, capture outputs (runs, charts, explanations), and document results.

- [ ] Improve reproducibility and testing
  - Related requirement(s): Deterministic segmentation; interpretability/reproducibility
  - Files/modules to touch (suggested): `src/patterns/runs.py`, new unit tests under `tests/patterns/`, CI config if present
  - High-level description of what needs to be implemented or fixed: Add unit tests for run detection edge cases and determinism; document data-fetch reproducibility constraints (e.g., cache or fixture data for tests).

- [ ] Wire full pipeline end-to-end
  - Related requirement(s): Modular explainable framework; interpretability/practical utility
  - Files/modules to touch (suggested): `src/ui/cli.py`, `src/report/` (new or existing), orchestration module
  - High-level description of what needs to be implemented or fixed: Provide a single entry point that fetches OHLCV, detects runs, correlates events, generates explanations, and produces charts/report artifacts with consistent output structure.

- [ ] Event correlation scoring/visibility in reports
  - Related requirement(s): Correlate price runs with public market events; explainability
  - Files/modules to touch (suggested): `src/events/correlate.py`, `src/report/charts.py` or new report renderer
  - High-level description of what needs to be implemented or fixed: Expose matched events per run in outputs (tabular or annotations), and consider simple relevance scoring or filtering to keep correlations explainable.

- [ ] Add data-source and access documentation
  - Related requirement(s): Operate solely on publicly available OHLCV data; reproducibility/practical utility
  - Files/modules to touch (suggested): `README.md`, `docs/`
  - High-level description of what needs to be implemented or fixed: Document data sources (e.g., Yahoo Finance), rate limits, and how to run offline with cached fixtures to keep behavior reproducible.
