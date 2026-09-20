from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import ANALYSIS_DIR, CLEAN_DIR, QUALITY_DIR, RAW_DIR, ensure_directories, load_config, write_json


def describe_returns(group: pd.DataFrame) -> dict:
    values = group["return_pct"].dropna()
    rolling_vol = group["rolling_volatility_30d_pct_annualized"].dropna()
    return {
        "asset_id": group["asset_id"].iloc[0],
        "symbol": group["symbol"].iloc[0],
        "asset_name": group["asset_name"].iloc[0],
        "sample_rank": group["sample_rank"].iloc[0],
        "return_observations": int(values.size),
        "mean_daily_return_pct": values.mean(),
        "median_daily_return_pct": values.median(),
        "std_daily_return_pct": values.std(ddof=1),
        "minimum_daily_return_pct": values.min(),
        "p01_daily_return_pct": values.quantile(0.01),
        "p05_daily_return_pct": values.quantile(0.05),
        "p95_daily_return_pct": values.quantile(0.95),
        "p99_daily_return_pct": values.quantile(0.99),
        "maximum_daily_return_pct": values.max(),
        "return_skewness": values.skew(),
        "return_excess_kurtosis": values.kurt(),
        "median_annualized_30d_volatility_pct": rolling_vol.median(),
        "maximum_annualized_30d_volatility_pct": rolling_vol.max(),
    }


def diagnostics(group: pd.DataFrame) -> dict:
    returns = group["return_pct"]
    absolute = returns.abs()
    result = {
        "asset_id": group["asset_id"].iloc[0],
        "symbol": group["symbol"].iloc[0],
        "asset_name": group["asset_name"].iloc[0],
        "sample_rank": group["sample_rank"].iloc[0],
    }
    for lag in (1, 5, 10):
        result[f"return_autocorrelation_lag_{lag}"] = returns.autocorr(lag=lag)
        result[f"absolute_return_autocorrelation_lag_{lag}"] = absolute.autocorr(lag=lag)
    return result


def main() -> None:
    ensure_directories()
    config = load_config()
    panel = pd.read_csv(CLEAN_DIR / "clean_observed_panel.csv", parse_dates=["date_utc"])
    quality = pd.read_csv(QUALITY_DIR / "data_quality_report.csv")
    registry = pd.read_csv(RAW_DIR / "sample_registry.csv")
    fan = panel[panel["asset_type"] == "fan_token"].copy()
    benchmarks = panel[panel["asset_type"] == "benchmark"].copy()

    descriptive = pd.DataFrame([describe_returns(group) for _, group in fan.groupby("asset_id", sort=False)])
    descriptive = descriptive.sort_values(["sample_rank", "asset_id"])
    descriptive.to_csv(ANALYSIS_DIR / "descriptive_statistics.csv", index=False)

    diagnostic_table = pd.DataFrame([diagnostics(group) for _, group in fan.groupby("asset_id", sort=False)])
    diagnostic_table = diagnostic_table.sort_values(["sample_rank", "asset_id"])
    diagnostic_table.to_csv(ANALYSIS_DIR / "autocorrelation_diagnostics.csv", index=False)

    returns_wide = panel.pivot_table(index="date_utc", columns="asset_id", values="return_pct", aggfunc="last")
    returns_wide.corr(min_periods=60).to_csv(ANALYSIS_DIR / "return_correlation_matrix.csv")

    benchmark_ids = [asset for asset in ["bitcoin", "ethereum", "chiliz"] if asset in returns_wide.columns]
    correlation_rows = []
    for asset_id, group in fan.groupby("asset_id"):
        for benchmark_id in benchmark_ids:
            pair = pd.concat(
                [
                    group.set_index("date_utc")["return_pct"].rename("fan_return"),
                    benchmarks[benchmarks["asset_id"] == benchmark_id].set_index("date_utc")["return_pct"].rename("benchmark_return"),
                ],
                axis=1,
                join="inner",
            ).dropna()
            correlation_rows.append(
                {
                    "asset_id": asset_id,
                    "symbol": group["symbol"].iloc[0],
                    "benchmark_id": benchmark_id,
                    "overlapping_return_days": len(pair),
                    "return_correlation": pair["fan_return"].corr(pair["benchmark_return"]),
                }
            )
    benchmark_correlations = pd.DataFrame(correlation_rows)
    benchmark_correlations.to_csv(ANALYSIS_DIR / "benchmark_correlations.csv", index=False)

    included_registry = registry[registry["included"].astype(str).str.lower().isin(["true", "1"])].copy()
    sample_overview = quality[quality["asset_type"] == "fan_token"].merge(
        included_registry[
            [
                "coingecko_id",
                "snapshot_market_cap_usd",
                "snapshot_volume_usd",
                "snapshot_market_cap_rank",
                "screening_note",
            ]
        ],
        left_on="asset_id",
        right_on="coingecko_id",
        how="left",
    )
    sample_overview.to_csv(ANALYSIS_DIR / "sample_overview.csv", index=False)

    top_five = (
        sample_overview.sort_values(["snapshot_market_cap_usd", "sample_rank"], ascending=[False, True])
        .head(5)["asset_id"]
        .tolist()
    )
    chart_source = fan[fan["asset_id"].isin(top_five)].copy()
    monthly = (
        chart_source.set_index("date_utc")
        .groupby(["asset_id", "symbol"])
        .resample("ME")
        .agg(
            indexed_price_100=("indexed_price_100", "last"),
            rolling_volatility_30d_pct_annualized=("rolling_volatility_30d_pct_annualized", "mean"),
        )
        .reset_index()
    )
    monthly.to_csv(ANALYSIS_DIR / "monthly_chart_data_long.csv", index=False)
    index_wide = monthly.pivot(index="date_utc", columns="symbol", values="indexed_price_100").reset_index()
    volatility_wide = monthly.pivot(
        index="date_utc", columns="symbol", values="rolling_volatility_30d_pct_annualized"
    ).reset_index()
    index_wide.to_csv(ANALYSIS_DIR / "monthly_indexed_price_top5.csv", index=False)
    volatility_wide.to_csv(ANALYSIS_DIR / "monthly_volatility_top5.csv", index=False)

    overview = {
        "study_title": config["study_title"],
        "data_start_date": str(fan["date_utc"].min().date()),
        "data_cutoff_date": config["cutoff_date"],
        "fan_token_count": int(fan["asset_id"].nunique()),
        "benchmark_count": int(benchmarks["asset_id"].nunique()),
        "fan_token_price_observations": int(fan["close_usd"].notna().sum()),
        "fan_token_return_observations": int(fan["return_pct"].notna().sum()),
        "median_coverage_ratio": float(sample_overview["coverage_ratio"].median()),
        "quality_pass_count": int((sample_overview["quality_status"] == "PASS").sum()),
        "extreme_return_flags": int(sample_overview["extreme_return_days"].sum()),
        "top_five_chart_assets": top_five,
    }
    write_json(ANALYSIS_DIR / "analysis_overview.json", overview)

    most_volatile = descriptive.sort_values("median_annualized_30d_volatility_pct", ascending=False).iloc[0]
    most_kurtotic = descriptive.sort_values("return_excess_kurtosis", ascending=False).iloc[0]
    draft = f"""# Data description and preliminary analysis draft

The dataset contains daily observations for {overview['fan_token_count']} fan tokens and three cryptocurrency benchmarks from {overview['data_start_date']} to {overview['data_cutoff_date']}. The fan-token sample contains {overview['fan_token_price_observations']:,} valid price observations. Tokens enter the unbalanced panel on their first valid trading date, which avoids discarding younger assets solely because they have shorter histories. Daily prices are expressed in US dollars and converted to natural logarithms. Returns are calculated as 100 times the one-day change in log price. Bitcoin, Ethereum and Chiliz are retained as market benchmarks. Provider-reported volume is stored but is not assumed to be directly comparable in US dollars across every asset.

The cleaning procedure converts timestamps to UTC dates, checks token-date uniqueness, creates a complete calendar for each asset and records missing observations without forward-filling prices. Non-positive prices are treated as invalid. Returns are calculated only across consecutive valid calendar days. Extreme movements are flagged for review rather than deleted or winsorized. The median price-coverage ratio is {overview['median_coverage_ratio']:.1%}, and {overview['quality_pass_count']} of {overview['fan_token_count']} fan-token series pass the automatic observation, coverage, duplication and price-validity checks.

Preliminary return statistics show substantial cross-token heterogeneity. {most_volatile['symbol']} has the highest median annualized 30-day volatility in the selected sample, while {most_kurtotic['symbol']} has the highest estimated excess kurtosis. These patterns are descriptive and motivate methods that are robust to changing volatility and heavy-tailed returns. They are not interpreted as evidence of speculative bubbles; explosive-root tests and change-point procedures are required for that conclusion.
"""
    (ANALYSIS_DIR / "draft_data_section.md").write_text(draft, encoding="utf-8")
    print(
        f"Created preliminary statistics for {overview['fan_token_count']} fan tokens "
        f"with {overview['fan_token_return_observations']:,} daily return observations."
    )


if __name__ == "__main__":
    main()
