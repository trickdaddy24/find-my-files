import csv
import json
import pytest
from pathlib import Path
import output

SAMPLE = [
    {"name": "main.py",  "path": "C:\\Projects", "size": "4.0 KB", "modified": "2025-11-30", "ext": "py"},
    {"name": "utils.py", "path": "C:\\Projects", "size": "2.0 KB", "modified": "2025-11-29", "ext": "py"},
]
TS = "04252026-103000"


def test_write_csv_creates_file(tmp_path):
    path = output.write_csv(SAMPLE, str(tmp_path), ts=TS)
    assert Path(path).exists()


def test_write_csv_filename_format(tmp_path):
    path = output.write_csv(SAMPLE, str(tmp_path), ts=TS)
    assert Path(path).name == f"fmf-results-{TS}.csv"


def test_write_csv_has_header_and_rows(tmp_path):
    path = output.write_csv(SAMPLE, str(tmp_path), ts=TS)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["name"] == "main.py"
    assert rows[1]["ext"] == "py"


def test_write_csv_columns(tmp_path):
    path = output.write_csv(SAMPLE, str(tmp_path), ts=TS)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        assert set(reader.fieldnames) == {"name", "path", "size", "modified", "ext"}


def test_write_json_creates_file(tmp_path):
    path = output.write_json(SAMPLE, str(tmp_path), ts=TS)
    assert Path(path).exists()


def test_write_json_filename_format(tmp_path):
    path = output.write_json(SAMPLE, str(tmp_path), ts=TS)
    assert Path(path).name == f"fmf-results-{TS}.json"


def test_write_json_content(tmp_path):
    path = output.write_json(SAMPLE, str(tmp_path), ts=TS)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["name"] == "main.py"
    assert data[1]["modified"] == "2025-11-29"


def test_write_outputs_csv_only(tmp_path):
    paths = output.write_outputs(SAMPLE, str(tmp_path), ["CSV"])
    assert len(paths) == 1
    assert paths[0].endswith(".csv")


def test_write_outputs_json_only(tmp_path):
    paths = output.write_outputs(SAMPLE, str(tmp_path), ["JSON"])
    assert len(paths) == 1
    assert paths[0].endswith(".json")


def test_write_outputs_both_share_timestamp(tmp_path):
    paths = output.write_outputs(SAMPLE, str(tmp_path), ["CSV", "JSON"])
    assert len(paths) == 2
    ts_csv  = Path(paths[0]).stem.split("fmf-results-")[1]
    ts_json = Path(paths[1]).stem.split("fmf-results-")[1]
    assert ts_csv == ts_json
