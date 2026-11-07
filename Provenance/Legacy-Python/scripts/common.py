from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
QUALITY_DIR = DATA_DIR / "quality"
ANALYSIS_DIR = DATA_DIR / "analysis"
FINAL_DIR = PROJECT_ROOT / "outputs"


def ensure_directories() -> None:
    for path in (
        RAW_DIR / "coingecko",
        RAW_DIR / "yahoo",
        CLEAN_DIR,
        QUALITY_DIR,
        ANALYSIS_DIR,
        FINAL_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    return json.loads((CONFIG_DIR / "project_config.json").read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def build_url(base: str, params: dict[str, Any]) -> str:
    clean = {k: v for k, v in params.items() if v is not None}
    return f"{base}?{urllib.parse.urlencode(clean)}"


def get_json(
    url: str,
    *,
    timeout: int,
    attempts: int,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    headers = {
        "User-Agent": "FRAM-fan-token-research/1.0",
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts:
                body = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {exc.code} for {url}: {body[:500]}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2 ** attempt, 30)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == attempts:
                raise RuntimeError(f"Network failure for {url}: {exc}") from exc
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"Failed to retrieve {url}: {last_error}")


def coingecko_headers() -> dict[str, str]:
    key = os.environ.get("COINGECKO_API_KEY", "").strip()
    return {"x-cg-demo-api-key": key} if key else {}
