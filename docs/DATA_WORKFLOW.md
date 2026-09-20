# Data workflow and decision gates

## 1. Freeze the specification

The active specification is stored in `config/project_config.json`. The candidate registry is stored in `config/candidate_tokens.csv`. Any change to the sample, cutoff, eligibility rules, or return construction must be made in configuration and documented before the pipeline is rerun.

**Gate:** exactly 20 eligible fan tokens must have at least 365 valid daily prices.

## 2. Collect and preserve raw inputs

Run `python scripts/run_pipeline.py` to refresh the data. The collector archives each provider response before any cleaning and writes `data/raw/request_manifest.csv` so the group can identify the exact request used for each series.

**Gate:** every included asset and benchmark must have a successful request entry. Never manually edit a raw provider response.

## 3. Clean without hiding uncertainty

The cleaning stage:

- converts timestamps to UTC dates;
- enforces an `asset_id` + `date_utc` key;
- retains the latest timestamp if a date is duplicated and reports conflicts;
- rejects non-positive prices from logarithmic transformations;
- creates a complete daily calendar from the first valid observation;
- leaves missing prices empty rather than forward-filling;
- calculates returns only across consecutive valid calendar days;
- flags extreme returns without deleting them; and
- calculates 30-day rolling volatility annualized by the square root of 365.

**Gate:** resolve any `REVIEW` series in `data/quality/data_quality_report.csv` before modelling.

## 4. Cross-validate and review outliers

The validation stage compares a recent audit sample with CoinGecko after testing date shifts of -1, 0, and +1 days. PASS requires:

- at least 100 matched days;
- price correlation of at least 0.95;
- median absolute relative difference no greater than 5%; and
- 95th-percentile absolute relative difference no greater than 15%.

An isolated disagreement is a reason to investigate, not an automatic reason to discard the observation. Record decisions in the review files and preserve the original values.

**Gate:** every cross-source `REVIEW` and every row in `extreme_return_review.csv` must have a documented decision.

## 5. Preliminary analysis

The analysis stage produces:

- sample and coverage summaries;
- distributional statistics for daily log returns;
- 30-day rolling-volatility summaries;
- return and absolute-return autocorrelations at lags 1, 5, and 10;
- fan-token correlations with BTC, ETH, and CHZ;
- the full return-correlation matrix; and
- monthly chart series for the five largest eligible fan tokens at the fixed snapshot.

**Gate:** describe the results as preliminary evidence only. Do not label a price path as a bubble until formal explosive-root and date-stamping tests have been completed.

## 6. Reproducibility checks

Run:

```bash
python scripts/check_outputs.py
```

The check fails if the sample size changes, primary keys are duplicated, non-positive analysis prices appear, the cutoff differs from the fixed design, or the extreme-return queue no longer agrees with the clean panel.
