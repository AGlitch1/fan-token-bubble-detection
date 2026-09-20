from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def run(script: str, *arguments: str) -> None:
    command = [sys.executable, str(SCRIPT_DIR / script), *arguments]
    print(f"Running {script}...")
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FRAM Phase 2 data pipeline.")
    parser.add_argument("--offline", action="store_true", help="Reuse existing raw downloads.")
    parser.add_argument("--skip-cross-validation", action="store_true")
    args = parser.parse_args()

    if not args.offline:
        collection_args = ["--skip-cross-validation"] if args.skip_cross_validation else []
        run("collect_data.py", *collection_args)
    run("clean_validate.py")
    run("preliminary_analysis.py")
    print("Python pipeline complete. Review data/quality and data/analysis before modelling.")


if __name__ == "__main__":
    main()
