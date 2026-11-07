run_propagation <- function(data) {
  output <- list(); adf <- list(); models <- list(); granger <- list(); ranks <- list()
  fans <- unique(data$monthly$asset_id[data$monthly$asset_type == "fan_token"])
  for (id in fans) {
    ids <- c(id, config$propagation_benchmarks)
    series <- lapply(ids, function(a) {
      z <- data$monthly[data$monthly$asset_id == a & is.finite(data$monthly$close), c("date", "close")]
      names(z)[2] <- a
      z
    })
    merged <- Reduce(function(a, b) merge(a, b, by = "date"), series)
    z <- longest_monthly_block(merged)
    if (nrow(z) < config$monthly_min_observations) stop("Insufficient benchmark overlap: ", id)
    x <- apply(as.matrix(z[, ids]), 2, safe_scale)
    colnames(x) <- c("Token", "Bitcoin", "Chiliz")
    # Same Johansen specification as the original, with an explicitly different variable set.
    jo <- urca::ca.jo(x, type = "trace", K = 2, ecdet = "none", spec = "longrun")
    k <- ncol(x); rank <- 0L; selecting_rank <- TRUE
    for (r in 0:(k - 1L)) {
      ix <- k - r
      reject <- jo@teststat[ix] > jo@cval[ix, "5pct"]
      ranks[[length(ranks) + 1L]] <- data.frame(asset_id = id, null_rank_at_most = r,
        trace_statistic = jo@teststat[ix], critical_5pct = jo@cval[ix, "5pct"], reject_5pct = reject,
        observations = nrow(z), variable_set = "standardized token/BTC/CHZ price levels")
      if (selecting_rank && reject) rank <- r + 1L else selecting_rank <- FALSE
    }
    for (v in colnames(x)) for (form in c("level", "first_difference")) {
      vdata <- if (form == "level") x[, v] else diff(x[, v])
      test <- urca::ur.df(vdata, type = "drift", lags = 1, selectlags = "AIC")
      adf[[length(adf) + 1L]] <- data.frame(asset_id = id, variable = v, transformation = form,
        tau2 = test@teststat[1, "tau2"], critical_5pct = test@cval["tau2", "5pct"],
        reject_unit_root_5pct = test@teststat[1, "tau2"] < test@cval["tau2", "5pct"])
    }
    vecm <- NULL
    if (rank > 0L && rank < k) {
      vecm <- urca::cajorls(jo, r = rank)
      co <- summary(vecm$rlm)
      for (equation in seq_along(co)) {
        tab <- co[[equation]]$coefficients
        output[[length(output) + 1L]] <- data.frame(asset_id = id, equation = colnames(x)[equation], term = rownames(tab),
          estimate = tab[, 1], std_error = tab[, 2], t_value = tab[, 3], p_value = tab[, 4], selected_rank = rank,
          interpretation = "benchmark association; not FSI propagation or causal evidence")
      }
    }
    # Same p=1 VAR/F-test method, applied to the explicitly declared benchmark system.
    vm <- vars::VAR(log(as.matrix(z[, ids])), p = 1, type = "both")
    for (cause in colnames(vm$y)) {
      gc <- vars::causality(vm, cause = cause)$Granger
      granger[[length(granger) + 1L]] <- data.frame(asset_id = id, cause = cause, statistic = as.numeric(gc$statistic),
        p_value = gc$p.value, interpretation = "joint Granger predictability within token/BTC/CHZ system")
    }
    models[[id]] <- list(johansen = jo, vecm = vecm, var = vm, dates = z$date, selected_rank = rank)
    write_table(z, file.path(paths$clean, paste0(id, "_benchmark_system.csv")))
  }
  write_table(bind_rows(ranks, data.frame()), file.path(paths$results, "benchmark_johansen_trace.csv"))
  write_table(bind_rows(adf, data.frame()), file.path(paths$results, "benchmark_unit_root_tests.csv"))
  write_table(bind_rows(output, data.frame(asset_id = character(), equation = character(), term = character(), estimate = numeric(), std_error = numeric(), t_value = numeric(), p_value = numeric(), selected_rank = integer(), interpretation = character())), file.path(paths$results, "benchmark_vecm_coefficients.csv"))
  write_table(bind_rows(granger, data.frame()), file.path(paths$results, "benchmark_granger_tests.csv"))
  saveRDS(models, file.path(paths$results, "benchmark_propagation_models.rds"))
}
