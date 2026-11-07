# Explicit adaptations to the shorter fan-token histories. See Working-paper/Methodology.txt.
config <- list(
  start_date = as.Date("2019-01-01"), cutoff_date = as.Date("2026-09-19"),
  report_cutoffs = as.Date(c("2026-06-30", "2026-09-19")),
  report_min_observations = 365L, report_episode_days = 30L,
  report_ks_startup_fraction = 0.20, report_ks_minimum_startup = 30L,
  report_ks_arl0 = 500L, report_ks_sensitivity_arl0 = 1000L,
  report_bayesian_hazard_days = 365L, report_bayesian_slope_prior_sd = 0.5,
  fan_token_count = 20L, monthly_min_observations = 30L,
  critical_value_replications = 1000L, critical_value_seed = 4L,
  monthly_arl0 = 500L, weekly_arl0 = 5000L,
  startup_fraction = 0.20, minimum_startup = 20L,
  forecast_holdout = 37L, forecast_min_training = 36L,
  bsts_iterations = 1000L, bsts_seed = 9L,
  mcs_replications = 5000L, mcs_alpha = 0.15,
  # BENCHMARK propagation, not a financial-stress proxy or the paper's FSI result.
  propagation_benchmarks = c("bitcoin", "chiliz")
)
