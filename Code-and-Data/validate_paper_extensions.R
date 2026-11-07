#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
source("R/common.R")
checks <- character()
assert <- function(condition, description) {
  if (!isTRUE(condition)) stop("VALIDATION FAILED: ", description)
  checks <<- c(checks, paste("PASS", description))
}
d <- read_table("Processed-data/clean_daily_panel.csv")
d$date_utc <- as.Date(d$date_utc)
assert(!anyDuplicated(d[c("asset_id", "date_utc")]), "unique daily asset/date keys")
assert(length(unique(d$asset_id[d$asset_type == "fan_token"])) == 20L, "20 fan tokens")
assert(length(unique(d$asset_id[d$asset_type == "benchmark"])) == 3L, "3 benchmarks")
assert(all(d$date_utc <= config$cutoff_date), "frozen data cutoff is respected")
assert(!any(d$valid_price_flag & (!is.finite(d$close_usd) | d$close_usd <= 0)), "positive finite prices in analysis")
for (g in split(d, d$asset_id)) {
  assert(all(diff(g$date_utc) == 1), paste(g$asset_id[1], "has a complete daily calendar"))
  valid_return <- g$valid_price_flag & c(FALSE, head(g$valid_price_flag, -1))
  expected <- c(NA_real_, diff(g$log_price)) * 100
  assert(all(is.na(g$return_pct[!valid_return])), paste(g$asset_id[1], "does not compute returns across missing prices"))
  assert(isTRUE(all.equal(g$return_pct[valid_return], expected[valid_return], tolerance = 1e-10)), paste(g$asset_id[1], "log returns agree with price differences"))
}
legacy <- read_table("../Provenance/Legacy-Python/clean/clean_daily_panel.csv")
legacy$date_utc <- as.Date(legacy$date_utc)
key <- function(x) paste(x$asset_id, x$date_utc)
ix <- match(key(d), key(legacy))
assert(nrow(d) == nrow(legacy) && !anyNA(ix), "R rebuild recovers every legacy daily panel key")
for (col in c("open_usd", "high_usd", "low_usd", "close_usd", "adj_close_usd", "volume_reported", "log_price", "return_pct", "indexed_price_100", "rolling_volatility_30d_pct_annualized"))
  assert(isTRUE(all.equal(d[[col]], legacy[[col]][ix], tolerance = 1e-8, check.attributes = FALSE)), paste("R reconstruction agrees with archived Python data for", col))
m <- read_table("Processed-data/monthly_panel.csv")
assert(!anyDuplicated(m[c("asset_id", "date")]), "unique monthly asset/date keys")
assert(all(as.Date(m$period_end) <= config$cutoff_date), "no unfinished final month is modeled")
for (i in seq_len(nrow(m))) {
  z <- d[d$asset_id == m$asset_id[i] & format(d$date_utc, "%Y-%m") == substr(m$date[i], 1, 7), ]
  expected <- if (all(z$valid_price_flag)) mean(z$close_usd) else NA_real_
  assert(isTRUE(all.equal(m$close[i], expected, tolerance = 1e-10)), paste("monthly arithmetic mean", m$asset_id[i], m$date[i]))
}
ts <- read_table("Results/psy_test_summary.csv")
assert(length(unique(ts$asset_id)) == 20L, "all 20 fan tokens have R recursive ADF results")
assert(all(ts$replications == 1000L), "critical sequences use 1000 Monte Carlo replications")
cp <- read_table("Results/ks_cpm_change_points.csv")
assert(all(as.Date(cp$detection_date) >= as.Date(cp$first_post_change_date)), "KS detection times follow estimated changes")
seq <- read_table("Results/psy_bsadf_series.csv")
assert(all(seq$above_95 == (seq$bsadf > seq$critical_95)), "BSADF exceedance flags match endpoint-specific critical values")
pred <- read_table("Results/expanding_window_forecasts.csv")
assert(length(unique(pred$asset_id)) == 20L, "all 20 fan tokens have forecast outputs")
assert(all(as.Date(pred$forecast_origin) < as.Date(pred$date)), "forecasts use earlier training origins")
assert(all(is.finite(pred$forecast_log_price)) && all(pred$lower_95_log <= pred$upper_95_log), "forecasts and uncertainty bounds are valid")
assert(all(pred$training_observations >= config$forecast_min_training), "forecast minimum training history is respected")
# Replay package computations for one asset to check indexing and exports, not just file existence.
models <- readRDS("Results/detection_models.rds")
first <- models[[1]]
id <- sub("_[0-9]+$", "", names(models)[1])
export <- seq[seq$asset_id == id & seq$block == 1, ]
assert(isTRUE(all.equal(export$bsadf, as.numeric(first$radf$bsadf), tolerance = 1e-12)), "exported BSADF statistics equal saved exuber model")
assert(identical(as.character(export$date), as.character(tail(first$dates, nrow(export)))), "BSADF dates align with package minimum-window truncation")
writeLines(c("R REPLICATION VALIDATION", checks, sprintf("%d checks passed.", length(checks))), "Results/validation.txt")
message(length(checks), " validation checks passed")
