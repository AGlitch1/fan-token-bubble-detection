# Fan-Token Bubble Detection

Reproducible Phase 2 data pipeline for the FRAM group project **“Bubble Detection and Dating in Fan Tokens: A SADF/BSADF, Change-Point and Bayesian Time-Series Analysis.”**

This repository covers data specification, collection, cleaning, validation, and preliminary analysis. Formal SADF/GSADF and BSADF date-stamping, change-point detection, and Bayesian modelling are the next stage and are intentionally not presented as completed results here.

## Current deliverables

- A fixed sample of 20 sports fan tokens.
- Bitcoin, Ethereum, and Chiliz market benchmarks.
- Daily UTC prices and reported volume through **2026-09-19**, the last complete day before collection.
- An analysis-ready unbalanced panel, data-quality report, data dictionary, validation tables, descriptive statistics, diagnostics, correlations, and chart data.
- A formatted Excel review workbook in `outputs/FRAM_PHASE2_DATA_ANALYSIS.xlsx`.
- A report-ready draft in `outputs/DATA_DESCRIPTION_AND_PRELIMINARY_ANALYSIS.md`.
- Phase 1 and literature-review reference files under `references/`.

## Quick start

Python 3.11 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run_pipeline.py --offline
python scripts/check_outputs.py
```

`--offline` reuses the archived downloads already stored locally. To refresh every provider request, run:

```bash
python scripts/run_pipeline.py
```

An optional CoinGecko key can be provided through `COINGECKO_API_KEY`. Never commit API keys or `.env` files.

Equivalent shortcuts are available through `make install`, `make data`, `make offline`, and `make check`.

The Python workflow regenerates all CSV, JSON, and Markdown analysis outputs. The formatted workbook is included as a stable deliverable. `scripts/build_workbook.mjs` can rebuild it inside a Codex workspace that provides `@oai/artifact-tool`; outside that environment, treat the CSV outputs as the portable source of truth.

## Repository layout

```text
fan-token-bubble-detection/
├── config/                 Fixed sample and pipeline settings
├── data/
│   ├── raw/                Provider responses, request log, and sample registry
│   ├── clean/              Analysis-ready daily panels
│   ├── quality/            Quality, validation, dictionary, and review files
│   └── analysis/           Descriptive tables, diagnostics, and chart data
├── docs/                   Workflow and repository conventions
├── outputs/                Final workbook, report draft, and selected figures
├── references/             Phase 1 and literature-review inputs
├── scripts/                Collection, cleaning, validation, and analysis code
├── tests/                  Output-level data integrity tests
├── Makefile
├── pyproject.toml
└── requirements.txt
```

Large raw provider files and generated clean panels are deliberately excluded from Git by `.gitignore`, although the current local repository contains them. A fresh clone can recreate them by running the pipeline. Small sample-defining snapshots, manifests, quality outputs, and analysis tables remain version-controlled.

## Fixed data design

- **Sample:** 20 eligible sports-team or national-team fan tokens selected from the fixed CoinGecko fan-token category snapshot.
- **Screening:** FIGHT is excluded for insufficient history; BlockchainSpace is excluded because it is not a sports fan token; Portugal is the next eligible replacement.
- **Frequency:** daily observations on a UTC calendar.
- **Currency:** US dollars.
- **Panel:** unbalanced; a token enters on its first valid trading date.
- **Primary key:** `asset_id` and `date_utc`. Tickers are display labels only.
- **Return:** 100 multiplied by the one-day change in natural log price.
- **Missing observations:** retained and flagged; prices are never forward-filled.
- **Extreme observations:** flagged above an absolute 100-percentage-point log return but never automatically deleted or winsorized.
- **Cross-source audit:** recent provider prices are compared with CoinGecko, allowing a one-day boundary shift.

The sample snapshot uses CoinGecko's `/coins/markets` endpoint. Historical validation uses `/coins/{id}/market_chart/range`. Full daily OHLC and reported volume are archived from the Yahoo Finance chart service; its use and limitations are recorded in the source manifest.

## Pipeline

1. `collect_data.py` downloads and archives source responses and creates the sample and request manifests.
2. `clean_validate.py` standardizes dates and numeric types, checks uniqueness and price validity, creates the daily calendar, computes transformations, and produces review queues.
3. `preliminary_analysis.py` generates descriptive statistics, volatility measures, autocorrelation diagnostics, return correlations, benchmark correlations, and chart-ready monthly series.
4. `run_pipeline.py` executes the stages in order.
5. `check_outputs.py` verifies the core sample and data-integrity invariants.

See `docs/DATA_WORKFLOW.md` for decision gates and expected outputs.

## Required review before econometric modelling

1. Resolve every `REVIEW` row in `data/quality/cross_source_validation.csv`.
2. Work through `data/quality/extreme_return_review.csv`, preserving the original raw data and documenting each keep, correct, or exclude decision.
3. Freeze the sample, cutoff date, and any approved correction log.
4. Run SADF/GSADF and BSADF date-stamping on log prices, followed by change-point and Bayesian robustness analysis.

Preliminary statistics describe distributional shape, volatility clustering, and co-movement. They do not establish the existence or timing of speculative bubbles.

## Related local material

The reconstructed methodology-paper repository remains separate at:

```text
../method_replication/Green-Bubbles-A-Four-Stage-Paradigm-for-Detection-and-Propagation
```

Keeping the two repositories separate avoids a nested Git history and preserves the original replication materials unchanged.

## License and data terms

No open-source license has been assigned to this group project. Before publishing the repository, the group should select a license and confirm that redistribution of downloaded market data complies with each provider's terms.
