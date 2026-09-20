from __future__ import annotations

import json
from math import sqrt

import numpy as np
import pandas as pd

from common import CLEAN_DIR, QUALITY_DIR, RAW_DIR, ensure_directories, load_config, write_json


def clean_asset(group: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, dict]:
    group = group.copy()
    group["date_utc"] = pd.to_datetime(group["date_utc"], errors="coerce", utc=True).dt.tz_localize(None)
    group = group.dropna(subset=["date_utc"]).sort_values(["date_utc", "timestamp_utc"])
    for column in ["open_usd", "high_usd", "low_usd", "close_usd", "adj_close_usd", "volume_reported"]:
        group[column] = pd.to_numeric(group[column], errors="coerce")

    duplicate_rows = int(group.duplicated(["date_utc"], keep=False).sum())
    conflicting_duplicates = 0
    if duplicate_rows:
        duplicate_groups = group[group.duplicated(["date_utc"], keep=False)].groupby("date_utc")
        conflicting_duplicates = int(sum(block["close_usd"].nunique(dropna=True) > 1 for _, block in duplicate_groups))
    group = group.drop_duplicates(["date_utc"], keep="last")

    cutoff = pd.Timestamp(config["cutoff_date"])
    start = pd.Timestamp(config["start_date"])
    group = group[(group["date_utc"] >= start) & (group["date_utc"] <= cutoff)]
    valid_raw = group["close_usd"].notna() & (group["close_usd"] > 0)
    if not valid_raw.any():
        raise RuntimeError(f"No positive closing prices for {group['asset_id'].iloc[0]}")

    first_valid = group.loc[valid_raw, "date_utc"].min()
    calendar = pd.DataFrame({"date_utc": pd.date_range(first_valid, cutoff, freq="D")})
    metadata_columns = ["asset_id", "symbol", "asset_name", "asset_type", "sample_rank", "yahoo_symbol", "source"]
    metadata = {column: group[column].dropna().iloc[0] if group[column].notna().any() else None for column in metadata_columns}
    clean = calendar.merge(group, on="date_utc", how="left", suffixes=("", "_raw"))
    for column, value in metadata.items():
        clean[column] = value
    clean["sample_rank"] = pd.to_numeric(clean["sample_rank"], errors="coerce").astype("Float64")

    clean["invalid_price_flag"] = clean["close_usd"].notna() & (clean["close_usd"] <= 0)
    clean["valid_price_flag"] = clean["close_usd"].notna() & (clean["close_usd"] > 0)
    clean["missing_price_flag"] = ~clean["valid_price_flag"]
    clean["zero_volume_flag"] = clean["volume_reported"].eq(0)
    clean["log_price"] = np.where(clean["valid_price_flag"], np.log(clean["close_usd"]), np.nan)
    consecutive = clean["valid_price_flag"] & clean["valid_price_flag"].shift(1, fill_value=False)
    clean["prior_valid_close_usd"] = np.where(consecutive, clean["close_usd"].shift(1), np.nan)
    clean["return_pct"] = np.where(consecutive, clean["log_price"].diff() * 100.0, np.nan)
    clean["log_volume"] = np.where(
        clean["volume_reported"].notna() & (clean["volume_reported"] >= 0),
        np.log1p(clean["volume_reported"]),
        np.nan,
    )
    first_price = float(clean.loc[clean["valid_price_flag"], "close_usd"].iloc[0])
    clean["indexed_price_100"] = np.where(
        clean["valid_price_flag"], clean["close_usd"] / first_price * 100.0, np.nan
    )
    clean["rolling_volatility_30d_pct_annualized"] = (
        clean["return_pct"]
        .rolling(
            int(config["rolling_volatility_days"]),
            min_periods=int(config["rolling_volatility_min_observations"]),
        )
        .std(ddof=1)
        * sqrt(float(config["annualization_days"]))
    )
    clean["extreme_return_flag"] = clean["return_pct"].abs() > float(config["outlier_abs_log_return_pct"])

    valid_dates = clean.loc[clean["valid_price_flag"], "date_utc"]
    clean["gap_days_since_prior_valid"] = np.nan
    clean.loc[clean["valid_price_flag"], "gap_days_since_prior_valid"] = valid_dates.diff().dt.days.values

    expected_days = len(clean)
    valid_days = int(clean["valid_price_flag"].sum())
    coverage = valid_days / expected_days if expected_days else 0.0
    failures = []
    if valid_days < int(config["min_observations"]):
        failures.append("insufficient valid observations")
    if coverage < float(config["min_coverage_ratio"]):
        failures.append("coverage below threshold")
    if int(clean["invalid_price_flag"].sum()):
        failures.append("non-positive prices")
    if conflicting_duplicates:
        failures.append("conflicting duplicate dates")

    quality = {
        "asset_id": metadata["asset_id"],
        "symbol": metadata["symbol"],
        "asset_name": metadata["asset_name"],
        "asset_type": metadata["asset_type"],
        "sample_rank": metadata["sample_rank"],
        "first_valid_date": first_valid.date().isoformat(),
        "last_expected_date": cutoff.date().isoformat(),
        "expected_calendar_days": expected_days,
        "valid_price_days": valid_days,
        "return_observations": int(clean["return_pct"].notna().sum()),
        "missing_price_days": int(clean["missing_price_flag"].sum()),
        "coverage_ratio": coverage,
        "duplicate_rows": duplicate_rows,
        "conflicting_duplicate_dates": conflicting_duplicates,
        "invalid_price_days": int(clean["invalid_price_flag"].sum()),
        "zero_volume_days": int(clean["zero_volume_flag"].sum()),
        "extreme_return_days": int(clean["extreme_return_flag"].sum()),
        "largest_positive_return_pct": clean["return_pct"].max(),
        "largest_negative_return_pct": clean["return_pct"].min(),
        "quality_status": "PASS" if not failures else "REVIEW",
        "quality_issues": "; ".join(failures),
    }
    return clean, quality


def cross_validate(clean_observed: pd.DataFrame) -> pd.DataFrame:
    path = RAW_DIR / "coingecko_validation_prices.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(
            columns=[
                "asset_id",
                "matched_days",
                "selected_date_shift_days",
                "price_correlation",
                "median_abs_relative_difference",
                "p95_abs_relative_difference",
                "validation_status",
            ]
        )
    cg = pd.read_csv(path)
    if cg.empty:
        return pd.DataFrame()
    cg["date_utc"] = pd.to_datetime(cg["date_utc"], errors="coerce")
    cg["coingecko_price_usd"] = pd.to_numeric(cg["coingecko_price_usd"], errors="coerce")
    yahoo = clean_observed[["asset_id", "date_utc", "close_usd"]].copy()
    results = []
    for asset_id, cg_group in cg.groupby("asset_id"):
        yahoo_group = yahoo[yahoo["asset_id"] == asset_id]
        candidates = []
        for shift in (-1, 0, 1):
            shifted = cg_group.copy()
            shifted["aligned_date"] = shifted["date_utc"] + pd.to_timedelta(shift, unit="D")
            merged = yahoo_group.merge(
                shifted[["aligned_date", "coingecko_price_usd"]],
                left_on="date_utc",
                right_on="aligned_date",
                how="inner",
            ).dropna(subset=["close_usd", "coingecko_price_usd"])
            correlation = merged["close_usd"].corr(merged["coingecko_price_usd"]) if len(merged) >= 3 else np.nan
            candidates.append((correlation if pd.notna(correlation) else -np.inf, shift, merged))
        correlation, shift, merged = max(candidates, key=lambda item: item[0])
        relative_difference = (merged["close_usd"] / merged["coingecko_price_usd"] - 1).abs()
        median_diff = relative_difference.median()
        p95_diff = relative_difference.quantile(0.95)
        # Require agreement for both the typical day and the tail of the
        # validation window. A high p95 difference can reveal isolated source
        # discrepancies that a small median difference would otherwise hide.
        passed = (
            len(merged) >= 100
            and correlation >= 0.95
            and median_diff <= 0.05
            and p95_diff <= 0.15
        )
        results.append(
            {
                "asset_id": asset_id,
                "matched_days": len(merged),
                "selected_date_shift_days": shift,
                "price_correlation": correlation,
                "median_abs_relative_difference": median_diff,
                "p95_abs_relative_difference": p95_diff,
                "validation_status": "PASS" if passed else "REVIEW",
            }
        )
    return pd.DataFrame(results)


def main() -> None:
    ensure_directories()
    config = load_config()
    raw = pd.read_csv(RAW_DIR / "raw_market_data.csv")
    registry = pd.read_csv(RAW_DIR / "sample_registry.csv")

    clean_groups = []
    quality_rows = []
    for _, group in raw.groupby("asset_id", sort=False):
        clean, quality = clean_asset(group, config)
        clean_groups.append(clean)
        quality_rows.append(quality)

    clean_panel = pd.concat(clean_groups, ignore_index=True)
    clean_panel = clean_panel.sort_values(["asset_type", "sample_rank", "asset_id", "date_utc"])
    clean_panel["date_utc"] = clean_panel["date_utc"].dt.strftime("%Y-%m-%d")
    clean_panel.to_csv(CLEAN_DIR / "clean_daily_panel.csv", index=False)
    observed = clean_panel[clean_panel["valid_price_flag"]].copy()
    observed.to_csv(CLEAN_DIR / "clean_observed_panel.csv", index=False)

    extreme_review = observed[observed["extreme_return_flag"]].copy()
    extreme_review = extreme_review[
        [
            "date_utc",
            "asset_id",
            "symbol",
            "asset_name",
            "prior_valid_close_usd",
            "close_usd",
            "return_pct",
            "source",
        ]
    ]
    extreme_review["review_status"] = "PENDING"
    extreme_review["review_note"] = ""
    extreme_review.to_csv(QUALITY_DIR / "extreme_return_review.csv", index=False)

    quality = pd.DataFrame(quality_rows).sort_values(["asset_type", "sample_rank", "asset_id"])
    quality.to_csv(QUALITY_DIR / "data_quality_report.csv", index=False)

    observed_for_validation = observed.copy()
    observed_for_validation["date_utc"] = pd.to_datetime(observed_for_validation["date_utc"])
    validation = cross_validate(observed_for_validation)
    validation.to_csv(QUALITY_DIR / "cross_source_validation.csv", index=False)

    cleaning_log = pd.DataFrame(
        [
            ["Preserve raw data", "Raw JSON and CSV files are never overwritten."],
            ["Time standard", "All observations use UTC calendar dates."],
            ["Duplicate handling", "Exact token-date duplicates are flagged; the latest timestamp is retained for processing."],
            ["Invalid prices", "Non-positive prices are flagged and excluded from log transformations."],
            ["Missing dates", "A complete calendar is created from first valid observation to cutoff; prices are not forward-filled."],
            ["Returns", "Daily log returns are calculated only when both the current and previous calendar day have valid prices."],
            ["Extreme returns", f"Absolute log returns above {config['outlier_abs_log_return_pct']}% are flagged but not deleted or winsorized."],
            ["Rolling volatility", f"{config['rolling_volatility_days']}-day return standard deviation, annualized with sqrt({config['annualization_days']})."],
            ["Cross-source validation", "Yahoo closing prices are compared with CoinGecko over the recent validation window, allowing a one-day boundary shift. PASS requires at least 100 matches, correlation >= 0.95, median absolute relative difference <= 5%, and 95th-percentile difference <= 15%."],
        ],
        columns=["step", "rule"],
    )
    cleaning_log.to_csv(QUALITY_DIR / "cleaning_log.csv", index=False)

    data_dictionary = pd.DataFrame(
        [
            ["date_utc", "date", "UTC calendar date", "Source/derived"],
            ["asset_id", "text", "Stable CoinGecko asset identifier", "Registry"],
            ["symbol", "text", "Display ticker; not used as the primary key", "Registry"],
            ["asset_name", "text", "Asset name", "Registry"],
            ["asset_type", "category", "fan_token or benchmark", "Registry"],
            ["sample_rank", "integer", "Candidate rank at sample definition; blank for benchmarks", "Registry"],
            ["open_usd", "number", "Provider-reported daily opening price in USD", "Yahoo"],
            ["high_usd", "number", "Provider-reported daily high price in USD", "Yahoo"],
            ["low_usd", "number", "Provider-reported daily low price in USD", "Yahoo"],
            ["close_usd", "number", "Provider-reported daily closing price in USD", "Yahoo"],
            ["adj_close_usd", "number", "Provider-reported adjusted close in USD", "Yahoo"],
            ["volume_reported", "number", "Provider-reported volume; not assumed comparable in USD across assets", "Yahoo"],
            ["log_price", "number", "Natural logarithm of positive closing price", "Derived"],
            ["prior_valid_close_usd", "number", "Prior calendar day's valid closing price when a consecutive-day return can be calculated", "Derived"],
            ["return_pct", "percentage points", "100 times the one-day difference in log price", "Derived"],
            ["log_volume", "number", "Natural logarithm of one plus non-negative reported volume", "Derived"],
            ["indexed_price_100", "index", "Closing price divided by first valid price times 100", "Derived"],
            ["rolling_volatility_30d_pct_annualized", "percentage points", "Annualized standard deviation of daily log returns over 30 days", "Derived"],
            ["gap_days_since_prior_valid", "integer", "Days since the prior valid closing-price observation", "Derived"],
            ["missing_price_flag", "boolean", "True when no valid positive closing price exists", "Derived"],
            ["zero_volume_flag", "boolean", "True when provider-reported volume equals zero", "Derived"],
            ["extreme_return_flag", "boolean", "True when absolute daily log return exceeds the configured review threshold", "Derived"],
        ],
        columns=["variable", "type_or_unit", "definition", "origin"],
    )
    data_dictionary.to_csv(QUALITY_DIR / "data_dictionary.csv", index=False)

    sources = pd.DataFrame(
        [
            ["CoinGecko fan-token category snapshot", "https://api.coingecko.com/api/v3/coins/markets", "Sample identification and market-cap snapshot"],
            ["Yahoo Finance chart service", "https://query1.finance.yahoo.com/v8/finance/chart/", "Full daily OHLC and reported volume history"],
            ["CoinGecko historical chart validation", "https://api.coingecko.com/api/v3/coins/{id}/market_chart/range", "Recent cross-source price validation"],
        ],
        columns=["source", "url", "use"],
    )
    sources.to_csv(QUALITY_DIR / "source_manifest.csv", index=False)

    fan_quality = quality[quality["asset_type"] == "fan_token"]
    summary = {
        "fan_token_count": int(len(fan_quality)),
        "benchmark_count": int((quality["asset_type"] == "benchmark").sum()),
        "quality_pass_count": int((fan_quality["quality_status"] == "PASS").sum()),
        "quality_review_count": int((fan_quality["quality_status"] != "PASS").sum()),
        "median_coverage_ratio": float(fan_quality["coverage_ratio"].median()),
        "total_valid_fan_token_prices": int(fan_quality["valid_price_days"].sum()),
        "total_extreme_return_flags": int(fan_quality["extreme_return_days"].sum()),
        "cross_validation_pass_count": int((validation.get("validation_status", pd.Series(dtype=str)) == "PASS").sum()),
        "cross_validation_review_count": int((validation.get("validation_status", pd.Series(dtype=str)) != "PASS").sum()),
    }
    write_json(QUALITY_DIR / "validation_summary.json", summary)
    print(
        f"Cleaned {len(clean_panel):,} token-day rows; "
        f"{summary['quality_pass_count']}/{summary['fan_token_count']} fan-token series passed automatic checks."
    )


if __name__ == "__main__":
    main()
