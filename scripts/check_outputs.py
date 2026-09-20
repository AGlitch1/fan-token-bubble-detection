from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required output is missing: {path.relative_to(PROJECT_ROOT)}")
    return path


def main() -> None:
    config = json.loads(require(PROJECT_ROOT / "config" / "project_config.json").read_text(encoding="utf-8"))
    quality = pd.read_csv(require(PROJECT_ROOT / "data" / "quality" / "data_quality_report.csv"))
    validation = pd.read_csv(require(PROJECT_ROOT / "data" / "quality" / "cross_source_validation.csv"))
    extreme = pd.read_csv(require(PROJECT_ROOT / "data" / "quality" / "extreme_return_review.csv"))
    panel = pd.read_csv(
        require(PROJECT_ROOT / "data" / "clean" / "clean_observed_panel.csv"),
        usecols=["date_utc", "asset_id", "asset_type", "close_usd", "extreme_return_flag"],
    )

    fan_quality = quality[quality["asset_type"] == "fan_token"]
    fan_panel = panel[panel["asset_type"] == "fan_token"]
    duplicate_count = int(panel.duplicated(["asset_id", "date_utc"]).sum())
    nonpositive_count = int((panel["close_usd"] <= 0).sum())
    flagged_count = int(panel["extreme_return_flag"].sum())

    assert config["cutoff_date"] == "2026-09-19", "Unexpected data cutoff"
    assert len(fan_quality) == config["sample_size"] == 20, "Fan-token sample size changed"
    assert fan_panel["asset_id"].nunique() == 20, "Clean panel does not contain 20 fan tokens"
    assert duplicate_count == 0, "Duplicate asset-date keys found"
    assert nonpositive_count == 0, "Non-positive prices found in the observed panel"
    assert flagged_count == len(extreme), "Extreme-return review queue is out of sync"
    assert set(validation["validation_status"]).issubset({"PASS", "REVIEW"}), "Unknown validation status"

    summary = {
        "status": "PASS",
        "fan_tokens": int(fan_panel["asset_id"].nunique()),
        "observed_rows": int(len(panel)),
        "duplicate_asset_dates": duplicate_count,
        "nonpositive_prices": nonpositive_count,
        "extreme_review_rows": int(len(extreme)),
        "cross_source_review_rows": int((validation["validation_status"] == "REVIEW").sum()),
        "cutoff_date": config["cutoff_date"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
