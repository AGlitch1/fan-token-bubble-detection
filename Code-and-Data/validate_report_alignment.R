#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(script)) setwd(dirname(normalizePath(script)))
source("R/common.R")
source("R/06_report_alignment.R")
checks <- character()
assert <- function(condition, description) {
  if (!isTRUE(condition)) stop("VALIDATION FAILED: ", description)
  checks <<- c(checks, paste("PASS", description))
}
d <- read_table("Processed-data/clean_daily_panel.csv")
d$date_utc <- as.Date(d$date_utc)
assert(!anyDuplicated(d[c("asset_id", "date_utc")]), "unique daily asset/date keys")
assert(length(unique(d$asset_id[d$asset_type == "fan_token"])) == 20L, "20 fan tokens")
assert(length(unique(d$asset_id[d$asset_type == "benchmark"])) == 3L, "BTC/ETH/CHZ benchmarks retained")
assert(all(d$close_usd == d$adj_close_usd), "archived crypto adjusted prices equal closes used in submitted results")
for (g in split(d, d$asset_id)) {
  assert(all(diff(g$date_utc) == 1), paste(g$asset_id[1], "complete daily calendar"))
  assert(max(abs(g$return_pct[-1] - diff(log(g$adj_close_usd)) * 100), na.rm = TRUE) < 1e-9,
    paste(g$asset_id[1], "returns use adjacent adjusted log prices"))
}
test <- read_table(file.path(report_dir, "psy_test_summary.csv"))
seq <- read_table(file.path(report_dir, "psy_bsadf_series.csv"))
ep <- read_table(file.path(report_dir, "psy_persistent_intervals.csv"))
cp <- read_table(file.path(report_dir, "ks_cpm_change_points.csv"))
bay <- read_table(file.path(report_dir, "bayesian_local_adf.csv"))
models <- readRDS(file.path(report_dir, "daily_radf_models.rds"))
assert(nrow(test) == 46L, "23 assets independently estimated at both cutoffs")
assert(all(seq$above_95 == (seq$bsadf > seq$dating_reference_95)), "daily threshold crossings are exported correctly")
assert(all(ep$duration_days >= 30), "retained intervals satisfy submitted 30-day persistence rule")
assert(all(as.Date(cp$detection_date) >= as.Date(cp$first_post_change_date)), "KS detection occurs after estimated change")
assert(setequal(unique(cp$arl0), c(500, 1000)), "daily KS primary and sensitivity ARLs are present")
assert(all(bay$bayesian_explosive_slope_probability >= 0 & bay$bayesian_explosive_slope_probability <= 1), "Bayesian slope probabilities bounded by zero and one")
for (i in seq_len(nrow(test))) {
  t <- test[i, ]
  key <- paste(t$cutoff_date, t$asset_id, t$block, sep = "_")
  fit <- models[[key]]
  exported <- seq[seq$cutoff_date == t$cutoff_date & seq$asset_id == t$asset_id & seq$block == t$block, ]
  assert(max(abs(exported$bsadf - as.numeric(fit$radf$bsadf))) < 1e-10, paste(key, "export matches actual exuber model"))
  assert(identical(as.character(exported$date_utc), as.character(tail(fit$dates, nrow(exported)))), paste(key, "daily endpoint indexing is correct"))
}
for (cutoff in as.character(config$report_cutoffs)) {
  t <- test[test$cutoff_date == cutoff & test$asset_type == "fan_token", ]
  count <- if (cutoff == "2026-06-30") 37662L else 39282L
  assert(sum(t$observations) == count, paste(cutoff, "fan-token observation count agrees with submitted report"))
  reference_path <- if (cutoff == "2026-06-30") "../Provenance/Legacy-Python/outputs/phase3_report_support/june_test_summary.csv" else "../Provenance/Legacy-Python/analysis/psy_test_summary.csv"
  reference <- read_table(reference_path)
  match_ix <- match(t$asset_id, reference$asset_id)
  assert(max(abs(t$sadf_statistic - reference$sadf_statistic[match_ix])) < 1e-5, paste(cutoff, "R SADF agrees with submitted numerical analysis"))
  assert(max(abs(t$gsadf_statistic - reference$gsadf_statistic[match_ix])) < 1e-5, paste(cutoff, "R GSADF agrees with submitted numerical analysis"))
  assert(sum(t$gsadf_reject_95) == if (cutoff == "2026-06-30") 9L else 10L, paste(cutoff, "GSADF reference counts agree with submitted report"))
  assert(sum(ep$cutoff_date == cutoff & ep$asset_type == "fan_token") == if (cutoff == "2026-06-30") 0L else 2L, paste(cutoff, "persistent-interval counts agree with submitted report"))
}
legacy <- read_table("../Provenance/Legacy-Python/analysis/bayesian_online_diagnostics.csv")
sept <- bay[bay$cutoff_date == "2026-09-19", ]
key <- function(x) paste(x$asset_id, x$date_utc)
ix <- match(key(sept), key(legacy))
assert(nrow(sept) == nrow(legacy) && !anyNA(ix), "Bayesian local-ADF dates agree with submitted September analysis")
assert(max(abs(sept$bayesian_explosive_slope_probability - legacy$bayesian_explosive_slope_probability[ix])) < 2e-7,
  "R Bayesian slope probabilities agree with submitted model within CDF numerical tolerance")
assert(max(abs(sept$bayesian_change_point_probability - legacy$bayesian_change_point_probability[ix])) < 1e-8,
  "R Bayesian reset probabilities agree with submitted model")
corr <- read_table(file.path(report_dir, "benchmark_return_correlations.csv"))
assert(nrow(corr) == 120L && setequal(corr$benchmark, c("bitcoin", "ethereum", "chiliz")), "all fan tokens compared against all three benchmarks at each cutoff")
writeLines(c("REPORT ALIGNMENT VALIDATION", checks, sprintf("%d checks passed.", length(checks))), file.path(report_dir, "validation.txt"))
message(length(checks), " report-alignment checks passed")
