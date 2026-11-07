from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from common import ANALYSIS_DIR, CLEAN_DIR, FINAL_DIR, QUALITY_DIR, ensure_directories, load_config, write_json


# Finite-sample PSY critical values (Table 1, Phillips, Shi and Yu, 2015).
# Values are tabulated for the recommended r0 rule and 2,000 replications.
PSY_T = np.array([100.0, 200.0, 400.0, 800.0, 1600.0])
PSY_CRITICAL_VALUES = {
    "SADF": {
        0.90: np.array([0.98, 1.12, 1.19, 1.25, 1.28]),
        0.95: np.array([1.30, 1.40, 1.49, 1.53, 1.57]),
        0.99: np.array([1.99, 1.90, 2.05, 2.03, 2.22]),
    },
    "GSADF": {
        0.90: np.array([1.65, 1.84, 1.92, 2.10, 2.19]),
        0.95: np.array([2.00, 2.08, 2.20, 2.34, 2.41]),
        0.99: np.array([2.57, 2.70, 2.80, 2.79, 2.87]),
    },
}


def psy_window_size(sample_size: int) -> tuple[float, int]:
    """Return the PSY r0 fraction and its integer minimum window width."""
    r0 = 0.01 + 1.8 / math.sqrt(sample_size)
    return r0, max(20, int(math.floor(r0 * sample_size)))


def critical_value(test: str, confidence: float, sample_size: int) -> float:
    """Interpolate the published finite-sample PSY table by sample size."""
    values = PSY_CRITICAL_VALUES[test][confidence]
    if sample_size < PSY_T[0]:
        slope = (values[1] - values[0]) / (PSY_T[1] - PSY_T[0])
        return float(values[0] + slope * (sample_size - PSY_T[0]))
    if sample_size > PSY_T[-1]:
        slope = (values[-1] - values[-2]) / (PSY_T[-1] - PSY_T[-2])
        return float(values[-1] + slope * (sample_size - PSY_T[-1]))
    return float(np.interp(sample_size, PSY_T, values))


def recursive_adf_statistics(log_prices: np.ndarray, min_window: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute endpoint SADF and BSADF sequences for an intercept, zero-lag ADF."""
    n = len(log_prices)
    sadf = np.full(n, np.nan, dtype=float)
    bsadf = np.full(n, np.nan, dtype=float)
    best_start = np.full(n, -1, dtype=int)
    if n < min_window or min_window < 4:
        return sadf, bsadf, best_start

    lagged = log_prices[:-1]
    differences = np.diff(log_prices)

    def prefix(values: np.ndarray) -> np.ndarray:
        return np.concatenate(([0.0], np.cumsum(values, dtype=float)))

    px = prefix(lagged)
    py = prefix(differences)
    pxx = prefix(lagged * lagged)
    pyy = prefix(differences * differences)
    pxy = prefix(lagged * differences)

    # Vectorize the right-tail t statistics over all admissible left endpoints.
    # The intercept is partialled out using centered sums.
    for end in range(min_window - 1, n):
        starts = np.arange(0, end - min_window + 2, dtype=int)
        rows = end - starts
        sx = px[end] - px[starts]
        sy = py[end] - py[starts]
        sxx = pxx[end] - pxx[starts]
        syy = pyy[end] - pyy[starts]
        sxy = pxy[end] - pxy[starts]

        centered_xx = sxx - sx * sx / rows
        centered_xy = sxy - sx * sy / rows
        centered_yy = syy - sy * sy / rows
        valid = (rows > 2) & (centered_xx > 0.0)
        beta = np.full(len(starts), np.nan, dtype=float)
        beta[valid] = centered_xy[valid] / centered_xx[valid]
        residual_ss = centered_yy - beta * centered_xy
        residual_ss = np.maximum(residual_ss, np.finfo(float).tiny)
        variance = residual_ss / np.maximum(rows - 2, 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            statistics = beta * np.sqrt(centered_xx / variance)
        statistics[~valid] = np.nan

        if np.isfinite(statistics).any():
            local = int(np.nanargmax(statistics))
            bsadf[end] = float(statistics[local])
            best_start[end] = int(starts[local])
            zero_start = np.flatnonzero(starts == 0)
            if len(zero_start):
                sadf[end] = float(statistics[int(zero_start[0])])

    return sadf, bsadf, best_start


def contiguous_blocks(group: pd.DataFrame) -> list[pd.DataFrame]:
    valid = group[group["log_price"].notna() & group["close_usd"].gt(0)].copy()
    if valid.empty:
        return []
    valid["date_utc"] = pd.to_datetime(valid["date_utc"])
    valid = valid.sort_values("date_utc").reset_index(drop=True)
    block_id = valid["date_utc"].diff().dt.days.ne(1).cumsum()
    return [block.reset_index(drop=True) for _, block in valid.groupby(block_id, sort=False)]


def stamp_episodes(
    dates: pd.Series,
    bsadf: np.ndarray,
    critical_sequence: np.ndarray,
    minimum_duration: int,
    confidence: float,
    asset: dict,
    block_index: int,
) -> list[dict]:
    above = np.isfinite(bsadf) & np.isfinite(critical_sequence) & (bsadf > critical_sequence)
    positions = np.flatnonzero(above)
    if not len(positions):
        return []
    groups = np.split(positions, np.flatnonzero(np.diff(positions) > 1) + 1)
    episodes = []
    for episode_number, indexes in enumerate(groups, start=1):
        if len(indexes) < minimum_duration:
            continue
        peak_index = int(indexes[np.nanargmax(bsadf[indexes])])
        episodes.append(
            {
                **asset,
                "block_index": block_index,
                "episode_number": episode_number,
                "confidence_level": confidence,
                "start_date": dates.iloc[int(indexes[0])].date().isoformat(),
                "end_date": dates.iloc[int(indexes[-1])].date().isoformat(),
                "peak_date": dates.iloc[peak_index].date().isoformat(),
                "duration_days": int(len(indexes)),
                "peak_bsadf": float(bsadf[peak_index]),
                "minimum_duration_days": int(minimum_duration),
                "right_censored": bool(int(indexes[-1]) == len(dates) - 1),
            }
        )
    return episodes


def standardized(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    center = float(np.mean(values))
    scale = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    if not np.isfinite(scale) or scale <= np.finfo(float).eps:
        return np.zeros_like(values)
    return (values - center) / scale


def optimal_mean_change_points(values: np.ndarray, min_segment: int, penalty_multiplier: float) -> list[int]:
    """Exact penalized dynamic programming for Gaussian mean shifts."""
    x = standardized(values)
    n = len(x)
    if n < 2 * min_segment:
        return []
    penalty = penalty_multiplier * math.log(n)
    prefix = np.concatenate(([0.0], np.cumsum(x)))
    prefix_sq = np.concatenate(([0.0], np.cumsum(x * x)))

    def segment_cost(starts: np.ndarray, end: int) -> np.ndarray:
        size = end - starts
        total = prefix[end] - prefix[starts]
        square_total = prefix_sq[end] - prefix_sq[starts]
        return np.maximum(square_total - total * total / size, 0.0)

    objective = np.full(n + 1, np.inf, dtype=float)
    previous = np.full(n + 1, -1, dtype=int)
    objective[0] = -penalty
    for end in range(min_segment, n + 1):
        starts = np.arange(0, end - min_segment + 1, dtype=int)
        feasible = np.isfinite(objective[starts])
        starts = starts[feasible]
        if not len(starts):
            continue
        scores = objective[starts] + segment_cost(starts, end) + penalty
        best = int(np.argmin(scores))
        objective[end] = float(scores[best])
        previous[end] = int(starts[best])

    if previous[n] < 0:
        return []
    boundaries = []
    end = n
    while end > 0:
        start = int(previous[end])
        if start <= 0:
            break
        boundaries.append(start)
        end = start
    return sorted(boundaries)


def change_point_outputs(group: pd.DataFrame, asset: dict, min_segment: int, penalty_multiplier: float) -> tuple[list[dict], list[dict]]:
    changes: list[dict] = []
    segments: list[dict] = []
    returns = pd.to_numeric(group["return_pct"], errors="coerce")
    dates = pd.to_datetime(group["date_utc"], errors="coerce")
    valid = returns.notna() & dates.notna()
    observed = pd.DataFrame({"date_utc": dates[valid].to_numpy(), "return_pct": returns[valid].to_numpy()})
    if len(observed) < 2 * min_segment:
        return changes, segments

    vol_scale = float(np.std(observed["return_pct"], ddof=1))
    if not np.isfinite(vol_scale) or vol_scale <= 0:
        vol_scale = 1.0
    raw_returns = observed["return_pct"].to_numpy(dtype=float)
    series = {
        "return_mean": raw_returns / vol_scale,
        "log_squared_return": np.log(np.square(raw_returns / vol_scale) + 1e-8),
    }
    for dimension, values in series.items():
        boundaries = optimal_mean_change_points(values, min_segment, penalty_multiplier)
        edges = [0, *boundaries, len(observed)]
        for segment_number, (start, end) in enumerate(zip(edges[:-1], edges[1:]), start=1):
            segment_returns = observed["return_pct"].iloc[start:end]
            segments.append(
                {
                    **asset,
                    "dimension": dimension,
                    "segment_number": segment_number,
                    "start_date": observed["date_utc"].iloc[start].date().isoformat(),
                    "end_date": observed["date_utc"].iloc[end - 1].date().isoformat(),
                    "observations": int(end - start),
                    "mean_daily_log_return_pct": float(segment_returns.mean()),
                    "annualized_volatility_pct": float(segment_returns.std(ddof=1) * math.sqrt(365)),
                }
            )
        for change_number, boundary in enumerate(boundaries, start=1):
            left = observed["return_pct"].iloc[max(0, boundary - min_segment):boundary]
            right = observed["return_pct"].iloc[boundary:min(len(observed), boundary + min_segment)]
            changes.append(
                {
                    **asset,
                    "dimension": dimension,
                    "change_number": change_number,
                    "change_date": observed["date_utc"].iloc[boundary].date().isoformat(),
                    "minimum_segment_days": int(min_segment),
                    "penalty": float(penalty_multiplier * math.log(len(observed))),
                    "penalty_multiplier": float(penalty_multiplier),
                    "left_window_mean_return_pct": float(left.mean()),
                    "right_window_mean_return_pct": float(right.mean()),
                    "left_window_annualized_volatility_pct": float(left.std(ddof=1) * math.sqrt(365)),
                    "right_window_annualized_volatility_pct": float(right.std(ddof=1) * math.sqrt(365)),
                }
            )
    return changes, segments


def normal_cdf_approx(z: np.ndarray) -> np.ndarray:
    """Vectorized standard-normal CDF approximation (maximum error below 8e-8)."""
    z = np.asarray(z, dtype=float)
    absolute = np.abs(z)
    t = 1.0 / (1.0 + 0.2316419 * absolute)
    density = 0.3989422804014327 * np.exp(-0.5 * absolute * absolute)
    tail = density * t * (
        0.319381530
        + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429)))
    )
    return np.where(z >= 0, 1.0 - tail, tail)


def bayesian_online_adf(
    log_prices: np.ndarray,
    dates: pd.Series,
    hazard_days: int,
    slope_prior_sd: float,
) -> list[dict]:
    """Bayesian online change-point model for the local right-tailed ADF slope."""
    if len(log_prices) < 3:
        return []
    differences = np.diff(log_prices)
    difference_scale = float(np.std(differences, ddof=1))
    level_scale = float(np.std(log_prices, ddof=1))
    if difference_scale <= np.finfo(float).eps or level_scale <= np.finfo(float).eps:
        return []

    response = differences / difference_scale
    levels = (log_prices[:-1] - float(np.mean(log_prices))) / level_scale
    hazard = min(0.5, 1.0 / max(2, hazard_days))

    prior_mean = np.array([0.0, 0.0], dtype=float)
    prior_cov = np.diag([4.0, slope_prior_sd * slope_prior_sd]).astype(float)
    means = prior_mean.reshape(1, 2)
    covariances = prior_cov.reshape(1, 2, 2)
    run_probabilities = np.array([1.0], dtype=float)
    records = []

    for index, (target, level) in enumerate(zip(response, levels), start=1):
        predictor = np.array([1.0, float(level)])
        cov_x = covariances @ predictor
        predictive_variance = 1.0 + cov_x @ predictor
        predictive_mean = means @ predictor
        log_likelihood = -0.5 * (
            math.log(2.0 * math.pi) + np.log(predictive_variance)
            + np.square(target - predictive_mean) / predictive_variance
        )

        prior_cov_x = prior_cov @ predictor
        prior_predictive_variance = float(1.0 + predictor @ prior_cov_x)
        prior_predictive_mean = float(predictor @ prior_mean)
        prior_log_likelihood = -0.5 * (
            math.log(2.0 * math.pi * prior_predictive_variance)
            + (target - prior_predictive_mean) ** 2 / prior_predictive_variance
        )

        log_growth = np.log(np.maximum(run_probabilities, np.finfo(float).tiny)) + log_likelihood + math.log1p(-hazard)
        log_reset = math.log(hazard) + prior_log_likelihood
        joint_logs = np.concatenate(([log_reset], log_growth))
        max_log = float(np.max(joint_logs))
        posterior_runs = np.exp(joint_logs - max_log)
        posterior_runs /= posterior_runs.sum()

        gains = cov_x / predictive_variance[:, None]
        updated_means = means + gains * (target - predictive_mean)[:, None]
        updated_covariances = covariances - np.einsum("ri,rj->rij", gains, cov_x)
        updated_covariances = 0.5 * (updated_covariances + np.swapaxes(updated_covariances, 1, 2))

        prior_gain = prior_cov_x / prior_predictive_variance
        reset_mean = prior_mean + prior_gain * (target - prior_predictive_mean)
        reset_cov = prior_cov - np.outer(prior_gain, prior_cov_x)
        means = np.vstack((reset_mean, updated_means))
        covariances = np.concatenate((reset_cov.reshape(1, 2, 2), updated_covariances), axis=0)
        run_probabilities = posterior_runs

        slope_mean = means[:, 1]
        slope_variance = np.maximum(covariances[:, 1, 1], np.finfo(float).tiny)
        positive_probability = float(np.dot(run_probabilities, normal_cdf_approx(slope_mean / np.sqrt(slope_variance))))
        mixture_mean = float(np.dot(run_probabilities, slope_mean))
        mixture_variance = float(
            np.dot(run_probabilities, slope_variance + slope_mean * slope_mean) - mixture_mean * mixture_mean
        )
        records.append(
            {
                "date_utc": dates.iloc[index].date().isoformat(),
                "bayesian_change_point_probability": float(run_probabilities[0]),
                "bayesian_explosive_slope_probability": positive_probability,
                "bayesian_adf_slope_mean_standardized": mixture_mean,
                "bayesian_adf_slope_sd_standardized": math.sqrt(max(mixture_variance, 0.0)),
                "posterior_expected_run_length_days": float(
                    np.dot(run_probabilities, np.arange(len(run_probabilities)))
                ),
            }
        )
    return records


def main() -> None:
    ensure_directories()
    config = load_config()
    phase3 = config["phase3"]
    panel = pd.read_csv(CLEAN_DIR / "clean_daily_panel.csv", parse_dates=["date_utc"])
    quality = pd.read_csv(QUALITY_DIR / "data_quality_report.csv")
    fan_quality = quality[quality["asset_type"] == "fan_token"]
    if len(fan_quality) != int(config["sample_size"]) or not fan_quality["quality_status"].eq("PASS").all():
        raise RuntimeError("Phase 3 requires the fixed fan-token sample to pass every data-quality check.")

    analysis_assets = panel[panel["asset_type"].isin(["fan_token", "benchmark"])].copy()
    psy_rows: list[dict] = []
    bsadf_rows: list[dict] = []
    episode_rows: list[dict] = []
    change_rows: list[dict] = []
    segment_rows: list[dict] = []
    bayesian_rows: list[dict] = []
    skipped_blocks: list[dict] = []

    for asset_id, group in analysis_assets.groupby("asset_id", sort=False):
        first = group.iloc[0]
        asset = {
            "asset_id": asset_id,
            "symbol": first["symbol"],
            "asset_name": first["asset_name"],
            "asset_type": first["asset_type"],
            "sample_rank": first["sample_rank"],
        }
        for block_index, block in enumerate(contiguous_blocks(group), start=1):
            prices = block["log_price"].to_numpy(dtype=float)
            dates = pd.to_datetime(block["date_utc"]).reset_index(drop=True)
            n = len(prices)
            if n < int(phase3["minimum_observations"]):
                skipped_blocks.append(
                    {**asset, "block_index": block_index, "observations": n, "reason": "below minimum observations"}
                )
                continue

            r0, min_window = psy_window_size(n)
            sadf, bsadf, best_start = recursive_adf_statistics(prices, min_window)
            if not np.isfinite(sadf).any() or not np.isfinite(bsadf).any():
                skipped_blocks.append(
                    {**asset, "block_index": block_index, "observations": n, "reason": "degenerate ADF regressions"}
                )
                continue
            global_sadf = float(np.nanmax(sadf))
            global_gsadf = float(np.nanmax(bsadf))
            summary = {
                **asset,
                "block_index": block_index,
                "start_date": dates.iloc[0].date().isoformat(),
                "end_date": dates.iloc[-1].date().isoformat(),
                "observations": n,
                "r0_fraction": r0,
                "minimum_window_days": min_window,
                "adf_lags": 0,
                "sadf_statistic": global_sadf,
                "gsadf_statistic": global_gsadf,
            }
            for confidence in (0.90, 0.95, 0.99):
                sadf_cv = critical_value("SADF", confidence, n)
                gsadf_cv = critical_value("GSADF", confidence, n)
                suffix = int(confidence * 100)
                summary[f"sadf_cv_{suffix}"] = sadf_cv
                summary[f"gsadf_cv_{suffix}"] = gsadf_cv
                summary[f"sadf_reject_{suffix}"] = bool(global_sadf > sadf_cv)
                summary[f"gsadf_reject_{suffix}"] = bool(global_gsadf > gsadf_cv)
            psy_rows.append(summary)

            endpoint_cv_by_confidence = {
                confidence: np.array(
                    [
                        critical_value("SADF", confidence, endpoint + 1) if np.isfinite(bsadf[endpoint]) else np.nan
                        for endpoint in range(n)
                    ],
                    dtype=float,
                )
                for confidence in (0.90, 0.95, 0.99)
            }
            for endpoint in np.flatnonzero(np.isfinite(bsadf)):
                endpoint_length = int(endpoint + 1)
                start_index = int(best_start[endpoint])
                bsadf_rows.append(
                    {
                        **asset,
                        "block_index": block_index,
                        "date_utc": dates.iloc[endpoint].date().isoformat(),
                        "endpoint_observations": endpoint_length,
                        "sadf_statistic": sadf[endpoint],
                        "bsadf_statistic": bsadf[endpoint],
                        "bsadf_best_window_start_date": dates.iloc[start_index].date().isoformat(),
                        "sadf_95pct_critical_value": endpoint_cv_by_confidence[0.95][endpoint],
                        "bsadf_above_95pct_critical_value": bool(
                            bsadf[endpoint] > endpoint_cv_by_confidence[0.95][endpoint]
                        ),
                    }
                )

            minimum_duration = max(
                int(phase3["minimum_bubble_duration_days"]),
                int(math.ceil(math.log(n))),
            )
            for confidence, endpoint_cv in endpoint_cv_by_confidence.items():
                episode_rows.extend(
                    stamp_episodes(dates, bsadf, endpoint_cv, minimum_duration, confidence, asset, block_index)
                )

            cp_rows, cp_segments = change_point_outputs(
                block,
                {**asset, "block_index": block_index},
                int(phase3["minimum_segment_days"]),
                float(phase3["change_point_penalty_multiplier"]),
            )
            change_rows.extend(cp_rows)
            segment_rows.extend(cp_segments)
            for record in bayesian_online_adf(
                prices,
                dates,
                int(phase3["bayesian_hazard_days"]),
                float(phase3["bayesian_slope_prior_sd"]),
            ):
                bayesian_rows.append({**asset, "block_index": block_index, **record})

    psy = pd.DataFrame(psy_rows)
    bsadf_series = pd.DataFrame(bsadf_rows)
    episodes = pd.DataFrame(episode_rows)
    change_points = pd.DataFrame(change_rows)
    change_segments = pd.DataFrame(segment_rows)
    bayesian = pd.DataFrame(bayesian_rows)

    psy.to_csv(ANALYSIS_DIR / "psy_test_summary.csv", index=False)
    bsadf_series.to_csv(ANALYSIS_DIR / "psy_bsadf_series.csv", index=False)
    episodes.to_csv(ANALYSIS_DIR / "psy_bubble_episodes.csv", index=False)
    change_points.to_csv(ANALYSIS_DIR / "change_points.csv", index=False)
    change_segments.to_csv(ANALYSIS_DIR / "change_point_segments.csv", index=False)
    bayesian.to_csv(ANALYSIS_DIR / "bayesian_online_diagnostics.csv", index=False)
    write_json(ANALYSIS_DIR / "phase3_skipped_blocks.json", skipped_blocks)

    fan_type = psy.get("asset_type", pd.Series(dtype=str)).eq("fan_token")
    gsadf_reject = psy.get("gsadf_reject_95", pd.Series(dtype=bool)).fillna(False)
    fan_episodes = episodes.get("asset_type", pd.Series(dtype=str)).eq("fan_token")
    episode_confidence = episodes.get("confidence_level", pd.Series(dtype=float)).eq(0.95)
    overview = {
        "study_title": config["study_title"],
        "data_cutoff_date": config["cutoff_date"],
        "test_series_count": int(len(psy)),
        "fan_token_series_count": int(fan_type.sum()),
        "benchmark_series_count": int(psy.get("asset_type", pd.Series(dtype=str)).eq("benchmark").sum()),
        "fan_tokens_reject_gsadf_5pct": int((fan_type & gsadf_reject).sum()),
        "fan_token_bubble_episodes_5pct": int((fan_episodes & episode_confidence).sum()),
        "change_point_count": int(len(change_points)),
        "bayesian_daily_rows": int(len(bayesian)),
        "skipped_blocks": int(len(skipped_blocks)),
        "critical_value_method": "PSY 2015 finite-sample table; endpoint SADF path interpolated/extrapolated by endpoint length with the full-block minimum window",
        "bayesian_model": "Gaussian online change-point model with fixed standardized innovation variance and a local ADF slope",
    }
    write_json(ANALYSIS_DIR / "phase3_analysis_overview.json", overview)

    top_episodes = "No 5% date-stamped episodes passed the minimum-duration rule."
    if not episodes.empty:
        significant = episodes[(episodes["confidence_level"] == 0.95) & (episodes["asset_type"] == "fan_token")]
        if not significant.empty:
            top_episodes = "\n".join(
                f"- {row.symbol}: {row.start_date} to {row.end_date} ({row.duration_days} days; peak BSADF {row.peak_bsadf:.2f}; {'ongoing at cutoff' if row.right_censored else 'ended'})"
                for row in significant.sort_values(["start_date", "asset_id"]).itertuples()
            )
    report = f"""# Phase 3 formal analysis summary

The fixed Phase 2 panel was analyzed through {config['cutoff_date']}. Recursive right-tailed ADF statistics were computed for {overview['fan_token_series_count']} fan-token series and {overview['benchmark_series_count']} benchmark series. The fan-token GSADF tests reject the unit-root null at 5% for {overview['fan_tokens_reject_gsadf_5pct']} of 20 tokens using interpolated finite-sample PSY critical values.

The 5% BSADF dating procedure returned {overview['fan_token_bubble_episodes_5pct']} fan-token episodes that met the {phase3['minimum_bubble_duration_days']}-day minimum-duration rule:

{top_episodes}

Penalized dynamic programming identified {overview['change_point_count']} mean or log-volatility change points across the 20 fan tokens and three benchmarks. The Bayesian online model generated {overview['bayesian_daily_rows']:,} daily posterior records. These methods identify statistical patterns; they do not establish the economic cause of an episode.

Critical values and implementation choices are documented in docs/PHASE_3_ANALYSIS.md. For date-stamping, the recursion keeps the full-block minimum window while its endpoint critical values are interpolated from the published SADF table by endpoint length. This is an approximation, not endpoint-specific simulation or a series-specific bootstrap; interpret marginal dates and tests with that limitation in mind.
"""
    (ANALYSIS_DIR / "phase3_formal_analysis_summary.md").write_text(report, encoding="utf-8")
    (FINAL_DIR / "PHASE3_FORMAL_ANALYSIS.md").write_text(report, encoding="utf-8")
    print(
        f"Phase 3 analyzed {overview['fan_token_series_count']} fan tokens and "
        f"{overview['benchmark_series_count']} benchmarks; "
        f"{overview['fan_tokens_reject_gsadf_5pct']} fan tokens reject GSADF at 5%."
    )


if __name__ == "__main__":
    main()
