# Phase 3 formal analysis summary

The fixed Phase 2 panel was analyzed through 2026-09-19. Recursive right-tailed ADF statistics were computed for 20 fan-token series and 3 benchmark series. The fan-token GSADF tests reject the unit-root null at 5% for 10 of 20 tokens using interpolated finite-sample PSY critical values.

The 5% BSADF dating procedure returned 2 fan-token episodes that met the 30-day minimum-duration rule:

- POR: 2026-06-15 to 2026-09-19 (97 days; peak BSADF 5.72; ongoing at cutoff)
- ARG: 2026-07-21 to 2026-08-23 (34 days; peak BSADF 2.58; ended)

Penalized dynamic programming identified 150 mean or log-volatility change points across the 20 fan tokens and three benchmarks. The Bayesian online model generated 47,535 daily posterior records. These methods identify statistical patterns; they do not establish the economic cause of an episode.

Critical values and implementation choices are documented in docs/PHASE_3_ANALYSIS.md. For date-stamping, the recursion keeps the full-block minimum window while its endpoint critical values are interpolated from the published SADF table by endpoint length. This is an approximation, not endpoint-specific simulation or a series-specific bootstrap; interpret marginal dates and tests with that limitation in mind.
