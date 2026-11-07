# Report-aligned empirical scope, using the paper's actual R detection packages.
# See Working-paper/Report-alignment.txt for distinctions between the proposal,
# submitted Phase 3, and original paper. No Google Trends/FSI inputs are needed.
report_dir <- file.path("Results", "Report-aligned")
report_figure_dir <- file.path("Figures", "Report-aligned")
dir.create(report_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(report_figure_dir, recursive = TRUE, showWarnings = FALSE)

reported_reference <- function(test, confidence, n) {
  # The submitted RESULTS used these reference approximations, not bootstrap CVs.
  tab <- read_table("Configuration/reported_reference_values.csv")
  tab <- tab[abs(tab$confidence - confidence) < 1e-10, ]
  x <- tab$sample_size; y <- tab[[test]]
  ans <- approx(x, y, xout = n, rule = 2)$y
  lo <- n < x[1]; hi <- n > tail(x, 1)
  ans[lo] <- y[1] + (y[2] - y[1]) / (x[2] - x[1]) * (n[lo] - x[1])
  ans[hi] <- tail(y, 1) + diff(tail(y, 2)) / diff(tail(x, 2)) * (n[hi] - tail(x, 1))
  ans
}

report_daily_blocks <- function(d) {
  d <- d[is.finite(d$adj_close_usd) & d$adj_close_usd > 0, ]
  d <- d[order(d$date_utc), ]
  split(d, cumsum(c(TRUE, as.numeric(diff(d$date_utc)) != 1)))
}

report_bayesian_adf <- function(y, dates) {
  # Base-R port of the LOCAL ADF model actually described in Phase 3.
  # It is not the paper's BSTS forecast and not section 6.5's proposed NIG model.
  dy <- diff(y); response <- dy / sd(dy)
  levels <- (head(y, -1) - mean(y)) / sd(y)
  h <- 1 / config$report_bayesian_hazard_days
  slope_var <- config$report_bayesian_slope_prior_sd^2
  m0 <- m1 <- 0; v00 <- 4; v01 <- 0; v11 <- slope_var; prob <- 1
  output <- matrix(NA_real_, length(dy), 5)
  for (i in seq_along(dy)) {
    x <- levels[i]; target <- response[i]
    cx0 <- v00 + v01 * x; cx1 <- v01 + v11 * x
    pv <- 1 + cx0 + cx1 * x; pm <- m0 + m1 * x
    prior_v <- 5 + slope_var * x^2
    growth <- log(pmax(prob, .Machine$double.xmin)) + dnorm(target, pm, sqrt(pv), log = TRUE) + log1p(-h)
    joint <- c(log(h) + dnorm(target, 0, sqrt(prior_v), log = TRUE), growth)
    prob <- exp(joint - max(joint)); prob <- prob / sum(prob)
    error <- target - pm
    m0 <- c(4 * target / prior_v, m0 + cx0 / pv * error)
    m1 <- c(slope_var * x * target / prior_v, m1 + cx1 / pv * error)
    v00 <- c(4 - 16 / prior_v, v00 - cx0^2 / pv)
    v01 <- c(-4 * slope_var * x / prior_v, v01 - cx0 * cx1 / pv)
    v11 <- c(slope_var - (slope_var * x)^2 / prior_v, v11 - cx1^2 / pv)
    slope_probability <- sum(prob * pnorm(m1 / sqrt(pmax(v11, .Machine$double.xmin))))
    slope_mean <- sum(prob * m1)
    slope_sd <- sqrt(max(0, sum(prob * (v11 + m1^2)) - slope_mean^2))
    output[i, ] <- c(prob[1], slope_probability, slope_mean, slope_sd, sum(prob * (seq_along(prob) - 1)))
  }
  data.frame(date_utc = dates[-1], bayesian_change_point_probability = output[, 1],
    bayesian_explosive_slope_probability = output[, 2], bayesian_adf_slope_mean_standardized = output[, 3],
    bayesian_adf_slope_sd_standardized = output[, 4], posterior_expected_run_length_days = output[, 5])
}

run_report_alignment <- function(data) {
  daily <- data$daily
  if (any(daily$close_usd != daily$adj_close_usd, na.rm = TRUE))
    message("Using adjusted close for the submitted report's price definition")
  summaries <- series <- episodes <- change_points <- bayesian <- comparisons <- list()
  model_dates <- list()
  for (cutoff in as.character(config$report_cutoffs)) {
    snapshot <- daily[daily$date_utc <= as.Date(cutoff), ]
    write_table(snapshot, file.path(paths$clean, paste0("daily_panel_", cutoff, ".csv")))
    for (id in unique(snapshot$asset_id)) {
      g <- snapshot[snapshot$asset_id == id, ]
      blocks <- report_daily_blocks(g)
      for (b in seq_along(blocks)) {
        z <- blocks[[b]]; n <- nrow(z)
        if (n < config$report_min_observations) stop("Insufficient daily history: ", id)
        message("Report scope ", cutoff, ": ", id)
        y <- log(z$adj_close_usd)
        price_window <- max(20L, as.integer(floor((0.01 + 1.8 / sqrt(n)) * n)))
        # exuber minw counts regression rows, while the submitted code counted
        # price observations (one more). This preserves the reported windows.
        fit <- exuber::radf(y, minw = price_window - 1L, lag = 0L)
        ix <- seq.int(n - nrow(fit$bsadf) + 1L, n)
        stat <- as.numeric(fit$bsadf)
        threshold <- reported_reference("SADF", 0.95, ix)
        above <- stat > threshold
        runs <- split(which(above), cumsum(c(TRUE, diff(which(above)) > 1L)))
        longest <- if (length(which(above))) max(lengths(runs)) else 0L
        meta <- data.frame(cutoff_date = cutoff, asset_id = id, symbol = z$symbol[1], asset_type = z$asset_type[1], block = b)
        summary <- cbind(meta, data.frame(observations = n, start_date = min(z$date_utc), end_date = max(z$date_utc),
          minimum_window_price_observations = price_window, exuber_minw_regression_rows = price_window - 1L,
          adf_lags = 0L, sadf_statistic = as.numeric(fit$sadf), gsadf_statistic = as.numeric(fit$gsadf),
          above95_days = sum(above), longest95_run = longest, calibration = "submitted_report_reference_approximation"))
        for (q in c(0.90, 0.95, 0.99)) for (test in c("SADF", "GSADF")) {
          cv <- reported_reference(test, q, n)
          summary[[paste0(tolower(test), "_cv_", q * 100)]] <- cv
          summary[[paste0(tolower(test), "_reject_", q * 100)]] <- as.numeric(fit[[tolower(test)]]) > cv
        }
        summaries[[length(summaries) + 1L]] <- summary
        bay <- report_bayesian_adf(y, z$date_utc)
        bayesian[[length(bayesian) + 1L]] <- cbind(meta[rep(1, nrow(bay)), ], bay)
        bs <- data.frame(date_utc = z$date_utc[ix], bsadf = stat,
          dating_reference_95 = threshold, above_95 = above,
          calibration = "SADF_based_endpoint_approximation_not_bootstrap")
        series[[length(series) + 1L]] <- cbind(meta[rep(1, nrow(bs)), ], bs)
        if (any(above)) for (run in runs) if (length(run) >= config$report_episode_days) {
          pos <- ix[run]; peak <- pos[which.max(stat[run])]
          episodes[[length(episodes) + 1L]] <- cbind(meta, data.frame(start_date = z$date_utc[min(pos)],
            end_date = z$date_utc[max(pos)], peak_bsadf_date = z$date_utc[peak], duration_days = length(pos),
            peak_bsadf = max(stat[run]), price_change_pct = 100 * (z$adj_close_usd[max(pos)] / z$adj_close_usd[min(pos)] - 1),
            ongoing = max(pos) == n, interpretation = "persistent reference-threshold signal; inspect price direction"))
        }
        # Keep the methodology paper's actual sequential KS algorithm. The
        # submitted Phase 3 mean-shift penalty model is a documented difference.
        returns <- diff(y)
        startup <- max(config$report_ks_minimum_startup, as.integer(ceiling(config$report_ks_startup_fraction * length(returns))))
        primary_cp <- integer()
        for (arl in c(config$report_ks_arl0, config$report_ks_sensitivity_arl0)) {
          ks <- cpm::processStream(returns, "Kolmogorov-Smirnov", ARL0 = arl, startup = startup)
          if (arl == config$report_ks_arl0) primary_cp <- ks$changePoints
          for (k in seq_along(ks$changePoints)) change_points[[length(change_points) + 1L]] <- cbind(meta, data.frame(
            arl0 = arl, startup_return_observations = startup,
            change_point_date = z$date_utc[ks$changePoints[k] + 1L],
            first_post_change_date = z$date_utc[ks$changePoints[k] + 2L],
            detection_date = z$date_utc[ks$detectionTimes[k] + 1L]))
        }
        # Compact audit model for package-output validation; no redundant MCMC objects.
        model_dates[[paste(cutoff, id, b, sep = "_")]] <- list(radf = fit, dates = z$date_utc)
        plot_report_diagnostics(z, bs, bay, z$date_utc[primary_cp + 1L], cutoff)
      }
      if (g$asset_type[1] == "fan_token") for (benchmark in c("bitcoin", "ethereum", "chiliz")) {
        bm <- snapshot[snapshot$asset_id == benchmark, c("date_utc", "return_pct")]
        pair <- merge(g[c("date_utc", "return_pct")], bm, by = "date_utc")
        ok <- is.finite(pair$return_pct.x) & is.finite(pair$return_pct.y)
        comparisons[[length(comparisons) + 1L]] <- data.frame(cutoff_date = cutoff, asset_id = id,
          benchmark = benchmark, matched_returns = sum(ok), correlation = cor(pair$return_pct.x[ok], pair$return_pct.y[ok]))
      }
    }
  }
  write_table(do.call(rbind, summaries), file.path(report_dir, "psy_test_summary.csv"))
  write_table(do.call(rbind, series), file.path(report_dir, "psy_bsadf_series.csv"))
  empty_episodes <- data.frame(cutoff_date = character(), asset_id = character(), symbol = character(), asset_type = character(), block = integer(), start_date = character(), end_date = character(), peak_bsadf_date = character(), duration_days = integer(), peak_bsadf = numeric(), price_change_pct = numeric(), ongoing = logical(), interpretation = character())
  write_table(bind_rows(episodes, empty_episodes), file.path(report_dir, "psy_persistent_intervals.csv"))
  write_table(do.call(rbind, change_points), file.path(report_dir, "ks_cpm_change_points.csv"))
  write_table(do.call(rbind, bayesian), file.path(report_dir, "bayesian_local_adf.csv"))
  write_table(do.call(rbind, comparisons), file.path(report_dir, "benchmark_return_correlations.csv"))
  saveRDS(model_dates, file.path(report_dir, "daily_radf_models.rds"))
  invisible(NULL)
}

plot_report_diagnostics <- function(z, bs, bay, change_dates, cutoff) {
  png(file.path(report_figure_dir, paste0(cutoff, "_", z$asset_id[1], ".png")), width = 1500, height = 1500, res = 140)
  old <- par(mfrow = c(3, 1), mar = c(4.5, 4.5, 4, 1), mgp = c(2.5, 0.8, 0))
  plot(z$date_utc, z$adj_close_usd, type = "l", col = "#167050", xlab = "", ylab = "Adjusted price (USD)",
    main = paste(z$symbol[1], "- daily diagnostics through", cutoff))
  if (length(change_dates)) abline(v = as.numeric(change_dates), col = "#b73f3f", lty = 3)
  plot(bs$date_utc, bs$bsadf, type = "l", col = "#264c9e",
    ylim = range(c(bs$bsadf, bs$dating_reference_95), finite = TRUE), xlab = "", ylab = "BSADF",
    main = "exuber statistic and reported approximate dating reference")
  lines(bs$date_utc, bs$dating_reference_95, col = "#b73f3f", lty = 2)
  plot(bay$date_utc, bay$bayesian_explosive_slope_probability, type = "l", col = "#6d468c", ylim = c(0, 1),
    xlab = "UTC date", ylab = "Posterior probability", main = "Report local-ADF slope probability (retrospective scaling)")
  abline(h = 0.95, col = "#b73f3f", lty = 2)
  par(old); dev.off()
}

refresh_report_figures <- function() {
  # Render from exported estimates; presentation edits need no model refit.
  daily <- read_table("Processed-data/clean_daily_panel.csv"); daily$date_utc <- as.Date(daily$date_utc)
  test <- read_table(file.path(report_dir, "psy_test_summary.csv"))
  bs <- read_table(file.path(report_dir, "psy_bsadf_series.csv")); bs$date_utc <- as.Date(bs$date_utc)
  bay <- read_table(file.path(report_dir, "bayesian_local_adf.csv")); bay$date_utc <- as.Date(bay$date_utc)
  cp <- read_table(file.path(report_dir, "ks_cpm_change_points.csv"))
  for (i in seq_len(nrow(test))) {
    t <- test[i, ]
    z <- daily[daily$asset_id == t$asset_id & daily$date_utc >= as.Date(t$start_date) & daily$date_utc <= as.Date(t$end_date), ]
    b <- bs[bs$asset_id == t$asset_id & bs$cutoff_date == t$cutoff_date & bs$block == t$block, ]
    p <- bay[bay$asset_id == t$asset_id & bay$cutoff_date == t$cutoff_date & bay$block == t$block, ]
    changes <- cp[cp$asset_id == t$asset_id & cp$cutoff_date == t$cutoff_date & cp$block == t$block & cp$arl0 == config$report_ks_arl0, ]
    plot_report_diagnostics(z, b, p, as.Date(changes$change_point_date), t$cutoff_date)
  }
}

write_report_alignment <- function() {
  test <- read_table(file.path(report_dir, "psy_test_summary.csv"))
  ep <- read_table(file.path(report_dir, "psy_persistent_intervals.csv"))
  cp <- read_table(file.path(report_dir, "ks_cpm_change_points.csv"))
  bay <- read_table(file.path(report_dir, "bayesian_local_adf.csv"))
  overview <- lapply(as.character(config$report_cutoffs), function(cutoff) {
    t <- test[test$cutoff_date == cutoff, ]; fan <- t[t$asset_type == "fan_token", ]
    data.frame(cutoff_date = cutoff, assets = nrow(t), fan_token_prices = sum(fan$observations),
      gsadf_reference_exceedances = sum(fan$gsadf_reject_95),
      fan_persistent_intervals = sum(ep$cutoff_date == cutoff & ep$asset_type == "fan_token"),
      ks_change_points_arl500 = sum(cp$cutoff_date == cutoff & cp$arl0 == config$report_ks_arl0),
      fan_bayesian_days_ge95 = sum(bay$cutoff_date == cutoff & bay$asset_type == "fan_token" & bay$bayesian_explosive_slope_probability >= 0.95))
  })
  write_table(do.call(rbind, overview), file.path(report_dir, "sample_comparison.csv"))
  status <- data.frame(section = c("Daily log-price SADF/GSADF and BSADF", "30-day persistence and June/September comparison",
    "Daily sequential KS-CPM", "Reported local-ADF Bayesian diagnostics", "BTC/ETH/CHZ comparisons",
    "Google Trends and financial stress", "ARIMA/BSTS forecasting and Johansen/VECM", "Wild bootstrap and hierarchical logit"),
    status = c(rep("COMPLETED", 5), "OUTSIDE_SUBMITTED_REPORT_SCOPE", "OPTIONAL_PAPER_EXTENSIONS", "PROPOSED_NOT_REPORTED_AS_IMPLEMENTED"),
    detail = c("exuber statistics; submitted Phase 3 approximate reference thresholds retained and labeled",
      "Both cutoffs re-estimated independently; adjusted USD prices; all 23 assets",
      "Paper cpm algorithm retained; differs from submitted Phase 3 penalized mean segmentation",
      "Base-R port of submitted local normal-prior model; not BSTS or proposed NIG model",
      "Daily return correlations; ETH is retained alongside BTC and CHZ",
      "Not required inputs and not missing project tasks",
      "Preserved separately; run_paper_extensions.R, not part of the submitted results",
      "Discussed in methodology; Phase 3 uses reference tables/local ADF and calls pooling future work"))
  write_table(status, "Results/method_status.csv")
  lines <- c("FAN-TOKEN R RESULTS ALIGNED WITH THE SUBMITTED PHASE 3 SCOPE", "",
    "Daily log adjusted USD prices; 20 fan tokens plus BTC/ETH/CHZ.",
    "Primary cutoff 2026-06-30; extension cutoff 2026-09-19; 30 consecutive days for retained intervals.",
    "", capture.output(print(do.call(rbind, overview), row.names = FALSE)), "",
    "The report does not use Google Trends or a financial-stress index. These are outside its scope.",
    "The R workflow retains exuber::radf and cpm::processStream from the methodology paper.",
    "The submitted reference-table interpolation and SADF-based dating approximation are retained for comparability.",
    "These are nominal reference classifications, not bootstrap p-values or matched BSADF critical values.",
    "Daily Bayesian local-ADF probabilities follow the submitted Phase 3 model and use retrospective full-sample scaling.",
    "KS-CPM replaces the submitted penalized mean-shift segmentation to preserve the paper's core method.",
    "Its counts must not be read as reproducing the report's 76.8% volatility-shift statistic.",
    "Proposed BIC/wild-bootstrap/NIG/hierarchical extensions are not claimed as implemented results.",
    "ARIMA/BSTS, Johansen/VECM and monthly/weekly analyses are preserved as optional paper extensions.",
    "See Working-paper/Report-alignment.txt for the complete scope comparison.", "",
    tail(readLines(file.path(report_dir, "validation.txt")), 1))
  writeLines(lines, file.path(report_dir, "RESULTS.txt"))
  writeLines(lines, "Results/RESULTS.txt")
  writeLines(lines, "../Working-paper/Fan-token-results.txt")
  capture.output(sessionInfo(), file = file.path(report_dir, "sessionInfo.txt"))
  source("R/05_report.R")
  write_inventory()
}
