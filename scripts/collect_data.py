from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path

import pandas as pd

from common import (
    ANALYSIS_DIR,
    CLEAN_DIR,
    CONFIG_DIR,
    RAW_DIR,
    build_url,
    coingecko_headers,
    ensure_directories,
    get_json,
    load_config,
    read_csv_rows,
    write_json,
)


COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_RANGE = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

BENCHMARKS = [
    {"coingecko_id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "yahoo_symbol": "BTC-USD"},
    {"coingecko_id": "ethereum", "symbol": "ETH", "name": "Ethereum", "yahoo_symbol": "ETH-USD"},
    {"coingecko_id": "chiliz", "symbol": "CHZ", "name": "Chiliz", "yahoo_symbol": "CHZ-USD"},
]


def unix_seconds(day: date) -> int:
    return int(datetime.combine(day, dt_time.min, tzinfo=timezone.utc).timestamp())


def fetch_category_snapshot(config: dict) -> tuple[list[dict], str]:
    url = build_url(
        COINGECKO_MARKETS,
        {
            "vs_currency": "usd",
            "category": "fan-token",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "false",
            "locale": "en",
        },
    )
    data = get_json(
        url,
        timeout=config["http_timeout_seconds"],
        attempts=config["http_max_attempts"],
        extra_headers=coingecko_headers(),
    )
    write_json(RAW_DIR / "coingecko" / "fan_token_category_snapshot.json", data)
    return data, url


def fetch_yahoo_history(asset: dict, config: dict) -> tuple[list[dict], str, dict]:
    start = date.fromisoformat(config["start_date"])
    cutoff = date.fromisoformat(config["cutoff_date"])
    url = build_url(
        YAHOO_CHART.format(symbol=asset["yahoo_symbol"]),
        {
            "period1": unix_seconds(start),
            "period2": unix_seconds(cutoff + timedelta(days=1)),
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        },
    )
    payload = get_json(
        url,
        timeout=config["http_timeout_seconds"],
        attempts=config["http_max_attempts"],
    )
    write_json(RAW_DIR / "yahoo" / f"{asset['coingecko_id']}.json", payload)

    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"Yahoo returned an error for {asset['yahoo_symbol']}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"Yahoo returned no result for {asset['yahoo_symbol']}")

    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    adjclose_blocks = (result.get("indicators") or {}).get("adjclose") or [{}]
    adjclose = adjclose_blocks[0].get("adjclose") or [None] * len(timestamps)

    rows: list[dict] = []
    for index, timestamp in enumerate(timestamps):
        stamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        rows.append(
            {
                "timestamp_utc": stamp.isoformat(),
                "date_utc": stamp.date().isoformat(),
                "asset_id": asset["coingecko_id"],
                "symbol": asset["symbol"],
                "asset_name": asset["name"],
                "asset_type": asset["asset_type"],
                "sample_rank": asset.get("sample_rank"),
                "yahoo_symbol": asset["yahoo_symbol"],
                "open_usd": (quote.get("open") or [None] * len(timestamps))[index],
                "high_usd": (quote.get("high") or [None] * len(timestamps))[index],
                "low_usd": (quote.get("low") or [None] * len(timestamps))[index],
                "close_usd": (quote.get("close") or [None] * len(timestamps))[index],
                "adj_close_usd": adjclose[index] if index < len(adjclose) else None,
                "volume_reported": (quote.get("volume") or [None] * len(timestamps))[index],
                "source": "Yahoo Finance chart service",
            }
        )
    return rows, url, result.get("meta") or {}


def fetch_coingecko_validation(asset: dict, config: dict) -> tuple[list[dict], str]:
    cutoff = date.fromisoformat(config["cutoff_date"])
    start = cutoff - timedelta(days=int(config["cross_validation_days"]) - 1)
    url = build_url(
        COINGECKO_RANGE.format(coin_id=asset["coingecko_id"]),
        {
            "vs_currency": "usd",
            "from": unix_seconds(start),
            "to": unix_seconds(cutoff + timedelta(days=1)),
        },
    )
    payload = get_json(
        url,
        timeout=config["http_timeout_seconds"],
        attempts=config["http_max_attempts"],
        extra_headers=coingecko_headers(),
    )
    write_json(RAW_DIR / "coingecko" / f"validation_{asset['coingecko_id']}.json", payload)
    rows = []
    for timestamp_ms, price in payload.get("prices", []):
        stamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        rows.append(
            {
                "date_utc": stamp.date().isoformat(),
                "asset_id": asset["coingecko_id"],
                "coingecko_price_usd": price,
            }
        )
    return rows, url


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect FRAM fan-token and benchmark market data.")
    parser.add_argument("--skip-cross-validation", action="store_true")
    args = parser.parse_args()

    ensure_directories()
    config = load_config()
    candidates = read_csv_rows(CONFIG_DIR / "candidate_tokens.csv")
    snapshot, snapshot_url = fetch_category_snapshot(config)
    snapshot_by_id = {row["id"]: row for row in snapshot}

    registry_rows: list[dict] = []
    assets_to_collect: list[dict] = []
    for row in candidates:
        cg = snapshot_by_id.get(row["coingecko_id"], {})
        registry = {
            **row,
            "candidate_rank": int(row["candidate_rank"]),
            "snapshot_market_cap_usd": cg.get("market_cap"),
            "snapshot_volume_usd": cg.get("total_volume"),
            "snapshot_market_cap_rank": cg.get("market_cap_rank"),
            "snapshot_last_updated": cg.get("last_updated"),
            "included": False,
            "valid_price_observations": 0,
            "collection_error": "",
        }
        if row["screening_status"].lower() == "eligible":
            assets_to_collect.append(
                {
                    "coingecko_id": row["coingecko_id"],
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "yahoo_symbol": row["yahoo_symbol"],
                    "asset_type": "fan_token",
                    "sample_rank": int(row["candidate_rank"]),
                }
            )
        registry_rows.append(registry)

    collected_rows: list[dict] = []
    request_manifest: list[dict] = [
        {"asset_id": "fan-token-category", "source": "CoinGecko", "request_url": snapshot_url, "status": "OK"}
    ]
    registry_by_id = {row["coingecko_id"]: row for row in registry_rows}

    for asset in assets_to_collect:
        try:
            rows, url, meta = fetch_yahoo_history(asset, config)
            valid_count = sum(
                1 for row in rows if row["close_usd"] is not None and float(row["close_usd"]) > 0
            )
            registry = registry_by_id[asset["coingecko_id"]]
            registry["valid_price_observations"] = valid_count
            registry["included"] = valid_count >= int(config["min_observations"])
            if not registry["included"]:
                registry["screening_note"] = (
                    f"Excluded after collection: only {valid_count} valid price observations"
                )
            else:
                collected_rows.extend(rows)
            request_manifest.append(
                {
                    "asset_id": asset["coingecko_id"],
                    "source": "Yahoo Finance chart service",
                    "request_url": url,
                    "status": "OK",
                    "provider_symbol": meta.get("symbol"),
                    "timezone": meta.get("exchangeTimezoneName"),
                }
            )
        except Exception as exc:
            registry_by_id[asset["coingecko_id"]]["collection_error"] = str(exc)
            request_manifest.append(
                {
                    "asset_id": asset["coingecko_id"],
                    "source": "Yahoo Finance chart service",
                    "request_url": "",
                    "status": f"ERROR: {exc}",
                }
            )
        time.sleep(float(config["request_delay_seconds"]))

    included_count = sum(bool(row["included"]) for row in registry_rows)
    if included_count != int(config["sample_size"]):
        raise RuntimeError(
            f"Expected {config['sample_size']} included fan tokens but collected {included_count}. "
            "Review data/quality/sample_registry.csv and candidate mappings."
        )

    benchmark_assets = []
    for bench in BENCHMARKS:
        asset = {**bench, "asset_type": "benchmark", "sample_rank": None}
        rows, url, meta = fetch_yahoo_history(asset, config)
        collected_rows.extend(rows)
        benchmark_assets.append(asset)
        request_manifest.append(
            {
                "asset_id": asset["coingecko_id"],
                "source": "Yahoo Finance chart service",
                "request_url": url,
                "status": "OK",
                "provider_symbol": meta.get("symbol"),
                "timezone": meta.get("exchangeTimezoneName"),
            }
        )
        time.sleep(float(config["request_delay_seconds"]))

    registry_frame = pd.DataFrame(registry_rows).sort_values("candidate_rank")
    registry_frame.to_csv(RAW_DIR / "sample_registry.csv", index=False)
    market_frame = pd.DataFrame(collected_rows)
    market_frame.to_csv(RAW_DIR / "raw_market_data.csv", index=False)

    validation_rows: list[dict] = []
    do_validation = bool(config["run_cross_source_validation"]) and not args.skip_cross_validation
    if do_validation:
        included_assets = [asset for asset in assets_to_collect if registry_by_id[asset["coingecko_id"]]["included"]]
        validation_assets = included_assets[:2] + benchmark_assets
        for asset in validation_assets:
            try:
                rows, url = fetch_coingecko_validation(asset, config)
                validation_rows.extend(rows)
                request_manifest.append(
                    {
                        "asset_id": asset["coingecko_id"],
                        "source": "CoinGecko validation",
                        "request_url": url,
                        "status": "OK",
                    }
                )
            except Exception as exc:
                request_manifest.append(
                    {
                        "asset_id": asset["coingecko_id"],
                        "source": "CoinGecko validation",
                        "request_url": "",
                        "status": f"UNAVAILABLE: {exc}",
                    }
                )
            time.sleep(float(config["coingecko_validation_delay_seconds"]))

    pd.DataFrame(
        validation_rows,
        columns=["date_utc", "asset_id", "coingecko_price_usd"],
    ).to_csv(RAW_DIR / "coingecko_validation_prices.csv", index=False)
    pd.DataFrame(request_manifest).to_csv(RAW_DIR / "request_manifest.csv", index=False)
    write_json(
        RAW_DIR / "collection_summary.json",
        {
            "snapshot_date": config["snapshot_date"],
            "cutoff_date": config["cutoff_date"],
            "included_fan_tokens": included_count,
            "benchmarks": [asset["coingecko_id"] for asset in benchmark_assets],
            "raw_rows": len(market_frame),
            "cross_validation_rows": len(validation_rows),
        },
    )
    print(f"Collected {len(market_frame):,} raw rows for {included_count} fan tokens and 3 benchmarks.")


if __name__ == "__main__":
    main()
