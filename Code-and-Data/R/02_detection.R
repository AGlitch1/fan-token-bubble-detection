run_detection <- function(data) {
  summaries <- sequences <- episodes <- changes <- segments <- robustness <- list()
  models <- list(); cv_cache <- new.env(parent = emptyenv())
  fans <- unique(data$monthly$asset_id[data$monthly$asset_type == "fan_token"])
  for (id in fans) {
    message("Detection: ", id)
    m <- data$monthly[data$monthly$asset_id == id & is.finite(data$monthly$close), ]
    blocks <- monthly_blocks(m)
    for (b in seq_along(blocks)) {
      z <- blocks[[b]]; n <- nrow(z)
      if (n < config$monthly_min_observations) next
      # Paper Code.Rmd lines 579-595: radf on arithmetic monthly PRICE LEVELS.
      fit <- exuber::radf(z$close)
      key <- as.character(n)
      if (!exists(key, envir = cv_cache, inherits = FALSE)) assign(key,
        exuber::radf_mc_cv(n, minw = attr(fit, "minw"), nrep = config$critical_value_replications,
          seed = config$critical_value_seed), envir = cv_cache)
      cv <- get(key, envir = cv_cache)
      startup <- max(config$minimum_startup, as.integer(round(config$startup_fraction * n)))
      # Paper Code.Rmd lines 526-534; first return is zero, as in the notebook.
      returns <- c(0, diff(log(z$close)))
      cpm_fit <- cpm::processStream(returns, "Kolmogorov-Smirnov", ARL0 = config$monthly_arl0, startup = startup)
      for (test in c("adf", "sadf", "gsadf")) summaries[[length(summaries) + 1L]] <- data.frame(
        asset_id = id, block = b, observations = n, start_date = min(z$date), end_date = max(z$date),
        min_window = attr(fit, "minw"), adf_lags = attr(fit, "lag"), test = toupper(test), statistic = as.numeric(fit[[test]]),
        critical_90 = cv[[paste0(test, "_cv")]]["90%"], critical_95 = cv[[paste0(test, "_cv")]]["95%"],
        critical_99 = cv[[paste0(test, "_cv")]]["99%"], reject_95 = as.numeric(fit[[test]]) > cv[[paste0(test, "_cv")]]["95%"],
        critical_value_method = "exuber::radf_mc_cv", replications = config$critical_value_replications)
      endpoint <- seq.int(n - nrow(fit$bsadf) + 1L, n)
      sequences[[length(sequences) + 1L]] <- data.frame(asset_id = id, block = b, date = z$date[endpoint],
        price = z$close[endpoint], badf = as.numeric(fit$badf), bsadf = as.numeric(fit$bsadf),
        critical_90 = cv$bsadf_cv[, "90%"], critical_95 = cv$bsadf_cv[, "95%"], critical_99 = cv$bsadf_cv[, "99%"],
        above_95 = as.numeric(fit$bsadf) > cv$bsadf_cv[, "95%"])
      # Use the package's default GSADF rejection gate and date-stamping convention.
      if (as.numeric(fit$gsadf) > cv$gsadf_cv["95%"]) {
        ds <- exuber::datestamp(fit, cv = cv, sig_lvl = 95, min_duration = 0L)
        for (s in ds) if (nrow(s)) for (i in seq_len(nrow(s))) episodes[[length(episodes) + 1L]] <- data.frame(
          asset_id = id, block = b, start_date = z$date[as.integer(s$Start[i])], peak_date = z$date[as.integer(s$Peak[i])],
          end_date = z$date[as.integer(s$End[i])], package_duration_periods = s$Duration[i], ongoing = s$Ongoing[i],
          confidence = 0.95, interpretation = "explosive/euphoric episode; not a complete bubble life cycle")
      }
      cp <- cpm_fit$changePoints
      dt <- cpm_fit$detectionTimes
      if (length(cp)) for (i in seq_along(cp)) changes[[length(changes) + 1L]] <- data.frame(
        asset_id = id, block = b, change_number = i, change_point_index = cp[i], change_point_date = z$date[cp[i]],
        first_post_change_date = z$date[cp[i] + 1L], detection_index = dt[i], detection_date = z$date[dt[i]],
        arl0 = config$monthly_arl0, startup = startup, frequency = "monthly")
      edges <- c(0L, cp, n)
      for (i in seq_len(length(edges) - 1L)) {
        ix <- seq.int(edges[i] + 1L, edges[i + 1L])
        segments[[length(segments) + 1L]] <- data.frame(asset_id = id, block = b, segment = i,
          start_date = min(z$date[ix]), end_date = max(z$date[ix]), observations = length(ix),
          mean_monthly_log_return = mean(returns[ix]), sd_monthly_log_return = sd(returns[ix]),
          interpretation = "statistical distribution regime; economic phase labels require separate evidence")
      }
      models[[paste(id, b, sep = "_")]] <- list(radf = fit, critical_values = cv, cpm = cpm_fit, dates = z$date)
      png(file.path(paths$figures, paste0(id, "_detection.png")), width = 1500, height = 1100, res = 140)
      old <- par(mfrow = c(2, 1), mar = c(4, 4, 3, 1))
      plot(z$date, z$close, type = "l", col = "#167050", xlab = "UTC month", ylab = "Monthly mean price (USD)", main = paste(z$symbol[1], "- monthly price and KS change points"))
      if (length(cp)) abline(v = as.numeric(z$date[cp]), col = "#bb3333", lty = 2)
      legend("topright", c("Price", "KS change point"), col = c("#167050", "#bb3333"), lty = c(1, 2), bty = "n")
      plot(z$date[endpoint], as.numeric(fit$bsadf), type = "l", col = "#264c9e",
        ylim = range(c(as.numeric(fit$bsadf), cv$bsadf_cv[, "95%"]), finite = TRUE),
        xlab = "UTC month", ylab = "BSADF statistic", main = "exuber BSADF and 95% Monte Carlo critical sequence")
      lines(z$date[endpoint], cv$bsadf_cv[, "95%"], col = "#bb3333", lty = 2)
      legend("topleft", c("BSADF", "95% critical value"), col = c("#264c9e", "#bb3333"), lty = c(1, 2), bty = "n")
      par(old); dev.off()
    }
    w <- data$weekly[data$weekly$asset_id == id & is.finite(data$weekly$close), ]
    w <- w[order(w$date), ]
    wblocks <- split(w, cumsum(c(TRUE, as.numeric(diff(w$date)) != 7)))
    for (b in seq_along(wblocks)) {
      z <- wblocks[[b]]; startup <- max(config$minimum_startup, as.integer(round(config$startup_fraction * nrow(z))))
      if (nrow(z) <= startup) next
      fit <- cpm::processStream(c(0, diff(log(z$close))), "Kolmogorov-Smirnov", ARL0 = config$weekly_arl0, startup = startup)
      if (length(fit$changePoints)) for (i in seq_along(fit$changePoints)) robustness[[length(robustness) + 1L]] <- data.frame(
        asset_id = id, block = b, change_point_date = z$date[fit$changePoints[i]],
        first_post_change_date = z$date[fit$changePoints[i] + 1L], detection_date = z$date[fit$detectionTimes[i]],
        observations = nrow(z), arl0 = config$weekly_arl0, startup = startup)
      models[[paste0(id, "_weekly_", b)]] <- list(cpm = fit, dates = z$date)
    }
  }
  write_table(bind_rows(summaries, data.frame()), file.path(paths$results, "psy_test_summary.csv"))
  write_table(bind_rows(sequences, data.frame()), file.path(paths$results, "psy_bsadf_series.csv"))
  write_table(bind_rows(episodes, data.frame(asset_id = character(), block = integer(), start_date = character(), peak_date = character(), end_date = character(), package_duration_periods = integer(), ongoing = logical(), confidence = numeric(), interpretation = character())), file.path(paths$results, "psy_euphoric_episodes.csv"))
  write_table(bind_rows(changes, data.frame(asset_id = character(), block = integer(), change_number = integer(), change_point_index = integer(), change_point_date = character(), first_post_change_date = character(), detection_index = integer(), detection_date = character(), arl0 = integer(), startup = integer(), frequency = character())), file.path(paths$results, "ks_cpm_change_points.csv"))
  write_table(bind_rows(segments, data.frame()), file.path(paths$results, "ks_cpm_segments.csv"))
  write_table(bind_rows(robustness, data.frame(asset_id = character(), block = integer(), change_point_date = character(), first_post_change_date = character(), detection_date = character(), observations = integer(), arl0 = integer(), startup = integer())), file.path(paths$results, "weekly_ks_robustness.csv"))
  saveRDS(models, file.path(paths$results, "detection_models.rds"))
  invisible(models)
}
