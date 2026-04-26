import pytest
from pathlib import Path
import search


def _make(tmp_path, *rel_paths):
    """Create empty files at given relative paths inside tmp_path."""
    for rel in rel_paths:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")


def test_name_search_plain(tmp_path):
    _make(tmp_path, "report.txt", "invoice.txt", "report_backup.xlsx")
    results = search.search([str(tmp_path)], term="report", use_regex=False,
                            ext_filter=None, exclude_dirs=[])
    names = {r["name"] for r in results}
    assert "report.txt" in names
    assert "report_backup.xlsx" in names
    assert "invoice.txt" not in names


def test_name_search_case_insensitive(tmp_path):
    _make(tmp_path, "Report.TXT")
    results = search.search([str(tmp_path)], term="report", use_regex=False,
                            ext_filter=None, exclude_dirs=[])
    assert len(results) == 1


def test_name_search_regex(tmp_path):
    _make(tmp_path, "report_2025.txt", "report_2024.txt", "invoice.txt")
    results = search.search([str(tmp_path)], term=r"report_\d{4}", use_regex=True,
                            ext_filter=None, exclude_dirs=[])
    names = {r["name"] for r in results}
    assert "report_2025.txt" in names
    assert "report_2024.txt" in names
    assert "invoice.txt" not in names


def test_extension_only_dotpy(tmp_path):
    _make(tmp_path, "main.py", "utils.py", "readme.txt")
    results = search.search([str(tmp_path)], term=None, use_regex=False,
                            ext_filter=".py", exclude_dirs=[])
    names = {r["name"] for r in results}
    assert "main.py" in names
    assert "utils.py" in names
    assert "readme.txt" not in names


def test_extension_normalization_star_dot(tmp_path):
    _make(tmp_path, "data.xlsx")
    results = search.search([str(tmp_path)], term=None, use_regex=False,
                            ext_filter="*.xlsx", exclude_dirs=[])
    assert len(results) == 1


def test_extension_normalization_no_dot(tmp_path):
    _make(tmp_path, "data.xlsx")
    results = search.search([str(tmp_path)], term=None, use_regex=False,
                            ext_filter="xlsx", exclude_dirs=[])
    assert len(results) == 1


def test_both_mode(tmp_path):
    _make(tmp_path, "report.py", "report.txt", "notes.py")
    results = search.search([str(tmp_path)], term="report", use_regex=False,
                            ext_filter=".py", exclude_dirs=[])
    names = {r["name"] for r in results}
    assert "report.py" in names
    assert "report.txt" not in names
    assert "notes.py" not in names


def test_exclude_dirs(tmp_path):
    _make(tmp_path, "node_modules/index.py", "src/main.py")
    results = search.search([str(tmp_path)], term=None, use_regex=False,
                            ext_filter=".py", exclude_dirs=["node_modules"])
    names = {r["name"] for r in results}
    assert "main.py" in names
    assert "index.py" not in names


def test_result_fields(tmp_path):
    _make(tmp_path, "test.py")
    results = search.search([str(tmp_path)], term=None, use_regex=False,
                            ext_filter=".py", exclude_dirs=[])
    assert len(results) == 1
    r = results[0]
    assert r["name"] == "test.py"
    assert r["ext"] == "py"
    assert r["path"] == str(tmp_path)
    assert "size" in r
    assert "modified" in r


def test_results_sorted_by_modified_descending(tmp_path):
    import time
    _make(tmp_path, "old.py")
    time.sleep(0.05)
    _make(tmp_path, "new.py")
    results = search.search([str(tmp_path)], term=None, use_regex=False,
                            ext_filter=".py", exclude_dirs=[])
    assert results[0]["name"] == "new.py"


def test_no_crash_on_empty_drives(tmp_path):
    results = search.search([], term="anything", use_regex=False,
                            ext_filter=None, exclude_dirs=[])
    assert results == []
