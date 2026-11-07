run_forecasting <- function(data) {
  predictions <- list(); models <- list(); summaries <- list(); tests <- list()
  fans <- unique(data$monthly$asset_id[data$monthly$asset_type == "fan_token"])
  trend_path <- "Google Trends/fan_token_search_interest.csv"
  trends <- NULL
  if (file.exists(trend_path)) {
    trends <- read_table(trend_path)
    stopifnot(all(c("asset_id", "date", "search_interest") %in% names(trends)))
    trends$date <- as.Date(trends$date)
    if (anyNA(trends$date) || any(!is.finite(trends$search_interest)) || any(trends$search_interest < 0) ||
        any(duplicated(trends[c("asset_id", "date")]))) stop("Invalid search-interest input")
  }
  for (id in fans) {
    message("Forecasting: ", id)
    z <- data$monthly[data$monthly$asset_id == id & is.finite(data$monthly$close), ]
    z <- longest_monthly_block(z)
    n <- nrow(z); holdout <- min(config$forecast_holdout, n - config$forecast_min_training)
    if (holdout < 3L) stop("Insufficient forecasting sample: ", id)
    y <- log(z$close)
    xv <- NULL
    if (!is.null(trends)) {
      tz <- trends[trends$asset_id == id, ]
      xv <- log1p(tz$search_interest[match(z$date, tz$date)])
      if (anyNA(xv)) stop("Search-interest series must cover all modeled months: ", id)
    }
    rows <- list(); last_models <- list()
    for (i in seq.int(n - holdout, n - 1L)) {
      train <- y[seq_len(i)]
      arima <- forecast::auto.arima(train, seasonal = FALSE)
      f <- forecast::forecast(arima, h = 1, level = 95)
      row <- function(model, mean, lower, upper) data.frame(asset_id = id, date = z$date[i + 1L],
        model = model, actual_log_price = y[i + 1L], forecast_log_price = as.numeric(mean), lower_95_log = as.numeric(lower),
        upper_95_log = as.numeric(upper), training_observations = i, forecast_origin = z$date[i],
        observed_price_usd = exp(y[i + 1L]), median_price_forecast_usd = exp(as.numeric(mean)))
      rows[[length(rows) + 1L]] <- row("ARIMA", f$mean, f$lower[, "95%"], f$upper[, "95%"])
      # Original Code.Rmd lines 1637-1667: AR(1), LOCAL LEVEL, seasonal(12).
      # The published equation describes a local trend; the repository uses local level.
      ss <- list()
      ss <- bsts::AddAutoAr(ss, train, lags = 1)
      ss <- bsts::AddLocalLevel(ss, train)
      ss <- bsts::AddSeasonal(ss, train, nseasons = 12)
      bm <- bsts::bsts(train, state.specification = ss, niter = config$bsts_iterations,
        seed = config$bsts_seed, ping = 0, expected.model.size = 3)
      bf <- predict(bm, horizon = 1, burn = bsts::SuggestBurn(0.1, bm), seed = config$bsts_seed,
        quantiles = c(0.025, 0.975))
      rows[[length(rows) + 1L]] <- row("BSTS", bf$mean, bf$interval[1, ], bf$interval[2, ])
      if (!is.null(xv)) {
        # t-1 model uses only covariates known at the forecast origin.
        # t model is a conditional nowcast requiring observed target-month interest.
        for (kind in c("ARIMAX_t1", "ARIMAX_t")) {
          x <- if (kind == "ARIMAX_t1") c(NA_real_, head(xv, -1L)) else xv
          train_ix <- if (kind == "ARIMAX_t1") seq.int(2L, i) else seq_len(i)
          am <- forecast::auto.arima(y[train_ix], xreg = matrix(x[train_ix], ncol = 1), seasonal = FALSE)
          af <- forecast::forecast(am, h = 1, xreg = matrix(x[i + 1L], ncol = 1), level = 95)
          rows[[length(rows) + 1L]] <- row(kind, af$mean, af$lower[, "95%"], af$upper[, "95%"])
          last_models[[kind]] <- am
        }
      }
      last_models$ARIMA <- arima; last_models$BSTS <- bm
    }
    pred <- do.call(rbind, rows)
    predictions[[id]] <- pred
    models[[id]] <- last_models
    write_table(pred, file.path(paths$results, paste0(id, "_forecasts.csv")))
    saveRDS(last_models, file.path(paths$results, paste0(id, "_forecast_models.rds")))
    model_names <- unique(pred$model)
    for (model in model_names) {
      p <- pred[pred$model == model, ]
      summaries[[length(summaries) + 1L]] <- data.frame(asset_id = id, model = model, forecasts = nrow(p),
        start_date = min(p$date), end_date = max(p$date),
        rmse_log_price = Metrics::rmse(p$actual_log_price, p$forecast_log_price),
        smape_log_price_pct = 100 * Metrics::smape(p$actual_log_price, p$forecast_log_price),
        rmse_price_usd = Metrics::rmse(p$observed_price_usd, p$median_price_forecast_usd),
        smape_price_pct = 100 * Metrics::smape(p$observed_price_usd, p$median_price_forecast_usd),
        interval_coverage = mean(p$actual_log_price >= p$lower_95_log & p$actual_log_price <= p$upper_95_log))
    }
    wide <- reshape(pred[c("date", "model", "actual_log_price", "forecast_log_price")],
      idvar = c("date", "actual_log_price"), timevar = "model", direction = "wide")
    benchmark <- if ("ARIMAX_t" %in% model_names) "ARIMAX_t" else "BSTS"
    loss <- matrix(NA_real_, nrow(wide), length(model_names), dimnames = list(NULL, model_names))
    for (model in model_names) {
      pr <- wide[[paste0("forecast_log_price.", model)]]
      loss[, model] <- (pr - wide$actual_log_price)^2
      if (model == benchmark) next
      # Same multDM function and loss as original. Preserve undefined small-sample tests explicitly.
      dm <- tryCatch(multDM::DM.test(wide[[paste0("forecast_log_price.", benchmark)]], pr,
        wide$actual_log_price, loss.type = "SE", h = 1, c = FALSE, H1 = "more"), error = identity)
      tests[[length(tests) + 1L]] <- data.frame(asset_id = id, comparison_model = model, benchmark = benchmark,
        statistic = if (inherits(dm, "error")) NA_real_ else as.numeric(dm$statistic),
        p_value = if (inherits(dm, "error")) NA_real_ else dm$p.value,
        status = if (inherits(dm, "error")) conditionMessage(dm) else "completed",
        alternative = "benchmark has greater predictive accuracy under squared error")
    }
    set.seed(5)
    mcs <- MCS::MCSprocedure(loss, alpha = config$mcs_alpha, B = config$mcs_replications, statistic = "TR", verbose = FALSE)
    capture.output(show(mcs), file = file.path(paths$results, paste0(id, "_model_confidence_set.txt")))
    saveRDS(mcs, file.path(paths$results, paste0(id, "_model_confidence_set.rds")))
    png(file.path(paths$figures, paste0(id, "_forecasts.png")), width = 1500, height = 850, res = 140)
    p <- pred[pred$model == "BSTS", ]
    ylim <- range(c(p$actual_log_price, p$lower_95_log, p$upper_95_log), finite = TRUE)
    plot(p$date, p$actual_log_price, type = "l", lwd = 2, ylim = ylim, xlab = "UTC month", ylab = "Log monthly mean price", main = paste(z$symbol[1], "- expanding-window one-month-ahead forecasts"))
    polygon(c(p$date, rev(p$date)), c(p$lower_95_log, rev(p$upper_95_log)), col = adjustcolor("#5b82c6", 0.2), border = NA)
    lines(p$date, p$actual_log_price, lwd = 2)
    lines(p$date, p$forecast_log_price, col = "#264c9e", lty = 2)
    a <- pred[pred$model == "ARIMA", ]
    lines(a$date, a$forecast_log_price, col = "#b5651d", lty = 3)
    legend("topleft", c("Actual", "BSTS (95% band)", "ARIMA"), col = c("black", "#264c9e", "#b5651d"), lty = c(1, 2, 3), bty = "n")
    dev.off()
  }
  all_predictions <- do.call(rbind, predictions)
  write_table(all_predictions, file.path(paths$results, "expanding_window_forecasts.csv"))
  write_table(do.call(rbind, summaries), file.path(paths$results, "forecast_accuracy.csv"))
  write_table(do.call(rbind, tests), file.path(paths$results, "forecast_dm_tests.csv"))
  saveRDS(models, file.path(paths$results, "forecast_models.rds"))
  invisible(all_predictions)
}
