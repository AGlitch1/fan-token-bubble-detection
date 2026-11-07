write_report <- function(data, started) {
  tests <- read_table("Results/psy_test_summary.csv")
  ep <- read_table("Results/psy_euphoric_episodes.csv")
  cp <- read_table("Results/ks_cpm_change_points.csv")
  acc <- read_table("Results/forecast_accuracy.csv")
  pred <- read_table("Results/expanding_window_forecasts.csv")
  status <- data.frame(section = c("Daily data reconstruction", "Monthly exuber RADF/BSADF", "Monthly KS-CPM", "Weekly KS-CPM robustness",
    "Benchmark Johansen/VECM and VAR", "Expanding-window ARIMA and BSTS", "Search-interest ARIMAX and density comparison", "Financial-stress propagation", "Paper simulation appendix"),
    status = c(rep("COMPLETED", 6), if (any(pred$model == "ARIMAX_t")) "ARIMAX_COMPLETED_DENSITY_PENDING_EXTERNAL_PHASE_LABELS" else "UNAVAILABLE_INPUT", "UNAVAILABLE_INPUT", "ORIGINAL_CODE_AND_DATA_INCLUDED"),
    detail = c("Rebuilt from archived provider JSON using R", "Price levels; package Monte Carlo critical sequences",
      "Nonparametric sequential distribution-change model", "Weekly mean prices with ARL0=5000",
      "Adapted token/BTC/CHZ system; does not measure financial stress",
      "Paper package specifications and 1000 BSTS MCMC draws",
      "No fan-token Google Trends dataset supplied; no synthetic values used",
      "No FSI series supplied; no market benchmark relabeled as financial stress",
      "Original-paper/Code-and-Data/Code.Rmd preserves the original appendix; not rerun for fan-token results"))
  write_table(status, "Results/paper_extension_status.csv")
  lines <- c("FAN-TOKEN R REPLICATION: GENERATED RESULTS", "",
    paste("Generated (UTC):", format(Sys.time(), tz = "UTC", usetz = TRUE)),
    paste("R:", R.version.string), paste("Elapsed minutes:", round(as.numeric(difftime(Sys.time(), started, units = "mins")), 2)), "",
    sprintf("Frozen sample: %d fan tokens and %d benchmarks.", length(unique(data$daily$asset_id[data$daily$asset_type == "fan_token"])), length(unique(data$daily$asset_id[data$daily$asset_type == "benchmark"]))),
    sprintf("Daily calendar rows: %d. Valid observed prices: %d.", nrow(data$daily), sum(data$daily$valid_price_flag)),
    paste("Daily cutoff:", config$cutoff_date, "| Last complete modeled month:", max(data$monthly$date)),
    sprintf("GSADF rejections at 95%%: %d of %d eligible token blocks.", sum(tests$reject_95[tests$test == "GSADF"]), sum(tests$test == "GSADF")),
    sprintf("Package-dated 95%% euphoric episodes: %d. Monthly KS change points: %d.", nrow(ep), nrow(cp)),
    sprintf("Forecasts per model: %d; token-specific holdouts range from %d to %d months.", sum(pred$model == "ARIMA"), min(acc$forecasts), max(acc$forecasts)), "",
    "Forecast accuracy (median across assets; log-price RMSE and USD-price SMAPE):")
  for (name in unique(acc$model)) {
    z <- acc[acc$model == name, ]
    lines <- c(lines, sprintf("  %s: median log RMSE %.6f; median price SMAPE %.3f%%", name, median(z$rmse_log_price), median(z$smape_price_pct)))
  }
  lines <- c(lines, "", "INTERPRETATION AND LIMITS", "BSADF identifies statistical explosiveness, not a complete economic bubble life cycle.",
    "KS-CPM identifies distribution changes. Formation/burst/decline labels are not inferred automatically.",
    "Shorter fan-token histories require rescaled startup and forecast training windows (see Methodology.txt).",
    "Benchmark propagation uses BTC and CHZ, not the paper's financial-stress and oil variables.",
    "Johansen/VECM tables are conditional diagnostics; consult the unit-root tests before interpreting cointegration.",
    "No fan-token Google Trends or financial-stress dataset was supplied; affected paper claims remain unavailable.",
    "The legacy Python analysis is archived for provenance and is not the source of these R statistics.",
    "All numbers in this report are generated from the R result tables.", "", "METHOD STATUS", capture.output(print(status, row.names = FALSE)), "", "VALIDATION", tail(readLines("Results/validation.txt"), 1))
  writeLines(lines, "Results/Paper-extensions-summary.txt")
  writeLines(lines, "../Working-paper/Paper-extensions-results.txt")
  capture.output(sessionInfo(), file = "Results/sessionInfo.txt")
  installed <- as.data.frame(installed.packages()[, c("Package", "Version", "Built"), drop = FALSE])
  write_table(installed, "Results/installed_packages.csv")
  # Portable SHA-256 inventory includes the complete deliverable, raw inputs and source.
  write_inventory()
}

write_inventory <- function() {
  files <- list.files("..", recursive = TRUE, full.names = TRUE, all.files = TRUE)
  files <- files[!dir.exists(files) & !grepl("/\\.R-library/|/MANIFEST_SHA256.csv$", files)]
  inventory <- data.frame(path = sub("^\\.\\./", "", files), bytes = file.info(files)$size,
    sha256 = vapply(files, digest::digest, character(1), algo = "sha256", file = TRUE, serialize = FALSE))
  write_table(inventory, "../MANIFEST_SHA256.csv")
}
