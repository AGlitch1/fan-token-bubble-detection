process_data <- function() {
  registry <- read_table(file.path(paths$raw, "sample_registry.csv"))
  manifest <- read_table(file.path(paths$raw, "request_manifest.csv"))
  requests <- manifest[manifest$source == "Yahoo Finance chart service" & manifest$status == "OK", ]
  candidates <- registry[tolower(as.character(registry$included)) == "true", ]
  # Recover provider values from JSON, independently of the old Python CSV export.
  frames <- lapply(seq_len(nrow(requests)), function(i) {
    req <- requests[i, ]
    j <- jsonlite::fromJSON(file.path(paths$raw, "yahoo", paste0(req$asset_id, ".json")), simplifyVector = FALSE)
    if (!is.null(j$chart$error)) stop("Archived Yahoo error: ", req$asset_id)
    obj <- j$chart$result[[1]]
    times <- unlist(obj$timestamp)
    q <- obj$indicators$quote[[1]]
    nums <- function(v) vapply(v, function(z) if (is.null(z)) NA_real_ else as.numeric(z), numeric(1))
    if (length(q$close) != length(times)) stop("Mismatched provider arrays: ", req$asset_id)
    meta <- candidates[candidates$coingecko_id == req$asset_id, ]
    fan <- nrow(meta) == 1L
    id <- as.character(req$asset_id)
    data.frame(
      timestamp_utc = format(as.POSIXct(times, origin = "1970-01-01", tz = "UTC"), "%Y-%m-%dT%H:%M:%S+00:00", tz = "UTC"),
      date_utc = as.Date(as.POSIXct(times, origin = "1970-01-01", tz = "UTC"), tz = "UTC"),
      asset_id = id, symbol = if (fan) meta$symbol else c(bitcoin = "BTC", ethereum = "ETH", chiliz = "CHZ")[[id]],
      asset_name = if (fan) meta$name else c(bitcoin = "Bitcoin", ethereum = "Ethereum", chiliz = "Chiliz")[[id]],
      asset_type = if (fan) "fan_token" else "benchmark", sample_rank = if (fan) meta$candidate_rank else NA_integer_,
      yahoo_symbol = req$provider_symbol,
      open_usd = nums(q$open), high_usd = nums(q$high), low_usd = nums(q$low), close_usd = nums(q$close),
      adj_close_usd = nums(obj$indicators$adjclose[[1]]$adjclose), volume_reported = nums(q$volume),
      source = "Yahoo Finance chart service")
  })
  raw <- do.call(rbind, frames)
  raw <- raw[raw$date_utc >= config$start_date & raw$date_utc <= config$cutoff_date, ]
  write_table(raw, file.path(paths$clean, "raw_market_data_rebuilt.csv"))
  quality <- list()
  clean <- lapply(split(raw, raw$asset_id), function(g) {
    g <- g[order(g$date_utc, g$timestamp_utc), ]
    duplicates <- sum(duplicated(g$date_utc) | duplicated(g$date_utc, fromLast = TRUE))
    if (duplicates) {
      conflicts <- vapply(split(g$close_usd, g$date_utc), function(v) length(unique(na.omit(v))) > 1L, logical(1))
      if (any(conflicts)) stop("Conflicting duplicate dates: ", g$asset_id[1])
    }
    g <- g[!duplicated(g$date_utc, fromLast = TRUE), ]
    valid <- is.finite(g$close_usd) & g$close_usd > 0
    if (!any(valid)) stop("No positive prices: ", g$asset_id[1])
    calendar <- data.frame(date_utc = seq(min(g$date_utc[valid]), config$cutoff_date, by = "day"))
    d <- merge(calendar, g, by = "date_utc", all.x = TRUE, sort = TRUE)
    for (col in c("asset_id", "symbol", "asset_name", "asset_type", "sample_rank", "yahoo_symbol", "source")) d[[col]] <- g[[col]][1]
    d$invalid_price_flag <- !is.na(d$close_usd) & (!is.finite(d$close_usd) | d$close_usd <= 0)
    d$valid_price_flag <- is.finite(d$close_usd) & d$close_usd > 0
    d$missing_price_flag <- !d$valid_price_flag
    d$zero_volume_flag <- !is.na(d$volume_reported) & d$volume_reported == 0
    d$log_price <- NA_real_
    d$log_price[d$valid_price_flag] <- log(d$close_usd[d$valid_price_flag])
    previous <- c(NA_real_, head(d$close_usd, -1L))
    consecutive <- d$valid_price_flag & c(FALSE, head(d$valid_price_flag, -1L))
    d$prior_valid_close_usd <- ifelse(consecutive, previous, NA_real_)
    d$return_pct <- ifelse(consecutive, c(NA_real_, diff(d$log_price)) * 100, NA_real_)
    d$log_volume <- ifelse(is.finite(d$volume_reported) & d$volume_reported >= 0, log1p(d$volume_reported), NA_real_)
    d$indexed_price_100 <- ifelse(d$valid_price_flag, d$close_usd / d$close_usd[which(d$valid_price_flag)[1]] * 100, NA_real_)
    d$rolling_volatility_30d_pct_annualized <- vapply(seq_len(nrow(d)), function(i) {
      v <- d$return_pct[max(1L, i - 29L):i]
      if (sum(is.finite(v)) >= 20L) sd(v, na.rm = TRUE) * sqrt(365) else NA_real_
    }, numeric(1))
    d$extreme_return_flag <- !is.na(d$return_pct) & abs(d$return_pct) > 100
    d$gap_days_since_prior_valid <- NA_real_
    d$gap_days_since_prior_valid[d$valid_price_flag] <- c(NA_real_, diff(as.numeric(d$date_utc[d$valid_price_flag])))
    quality[[length(quality) + 1L]] <<- data.frame(asset_id = g$asset_id[1], asset_type = g$asset_type[1],
      first_valid_date = min(d$date_utc), last_date = max(d$date_utc), expected_days = nrow(d),
      valid_prices = sum(d$valid_price_flag), missing_prices = sum(d$missing_price_flag),
      coverage = mean(d$valid_price_flag), duplicate_rows = duplicates,
      invalid_prices = sum(d$invalid_price_flag), extreme_returns = sum(d$extreme_return_flag))
    d
  })
  daily <- do.call(rbind, clean)
  rownames(daily) <- NULL
  daily <- daily[order(daily$asset_type, daily$sample_rank, daily$date_utc, na.last = TRUE), ]
  write_table(daily, file.path(paths$clean, "clean_daily_panel.csv"))
  write_table(daily[daily$valid_price_flag, ], file.path(paths$clean, "clean_observed_panel.csv"))
  write_table(do.call(rbind, quality), file.path(paths$results, "data_quality.csv"))
  decisions <- read_table("Configuration/manual_review_decisions.csv")
  extremes <- daily[daily$extreme_return_flag, c("asset_id", "date_utc", "close_usd", "return_pct")]
  reviewed <- merge(extremes, decisions[decisions$case_type == "extreme_return", ],
    by.x = c("asset_id", "date_utc"), by.y = c("asset_id", "date_or_period"), all.x = TRUE)
  write_table(reviewed, file.path(paths$results, "extreme_return_review.csv"))

  # Match the paper's arithmetic period means; do not use month-end closes.
  aggregate_period <- function(frequency) {
    period <- if (frequency == "monthly") as.Date(format(daily$date_utc, "%Y-%m-01")) else
      daily$date_utc - (as.integer(format(daily$date_utc, "%u")) - 1L)
    pieces <- split(seq_len(nrow(daily)), paste(daily$asset_id, period))
    data <- lapply(pieces, function(ix) {
      z <- daily[ix, ]; start <- period[ix[1]]
      end <- if (frequency == "monthly") seq(start, by = "month", length.out = 2L)[2] - 1L else start + 6L
      if (end > config$cutoff_date) return(NULL) # Omit the unfinished final month/week.
      good <- z$valid_price_flag
      # Missing internal days make a period unusable; first listing period is retained and flagged.
      complete <- all(good)
      data.frame(asset_id = z$asset_id[1], symbol = z$symbol[1], asset_type = z$asset_type[1], date = start,
        period_end = end, close = if (complete) mean(z$close_usd) else NA_real_,
        observed_days = sum(good), expected_days = nrow(z), full_calendar_period = nrow(z) == as.integer(end - start) + 1L,
        reported_volume_sum = if (all(is.finite(z$volume_reported))) sum(z$volume_reported) else NA_real_)
    })
    out <- do.call(rbind, data)
    out <- out[order(out$asset_id, out$date), ]
    out$log_price <- log(out$close)
    out$log_return <- NA_real_
    for (id in unique(out$asset_id)) {
      ix <- which(out$asset_id == id)
      # The original notebook pads the first period's return with zero.
      out$log_return[ix] <- c(0, diff(out$log_price[ix]))
    }
    write_table(out, file.path(paths$clean, paste0(frequency, "_panel.csv")))
    out
  }
  monthly <- aggregate_period("monthly")
  weekly <- aggregate_period("weekly")
  dir.create("Economic variables", showWarnings = FALSE)
  for (id in unique(monthly$asset_id)) write_table(monthly[monthly$asset_id == id, ], file.path("Economic variables", paste0(id, ".csv")))
  desc <- lapply(split(daily, daily$asset_id), function(d) {
    r <- d$return_pct[is.finite(d$return_pct)]
    data.frame(asset_id = d$asset_id[1], symbol = d$symbol[1], asset_type = d$asset_type[1],
      price_observations = sum(d$valid_price_flag), return_observations = length(r), mean_daily_return_pct = mean(r),
      sd_daily_return_pct = sd(r), annualized_volatility_pct = sd(r) * sqrt(365), min_return_pct = min(r), max_return_pct = max(r))
  })
  write_table(do.call(rbind, desc), file.path(paths$results, "descriptive_statistics.csv"))
  list(daily = daily, monthly = monthly, weekly = weekly)
}
