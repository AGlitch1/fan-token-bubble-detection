# Phase 3 formal time-series analysis

## Scope

Phase 3 runs on the fixed, quality-reviewed daily panel created in Phase 2. It analyzes each uninterrupted daily log-price block with at least 365 observations. Fan tokens are the main study sample; BTC, ETH, and CHZ are included as benchmarks. Gaps split a price series into separate blocks, so the procedures do not bridge missing calendar days.

## Recursive right-tailed ADF tests

Let yₜ be the natural logarithm of the USD closing price. Each recursive window estimates

Δyₜ = α + βyₜ₋₁ + εₜ

with an intercept and zero lagged differences. The right-tailed alternative is β > 0, which corresponds to an explosive autoregressive root in levels. The SADF recursion fixes the starting point at the beginning of a block; the BSADF recursion varies the starting point at each endpoint; GSADF is the maximum BSADF statistic over the block.

The minimum window follows the PSY rule r₀ = 0.01 + 1.8 / √T, rounded down to a number of price observations. This implementation uses the finite-sample SADF and GSADF critical values published in Table 1 of Phillips, Shi, and Yu (2015), with linear interpolation by sample length. It uses the SADF critical-value path for BSADF date-stamping and requires an episode to last at least 30 calendar days (or ceil(log(T)), if longer). The published table uses 2,000 simulations; this implementation does not regenerate those draws or run an asset-specific bootstrap. For date-stamping, the recursion retains the full-block minimum window while the SADF critical-value sequence is interpolated by endpoint sample length. Values outside the table's sample-size range are linearly extrapolated, so results near a critical value should be treated as approximate. The paper discusses the recommended window rule, multiple-bubble dating, and the lag-zero specification used here. [Phillips, Shi, and Yu (2015)](https://onlinelibrary.wiley.com/doi/10.1111/iere.12132)

The reported rejection flags are statistical evidence against a unit root in favor of an explosive alternative. A rejection alone does not establish the cause of the price movement.

## Change-point analysis

An exact penalized dynamic-programming segmentation is run separately on (1) standardized daily log returns and (2) log squared standardized returns. The second series is a proxy for changing volatility. Each segment must contain at least 30 observations, and each additional segment pays a 2 log(T) penalty. The outputs are retrospective break locations and segment summaries; no causal interpretation or separate break-date p-value is assigned. The factor of 2 is a conservative penalty for both the additional regime parameter and the searched break location.

## Bayesian online local-ADF model

The Bayesian robustness analysis follows the online run-length recursion of Adams and MacKay (2007). For each uninterrupted price block, it fits the local regression

Δyₜ / sΔ = α + β z(yₜ₋₁) + εₜ

where the response is standardized by the sample standard deviation of daily log changes, and the lagged log price is centered and standardized. The model uses a fixed unit innovation variance in these standardized units, a zero-mean normal prior with intercept variance 4 and slope standard deviation 0.5, and a geometric hazard with a 365-day expected run length. It reports the posterior probability that β is positive, the probability that a new run starts, the posterior mean and standard deviation of β, and the expected run length.

This is a sensitivity model, not an independent bubble test. Its posterior depends on the Gaussian likelihood, fixed standardized innovation variance, prior scale, and hazard setting. [Adams and MacKay (2007)](https://doi.org/10.48550/arXiv.0710.3742)

## Outputs

The pipeline writes these files under data/analysis/:

- psy_test_summary.csv: SADF and GSADF statistics, critical values, and rejection flags.
- psy_bsadf_series.csv: daily SADF/BSADF statistics and each endpoint's maximizing start date.
- psy_bubble_episodes.csv: 10%, 5%, and 1% date-stamped runs that pass the duration rule.
- change_points.csv: detected return-mean and log-volatility changes.
- change_point_segments.csv: segment dates, sizes, mean returns, and annualized volatility.
- bayesian_online_diagnostics.csv: daily Bayesian posterior series.
- phase3_analysis_overview.json and phase3_formal_analysis_summary.md: run counts and a concise narrative.

Run Phase 3 as part of the offline pipeline with python scripts/run_pipeline.py --offline, or rerun only this stage with make phase3.
