FAN TOKEN BUBBLE DETECTION
==========================

1. Overview
-----------
This repository provides a reproducible R workflow for detecting and dating
explosive price behaviour in sports fan tokens. The analysis combines recursive
right-tailed unit-root tests, sequential distribution-change detection, Bayesian
local-ADF diagnostics and comparisons with cryptocurrency benchmarks.

The repository contains raw provider archives, processed datasets, source code,
statistical outputs, figures and an executable R Markdown notebook. The methods
are informed by Vriz and Grossi (2026), with specifications for daily fan-token
data documented below.

2. Data and sample
------------------
The sample comprises 20 sports-team and national-team fan tokens selected from
a fixed CoinGecko category snapshot dated 20 September 2026. Bitcoin (BTC),
Ethereum (ETH) and Chiliz (CHZ) serve as market benchmarks. The same asset
selection is applied to both estimation windows:

  Primary sample endpoint:    30 June 2026
  Extended sample endpoint:   19 September 2026

Observations are daily and denominated in US dollars. Timestamps follow the
UTC calendar. The panel is unbalanced: each asset enters on its first valid
trading date. Provider histories begin no earlier than 1 January 2019.

Code-and-Data/Raw-data/ contains the archived Yahoo Finance chart responses,
CoinGecko category and validation responses, sample registry, request manifest,
collection summary and consolidated market-data files. Daily adjusted closing
prices are the principal model input. Open, high, low and reported trading
volume are retained for diagnostics and descriptive analysis.

All analysis inputs are supplied locally. Estimation uses the archived data
without requiring live provider requests or API credentials.

3. Repository structure
-----------------------
Code-and-Data/
  Code.Rmd                       Main executable analysis notebook
  Code.html                      Rendered results and diagnostic figures
  run_all.R                      Complete data-processing and analysis workflow
  install_packages.R             Package installation with specified versions
  render_report.R                Figure generation and HTML rendering
  validate_outputs.R             Validation entry point
  verify_manifest.R              SHA-256 file verification
  R/                             Processing, estimation and reporting functions
  Configuration/                 Sample definitions, review decisions and settings
  Raw-data/                      Archived provider responses and input manifests
  Processed-data/                Clean panels and estimation datasets
  Economic variables/            Monthly asset datasets for supplementary analysis
  Results/Report-aligned/         Primary daily estimation outputs
  Figures/Report-aligned/         Daily diagnostic figures
  Results/RESULTS.txt             Generated results summary
  Results/method_status.csv       Analysis coverage and model status
  Paper-extensions.Rmd            Supplementary methodology notebook
  run_paper_extensions.R          Supplementary analysis entry point
Working-paper/                   Methodology references and research documentation
Original-paper/                  Reference study source code, data and license
Provenance/runtime_image.txt     Recorded container environment
FanToken.Rproj                   RStudio project configuration
run_docker.sh                    Container execution wrapper
MANIFEST_SHA256.csv              File inventory, sizes and SHA-256 checksums

Paths in the following sections are relative to the directory containing this
README.txt file.

4. Software requirements and installation
----------------------------------------
The validated environment uses R 4.5.2. The primary analysis requires:

  exuber       1.1.0
  cpm          2.3
  jsonlite     2.0.0
  digest       0.6.39

HTML rendering requires knitr 1.50, rmarkdown 2.30 and Pandoc. Supplementary
modules use bsts 0.9.11, forecast 8.24.0, urca 1.3-4, vars 1.6-1, multDM 1.1.5,
MCS 0.1.3 and Metrics 0.1.4.

Container installation

Docker and Bash are required for the supplied container workflow. The following
image identifies the validated environment:

  gianvriz/green_bubbles@sha256:39586b764cbd2260aa0dbeed20cd16dd87b0833e97e6ce5210ae5f101af9c251

If the image is unavailable locally, download it before running the analysis:

  docker pull gianvriz/green_bubbles@sha256:39586b764cbd2260aa0dbeed20cd16dd87b0833e97e6ce5210ae5f101af9c251

Native R installation

Install R 4.5.2 and the system development libraries required to compile its
packages, then execute:

  Rscript Code-and-Data/install_packages.R

The installer creates a repository-local .R-library directory and installs the
specified package versions. Initial installation requires internet access.
The container supplies the recorded package and system dependency environment.

5. Data preparation
-------------------
R/01_process_data.R performs the following operations:

1. Parse archived provider responses and standardize UTC dates and numeric fields.
2. Apply the study date range and check duplicate asset-date records, rejecting
   conflicting duplicate prices.
3. Construct an individual daily calendar for each asset and flag missing or
   nonpositive prices, zero reported volume and extreme returns.
4. Calculate natural log prices, adjacent-day log returns, indexed prices,
   log-transformed trading volume and rolling volatility.
5. Export the complete daily panel and the subset containing valid observed prices.
6. Create independent daily estimation snapshots for each sample endpoint.
7. Generate monthly and weekly arithmetic mean prices for supplementary analyses.

Daily returns equal 100 times the change in natural log adjusted price. Returns
are calculated only between consecutive valid trading days. Rolling volatility
uses a 30-day standard deviation with at least 20 valid return observations,
annualized using 365 days. Missing prices remain unfilled, and extreme returns
are retained with their review records. Model inputs are divided into contiguous
blocks where gaps occur.

6. Statistical methods
----------------------
Recursive tests and persistence

SADF, GSADF and BSADF statistics are estimated with exuber::radf on daily log
adjusted prices. The regression includes an intercept and zero lagged
differences. For a series containing n prices, the minimum price window is:

  max(20, floor((0.01 + 1.8 / sqrt(n)) * n))

The exuber minw argument is one observation smaller because it counts regression
rows. Reference values are read from Configuration/reported_reference_values.csv
and interpolated or extrapolated linearly. Endpoint dating uses an SADF-based
reference approximation. Resulting classifications are nominal reference-threshold
exceedances; their interpretation is subject to this calibration approximation.

A retained interval requires at least 30 consecutive daily BSADF exceedances of
the 95% dating reference. Threshold failures and calendar gaps separate intervals.
Outputs include interval dates, duration, peak statistic, price change and an
indicator for intervals continuing at the sample endpoint.

Sequential distribution-change detection

Daily log returns are analysed using cpm::processStream with the
Kolmogorov-Smirnov statistic. Initialization uses the greater of 30 observations
and 20% of the return sample, rounded upward. The primary in-control average run
length is 500 observations; a value of 1000 provides a sensitivity specification.
Estimated change dates and subsequent detection dates are reported separately.

Bayesian local-ADF diagnostics

The Bayesian model uses normal coefficient priors, a slope-prior standard
deviation of 0.5, standardized innovation variance fixed at one and an expected
run length of 365 days. Outputs include posterior reset probabilities,
positive-slope probabilities and expected run lengths. Standardization uses the
full estimation sample within each cutoff; these diagnostics are retrospective.

Benchmark comparisons

Daily return correlations are calculated between each fan token and BTC, ETH
and CHZ within each sample window. Statistical classifications and posterior
probabilities characterize price behaviour; economic interpretation also
requires consideration of price direction and market context.

7. Execution
------------
Run the complete workflow from the directory containing this README:

  bash run_docker.sh

The native R equivalent is:

  Rscript Code-and-Data/run_all.R

The workflow processes the archived inputs, estimates both sample windows,
validates the results and writes the summary and checksum inventory. The
container runs with networking disabled and writes files under the current
host user's identity. Regeneration replaces derived datasets and outputs.

R entry points resolve paths relative to their script location and may also be
invoked using absolute paths. For an interactive session, open FanToken.Rproj,
set the working directory to Code-and-Data and execute source("run_all.R").

Analysis parameters are defined in:

  Code-and-Data/Configuration/analysis_config.R

8. Results and report generation
-------------------------------
Processed-data/clean_daily_panel.csv contains the complete daily calendar panel.
Processed-data/clean_observed_panel.csv contains valid observed prices.
The two estimation snapshots are:

  Processed-data/daily_panel_2026-06-30.csv
  Processed-data/daily_panel_2026-09-19.csv

Primary statistical outputs are stored in Code-and-Data/Results/Report-aligned/:

  psy_test_summary.csv             Recursive statistics, windows and reference flags
  psy_bsadf_series.csv             Daily BSADF statistics and dating references
  psy_persistent_intervals.csv     Retained intervals and associated price changes
  ks_cpm_change_points.csv         Change and detection dates for both ARL settings
  bayesian_local_adf.csv           Posterior probabilities and run-length estimates
  benchmark_return_correlations.csv
                                   Token correlations with BTC, ETH and CHZ
  sample_comparison.csv            Comparison across the two sample endpoints
  daily_radf_models.rds            Estimated recursive-test model objects
  RESULTS.txt                     Generated summary and methodological qualifications
  validation.txt                  Validation checks and their outcome
  sessionInfo.txt                 Recorded R session information

Figures are stored in Code-and-Data/Figures/Report-aligned/. Each diagnostic
figure displays the asset's price, BSADF sequence and Bayesian slope probability.

After estimation, generate the HTML report with:

  bash run_docker.sh render_report.R

Native R equivalent:

  Rscript Code-and-Data/render_report.R

Open Code-and-Data/Code.html to inspect the results and embedded figures.
Rendering uses the exported estimates and refreshes the checksum inventory.

9. Validation and reproducibility
--------------------------------
Execute the validation checks independently with:

  bash run_docker.sh validate_outputs.R

Native R equivalent:

  Rscript Code-and-Data/validate_outputs.R

Validation covers sample composition, daily calendars, price transformations,
recursive-test statistics, endpoint indexing, interval persistence, Bayesian
probabilities and benchmark coverage. Numerical consistency is checked against
the reference datasets and saved R model objects.

Verify the packaged file inventory with:

  bash run_docker.sh verify_manifest.R

Native R equivalent:

  Rscript Code-and-Data/verify_manifest.R

MANIFEST_SHA256.csv records relative paths, file sizes and SHA-256 hashes. The
manifest excludes itself and the local .R-library directory. Changes to inputs
or analysis settings require regeneration of the results and rendered report
before the file inventory is verified.

The container identity is recorded in Provenance/runtime_image.txt. R session
and package inventories accompany the outputs. Supplementary simulation seeds
and estimation settings are specified in Configuration/analysis_config.R.

10. Supplementary analyses
-------------------------
Additional modules provide monthly and weekly detection, ARIMA and Bayesian
structural time-series forecasts, and benchmark Johansen/VECM analysis.
Execute these modules explicitly with:

  bash run_docker.sh run_paper_extensions.R
  bash run_docker.sh render_paper_extensions.R

Their notebook is Code-and-Data/Paper-extensions.Rmd, the rendered output is
Code-and-Data/Paper-extensions.html, and the results summary is
Code-and-Data/Results/Paper-extensions-summary.txt. Detailed instructions are
provided in README-paper-extensions.txt.

The complete source, data and simulation notebook for the reference study are
included in Original-paper/Code-and-Data/Code.Rmd. Methodological specifications
and research documentation are provided in Working-paper/.

11. Reference and licensing
--------------------------
Vriz, G. L., and Grossi, L. (2026). Green bubbles: A four-stage paradigm for
detection and propagation. Energy Economics, 154, 109095.
DOI: https://doi.org/10.1016/j.eneco.2025.109095
Source repository:
https://github.com/GianVriz/Green-Bubbles-A-Four-Stage-Paradigm-for-Detection-and-Propagation
Archived revision: 88dbf4d6f07c61567ae65c81dbe4df9f5ee52a20.

The reference code is copyright (c) 2025 Gian Luca Vriz and is distributed under
the MIT License. The license is retained in LICENSE-original.txt and
Original-paper/LICENSE. Publications and provider datasets remain subject to
their respective ownership and usage terms.
