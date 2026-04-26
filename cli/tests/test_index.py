from pathlib import Path
from unittest.mock import patch
import index


def _make(tmp_path, *rel_paths):
    for rel in rel_paths:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")


def test_build_returns_file_count(tmp_path):
    _make(tmp_path, "a.py", "b.txt", "c.py")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        count = index.build(str(tmp_path), exclude_dirs=[])
    assert count == 3


def test_build_excludes_dirs(tmp_path):
    _make(tmp_path, "src/main.py", "venv/lib.py")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        count = index.build(str(tmp_path), exclude_dirs=["venv"])
    assert count == 1


def test_query_by_extension(tmp_path):
    _make(tmp_path, "main.py", "utils.py", "readme.txt")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        index.build(str(tmp_path), exclude_dirs=[])
        results = index.query([str(tmp_path)], term=None, use_regex=False, ext_filter=".py")
    names = {r["name"] for r in results}
    assert "main.py" in names
    assert "utils.py" in names
    assert "readme.txt" not in names


def test_query_by_name_plain(tmp_path):
    _make(tmp_path, "report.xlsx", "invoice.xlsx", "report_v2.xlsx")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        index.build(str(tmp_path), exclude_dirs=[])
        results = index.query([str(tmp_path)], term="report", use_regex=False, ext_filter=None)
    names = {r["name"] for r in results}
    assert "report.xlsx" in names
    assert "report_v2.xlsx" in names
    assert "invoice.xlsx" not in names


def test_query_by_name_regex(tmp_path):
    _make(tmp_path, "report_2025.csv", "report_2024.csv", "notes.csv")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        index.build(str(tmp_path), exclude_dirs=[])
        results = index.query(
            [str(tmp_path)], term=r"report_\d{4}", use_regex=True, ext_filter=None
        )
    names = {r["name"] for r in results}
    assert "report_2025.csv" in names
    assert "report_2024.csv" in names
    assert "notes.csv" not in names


def test_get_meta_missing(tmp_path):
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        result = index.get_meta("C:\\")
    assert result is None


def test_get_meta_after_build(tmp_path):
    _make(tmp_path, "a.txt", "b.txt")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        index.build(str(tmp_path), exclude_dirs=[])
        meta = index.get_meta(str(tmp_path))
    assert meta is not None
    assert meta["file_count"] == 2
    assert meta["drive"] == str(tmp_path)
    assert "indexed_at" in meta


def test_build_replaces_existing_index(tmp_path):
    # Use a subdirectory for the drive so the db file (in tmp_path root)
    # isn't picked up by the walk.
    drive = tmp_path / "drive"
    drive.mkdir()
    _make(drive, "a.py", "b.py", "c.py")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        index.build(str(drive), exclude_dirs=[])
        (drive / "c.py").unlink()
        count = index.build(str(drive), exclude_dirs=[])
    assert count == 2


def test_list_all_empty(tmp_path):
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        result = index.list_all()
    assert result == []


def test_list_all_after_build(tmp_path):
    _make(tmp_path, "x.txt")
    db = tmp_path / "idx.db"
    with patch.object(index, "INDEX_FILE", db):
        index.build(str(tmp_path), exclude_dirs=[])
        result = index.list_all()
    assert len(result) == 1
    assert result[0]["drive"] == str(tmp_path)
