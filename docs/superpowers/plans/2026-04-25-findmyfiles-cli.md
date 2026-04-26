# Find My Files CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python interactive wizard CLI (`cli/fmf.py`) that searches drives by filename and/or extension, supports regex, and exports results to CSV/JSON.

**Architecture:** Four focused modules — `settings.py` (persist defaults), `search.py` (os.walk engine), `output.py` (file writers), `fmf.py` (wizard orchestration). `fmf.py` calls the other three; they never call each other. Tests live in `cli/tests/` and use pytest.

**Tech Stack:** Python 3.10+, `questionary` (interactive prompts), `rich` (terminal table + spinner), `psutil` (drive detection), `pytest` (tests).

---

## File Map

| File | Role |
|---|---|
| `cli/requirements.txt` | Dependencies |
| `cli/tests/conftest.py` | Adds `cli/` to sys.path for all tests |
| `cli/settings.py` | Load/save `~/.fmf/settings.json` |
| `cli/tests/test_settings.py` | Tests for settings.py |
| `cli/search.py` | os.walk search engine |
| `cli/tests/test_search.py` | Tests for search.py |
| `cli/output.py` | CSV + JSON writers |
| `cli/tests/test_output.py` | Tests for output.py |
| `cli/fmf.py` | Wizard entry point |

---

## Task 1: Project Scaffold

**Files:**
- Create: `cli/requirements.txt`
- Create: `cli/tests/conftest.py`

- [ ] **Step 1: Create `cli/requirements.txt`**

```
questionary
rich
psutil
```

- [ ] **Step 2: Create `cli/tests/conftest.py`**

```python
import sys
from pathlib import Path

# Make the cli/ directory importable from tests
sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r cli/requirements.txt
```

Expected: packages install without error.

- [ ] **Step 4: Verify pytest is available**

```bash
pytest cli/tests/ --collect-only
```

Expected: `no tests ran` (no test files yet) — confirms pytest finds the test directory.

- [ ] **Step 5: Commit**

```bash
git add cli/requirements.txt cli/tests/conftest.py
git commit -m "feat: scaffold cli/ with requirements and test setup"
```

---

## Task 2: Settings Module

**Files:**
- Create: `cli/settings.py`
- Create: `cli/tests/test_settings.py`

- [ ] **Step 1: Write the failing tests**

Create `cli/tests/test_settings.py`:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch
import settings


def test_load_returns_defaults_when_file_missing(tmp_path):
    with patch.object(settings, "SETTINGS_FILE", tmp_path / "nonexistent.json"), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        result = settings.load()
    assert result["mode"] == "Name search"
    assert result["exclude_dirs"] == ["node_modules", ".git", "Windows"]
    assert result["drives"] == []
    assert result["use_regex"] is False


def test_save_creates_file(tmp_path):
    test_file = tmp_path / "settings.json"
    with patch.object(settings, "SETTINGS_FILE", test_file), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        settings.save({"drives": ["C:\\"], "mode": "Both", "term": "test",
                       "use_regex": True, "ext_filter": ".py",
                       "exclude_dirs": [".git"], "output_formats": ["JSON"],
                       "output_path": "C:\\output"})
    assert test_file.exists()
    data = json.loads(test_file.read_text(encoding="utf-8"))
    assert data["mode"] == "Both"
    assert data["use_regex"] is True


def test_save_and_load_roundtrip(tmp_path):
    test_file = tmp_path / "settings.json"
    payload = {"drives": ["D:\\"], "mode": "Extension only", "term": "",
               "use_regex": False, "ext_filter": ".xlsx",
               "exclude_dirs": [".git"], "output_formats": ["CSV"],
               "output_path": "D:\\out"}
    with patch.object(settings, "SETTINGS_FILE", test_file), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        settings.save(payload)
        loaded = settings.load()
    assert loaded["drives"] == ["D:\\"]
    assert loaded["ext_filter"] == ".xlsx"


def test_load_merges_partial_file_with_defaults(tmp_path):
    test_file = tmp_path / "settings.json"
    test_file.write_text('{"mode": "Extension only"}', encoding="utf-8")
    with patch.object(settings, "SETTINGS_FILE", test_file), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        result = settings.load()
    assert result["mode"] == "Extension only"
    # Default filled in for missing key
    assert result["exclude_dirs"] == ["node_modules", ".git", "Windows"]


def test_load_returns_defaults_on_corrupt_json(tmp_path):
    test_file = tmp_path / "settings.json"
    test_file.write_text("not valid json {{", encoding="utf-8")
    with patch.object(settings, "SETTINGS_FILE", test_file), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        result = settings.load()
    assert result["mode"] == "Name search"
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest cli/tests/test_settings.py -v
```

Expected: `ModuleNotFoundError: No module named 'settings'`

- [ ] **Step 3: Create `cli/settings.py`**

```python
import json
from pathlib import Path

SETTINGS_DIR = Path.home() / ".fmf"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

DEFAULTS = {
    "drives": [],
    "mode": "Name search",
    "term": "",
    "use_regex": False,
    "ext_filter": "",
    "exclude_dirs": ["node_modules", ".git", "Windows"],
    "output_formats": ["CSV"],
    "output_path": "",
}


def load() -> dict:
    if not SETTINGS_FILE.exists():
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        merged = DEFAULTS.copy()
        merged.update(saved)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.copy()


def save(data: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest cli/tests/test_settings.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add cli/settings.py cli/tests/test_settings.py
git commit -m "feat: add settings module with load/save and defaults"
```

---

## Task 3: Search Engine

**Files:**
- Create: `cli/search.py`
- Create: `cli/tests/test_search.py`

- [ ] **Step 1: Write the failing tests**

Create `cli/tests/test_search.py`:

```python
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
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest cli/tests/test_search.py -v
```

Expected: `ModuleNotFoundError: No module named 'search'`

- [ ] **Step 3: Create `cli/search.py`**

```python
import os
import re
from pathlib import Path
from datetime import datetime


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _normalize_ext(ext: str) -> str:
    """'.py' -> 'py', '*.xlsx' -> 'xlsx', 'txt' -> 'txt'"""
    return ext.lstrip("*").lstrip(".").lower()


def search(
    drives: list,
    term: str | None,
    use_regex: bool,
    ext_filter: str | None,
    exclude_dirs: list,
) -> list:
    results = []
    pattern = re.compile(term, re.IGNORECASE) if (term and use_regex) else None
    norm_ext = _normalize_ext(ext_filter) if ext_filter else None
    exclude_set = {d.lower() for d in exclude_dirs}

    for drive in drives:
        for dirpath, dirnames, filenames in os.walk(drive, onerror=lambda _: None):
            dirnames[:] = [d for d in dirnames if d.lower() not in exclude_set]
            for filename in filenames:
                # Name match
                if term:
                    if pattern:
                        if not pattern.search(filename):
                            continue
                    else:
                        if term.lower() not in filename.lower():
                            continue
                # Extension match
                if norm_ext:
                    file_ext = Path(filename).suffix.lstrip(".").lower()
                    if file_ext != norm_ext:
                        continue
                # Stat
                full = os.path.join(dirpath, filename)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                results.append({
                    "name": filename,
                    "path": dirpath,
                    "size": _human_size(st.st_size),
                    "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
                    "ext": Path(filename).suffix.lstrip(".").lower(),
                })

    results.sort(key=lambda r: r["modified"], reverse=True)
    return results
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest cli/tests/test_search.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add cli/search.py cli/tests/test_search.py
git commit -m "feat: add search engine with name/regex/extension/exclude support"
```

---

## Task 4: Output Module

**Files:**
- Create: `cli/output.py`
- Create: `cli/tests/test_output.py`

- [ ] **Step 1: Write the failing tests**

Create `cli/tests/test_output.py`:

```python
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
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest cli/tests/test_output.py -v
```

Expected: `ModuleNotFoundError: No module named 'output'`

- [ ] **Step 3: Create `cli/output.py`**

```python
import csv
import json
from datetime import datetime
from pathlib import Path

FIELDS = ["name", "path", "size", "modified", "ext"]


def _timestamp() -> str:
    return datetime.now().strftime("%m%d%Y-%H%M%S")


def write_csv(results: list, output_dir: str, ts: str | None = None) -> str:
    ts = ts or _timestamp()
    filepath = str(Path(output_dir) / f"fmf-results-{ts}.csv")
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    return filepath


def write_json(results: list, output_dir: str, ts: str | None = None) -> str:
    ts = ts or _timestamp()
    filepath = str(Path(output_dir) / f"fmf-results-{ts}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return filepath


def write_outputs(results: list, output_dir: str, formats: list) -> list:
    ts = _timestamp()
    paths = []
    if "CSV" in formats:
        paths.append(write_csv(results, output_dir, ts))
    if "JSON" in formats:
        paths.append(write_json(results, output_dir, ts))
    return paths
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest cli/tests/test_output.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add cli/output.py cli/tests/test_output.py
git commit -m "feat: add output module for CSV and JSON export"
```

---

## Task 5: Wizard Entry Point

**Files:**
- Create: `cli/fmf.py`

No unit tests for the wizard — the interactive `questionary` prompts can't be driven by pytest without heavy mocking. All logic under test is already covered by Tasks 2–4. Verification is a manual smoke test.

- [ ] **Step 1: Create `cli/fmf.py`**

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

import questionary
import psutil
from rich.console import Console
from rich.table import Table

import search as search_module
import output as output_module
import settings as settings_module

console = Console()
_CUSTOM = "[ Enter custom path ]"


def _detect_drives() -> list:
    return [p.mountpoint for p in psutil.disk_partitions() if p.fstype]


def _ask_drives(saved_drives: list, available: list) -> list:
    default_checked = saved_drives if saved_drives else available
    choices = [
        questionary.Choice(d, checked=(d in default_checked))
        for d in available
    ] + [questionary.Choice(_CUSTOM, checked=False)]

    selected = questionary.checkbox("Select drives to search:", choices=choices).ask()
    if selected is None:
        sys.exit(0)

    drives = [d for d in selected if d != _CUSTOM]

    if _CUSTOM in selected:
        custom = questionary.text("Enter custom path:").ask()
        if custom and custom.strip():
            drives.append(custom.strip())

    if not drives:
        console.print("[red]No drives selected. Exiting.[/red]")
        sys.exit(1)

    return drives


def _ask_mode(saved_mode: str) -> str:
    mode = questionary.select(
        "Search mode:",
        choices=["Name search", "Extension only", "Both"],
        default=saved_mode,
    ).ask()
    if mode is None:
        sys.exit(0)
    return mode


def _ask_term(saved_term: str, saved_regex: bool) -> tuple:
    """Returns (term, use_regex). term may be None."""
    term = questionary.text("Search term:", default=saved_term).ask()
    if term is None:
        sys.exit(0)
    term = term.strip() or None

    use_regex = False
    if term:
        use_regex = questionary.confirm(
            "Treat as regex?", default=saved_regex
        ).ask()
        if use_regex is None:
            sys.exit(0)

    return term, use_regex


def _ask_ext(saved_ext: str) -> str | None:
    ext = questionary.text(
        "Extension filter (e.g. .py, .xlsx):", default=saved_ext
    ).ask()
    if ext is None:
        sys.exit(0)
    return ext.strip() or None


def _ask_exclude(saved: list) -> list:
    raw = questionary.text(
        "Exclude folders (comma-separated):",
        default=",".join(saved),
    ).ask()
    if raw is None:
        sys.exit(0)
    return [d.strip() for d in raw.split(",") if d.strip()]


def _ask_output(saved_formats: list, saved_path: str) -> tuple:
    formats = questionary.checkbox(
        "Output format:",
        choices=[
            questionary.Choice("CSV",  checked="CSV"  in saved_formats),
            questionary.Choice("JSON", checked="JSON" in saved_formats),
        ],
    ).ask()
    if formats is None:
        sys.exit(0)
    if not formats:
        console.print("[red]No output format selected. Exiting.[/red]")
        sys.exit(1)

    default_path = saved_path or str(Path(__file__).parent)
    out_path = questionary.text("Output directory:", default=default_path).ask()
    if out_path is None:
        sys.exit(0)

    return formats, out_path.strip() or str(Path(__file__).parent)


def _print_summary(drives, mode, term, use_regex, ext_filter, exclude_dirs, formats, out_path):
    console.print("\n[bold]Search summary:[/bold]")
    console.print(f"  Drives:    {', '.join(drives)}")
    console.print(f"  Mode:      {mode}")
    if term:
        console.print(f"  Term:      {term}{'  (regex)' if use_regex else ''}")
    if ext_filter:
        console.print(f"  Extension: {ext_filter}")
    console.print(f"  Excluding: {', '.join(exclude_dirs)}")
    console.print(f"  Output:    {', '.join(formats)} → {out_path}\n")


def run():
    saved = settings_module.load()
    available = _detect_drives()

    drives      = _ask_drives(saved["drives"], available)
    mode        = _ask_mode(saved["mode"])
    term, use_regex = (None, False)
    ext_filter  = None

    if mode != "Extension only":
        term, use_regex = _ask_term(saved["term"], saved["use_regex"])

    if mode != "Name search":
        ext_filter = _ask_ext(saved["ext_filter"])

    exclude_dirs        = _ask_exclude(saved["exclude_dirs"])
    formats, out_path   = _ask_output(saved["output_formats"], saved["output_path"])

    _print_summary(drives, mode, term, use_regex, ext_filter, exclude_dirs, formats, out_path)

    go = questionary.confirm("Start search?", default=True).ask()
    if not go:
        sys.exit(0)

    # Search
    results = []
    with console.status("[cyan]Scanning...[/cyan]") as status:
        for drive in drives:
            status.update(f"[cyan]Scanning {drive}...[/cyan]")
            results.extend(search_module.search(
                drives=[drive],
                term=term,
                use_regex=use_regex,
                ext_filter=ext_filter,
                exclude_dirs=exclude_dirs,
            ))

    results.sort(key=lambda r: r["modified"], reverse=True)

    # Display
    if not results:
        console.print("[yellow]No files found.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name",     style="white",    no_wrap=True)
        table.add_column("Path",     style="dim")
        table.add_column("Size",     justify="right")
        table.add_column("Modified", justify="center")
        table.add_column("Ext",      justify="center")
        for r in results:
            table.add_row(r["name"], r["path"], r["size"], r["modified"], r["ext"])
        console.print(table)
        console.print(f"\n[green]{len(results)} file(s) found.[/green]")

    # Write output files
    if results:
        saved_paths = output_module.write_outputs(results, out_path, formats)
        for p in saved_paths:
            console.print(f"[green]Saved:[/green] {p}")

    # Persist settings
    settings_module.save({
        "drives":         drives,
        "mode":           mode,
        "term":           term or "",
        "use_regex":      use_regex,
        "ext_filter":     ext_filter or "",
        "exclude_dirs":   exclude_dirs,
        "output_formats": formats,
        "output_path":    out_path,
    })


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the full test suite — confirm all tests still pass**

```bash
pytest cli/tests/ -v
```

Expected: `27 passed` (5 settings + 11 search + 11 output)

- [ ] **Step 3: Smoke test the wizard manually**

```bash
cd "G:/kvcd/VSCODE - Main/Plex Stuff/ReadMyFiles"
python cli/fmf.py
```

Walk through the wizard:
1. Select at least one drive
2. Choose "Extension only"
3. Type `.txt`
4. Leave excludes as default
5. Choose CSV output, output dir = current folder
6. Confirm and run
7. Verify a `.csv` file appears with results

- [ ] **Step 4: Commit**

```bash
git add cli/fmf.py
git commit -m "feat: add interactive wizard entry point (fmf.py)"
```

---

## Self-Review

**Spec coverage:**
- ✅ Wizard flow — all 7 steps implemented in `fmf.py`
- ✅ Search mode (Name / Extension only / Both) — `_ask_mode` + conditional skips
- ✅ Regex support — `use_regex` toggle in `_ask_term`
- ✅ Auto-detect drives — `_detect_drives()` via psutil
- ✅ Custom path — `_CUSTOM` choice appended to drive list
- ✅ Exclude folders — `_ask_exclude`
- ✅ CSV + JSON output — `output.write_outputs`
- ✅ Filename format `MMDDYYYY-HHMMSS` — `_timestamp()` in `output.py`
- ✅ Same timestamp for both files — `write_outputs` calls `_timestamp()` once
- ✅ Settings persist after every run — `settings_module.save()` at end of `run()`
- ✅ First-run defaults — `DEFAULTS` in `settings.py`, `drives: []` → all pre-checked
- ✅ Permission errors silently skipped — `onerror=lambda _: None` in `os.walk`

**Type consistency:** All function signatures match between plan tasks. `write_csv`/`write_json` accept optional `ts` param; `write_outputs` passes a shared timestamp to both.
