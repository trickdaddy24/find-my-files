import csv
import json
from datetime import datetime
from pathlib import Path

# Required keys in each result dict passed to write_* functions.
# Matches the fields returned by search.search().
FIELDS = ["name", "path", "size", "modified", "ext"]


def _timestamp() -> str:
    return datetime.now().strftime("%m%d%Y-%H%M%S")


def write_csv(results: list[dict], output_dir: str | Path, ts: str | None = None) -> str:
    ts = ts or _timestamp()
    filepath = str(Path(output_dir) / f"fmf-results-{ts}.csv")
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    return filepath


def write_json(results: list[dict], output_dir: str | Path, ts: str | None = None) -> str:
    ts = ts or _timestamp()
    filepath = str(Path(output_dir) / f"fmf-results-{ts}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return filepath


def write_outputs(results: list[dict], output_dir: str | Path, formats: list[str]) -> list[str]:
    ts = _timestamp()
    paths = []
    if "CSV" in formats:
        paths.append(write_csv(results, output_dir, ts))
    if "JSON" in formats:
        paths.append(write_json(results, output_dir, ts))
    return paths
