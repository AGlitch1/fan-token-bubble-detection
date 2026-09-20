from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_clean_panel_invariants() -> None:
    panel = pd.read_csv(
        ROOT / "data" / "clean" / "clean_observed_panel.csv",
        usecols=["date_utc", "asset_id", "asset_type", "close_usd", "extreme_return_flag"],
    )
    fan = panel[panel["asset_type"] == "fan_token"]
    extreme = pd.read_csv(ROOT / "data" / "quality" / "extreme_return_review.csv")

    assert fan["asset_id"].nunique() == 20
    assert panel.duplicated(["asset_id", "date_utc"]).sum() == 0
    assert panel["close_usd"].gt(0).all()
    assert int(panel["extreme_return_flag"].sum()) == len(extreme)


def test_fixed_cutoff_and_quality_sample() -> None:
    config = json.loads((ROOT / "config" / "project_config.json").read_text(encoding="utf-8"))
    quality = pd.read_csv(ROOT / "data" / "quality" / "data_quality_report.csv")
    fan_quality = quality[quality["asset_type"] == "fan_token"]

    assert config["cutoff_date"] == "2026-09-19"
    assert config["sample_size"] == 20
    assert len(fan_quality) == 20
    assert set(fan_quality["quality_status"]).issubset({"PASS", "REVIEW"})
