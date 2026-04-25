# Find My Files — CLI Design

**Date:** 2026-04-25
**Scope:** Python CLI wizard (`cli/`) added to the ReadMyFiles repo

---

## Overview

A standalone Python CLI that replicates the core search behaviour of the browser prototype — drive selection, name/extension/both search modes, regex support, CSV/JSON export — using an interactive wizard powered by `questionary` (prompts) and `rich` (terminal output).

---

## File Structure

```
ReadMyFiles/
  cli/
    fmf.py            ← entry point, wizard orchestration
    search.py         ← os.walk search engine, regex matching
    output.py         ← CSV + JSON writers
    settings.py       ← load/save last-run defaults (~/.fmf/settings.json)
    requirements.txt  ← questionary, rich
```

`fmf.py` is the only orchestrator — it calls `search`, `output`, and `settings`. The other three modules are independent and do not call each other.

---

## Wizard Flow

Seven steps in order. Defaults shown in brackets come from the last saved run (or built-in defaults on first run).

```
① Drives
   Checkboxes of auto-detected drives (e.g. C:\, D:\, E:\)
   Pre-checked from last run.
   + "Enter a custom path" option appended to the list.

② Search mode
   Radio select — one of:
     > Name search     (match filename, supports regex)
     > Extension only  (list all files with a given extension)
     > Both            (name pattern AND extension filter combined)

③ Search term          [skipped if mode = "Extension only"]
   Text prompt.
   "Treat as regex? [y/N]" follow-up toggle.
   Default: last used term.

④ Extension filter     [skipped if mode = "Name search"]
   Text prompt — e.g. .py, .xlsx, .txt
   Default: last used extension.

⑤ Exclude folders
   Text prompt, comma-separated folder names to skip during walk.
   Default: node_modules,.git,Windows

⑥ Output
   Checkbox: CSV / JSON / Both
   Output path prompt (default: directory of fmf.py).

⑦ Confirm & run
   Summary of all chosen options printed.
   Press Enter to start.
   Rich spinner showing current drive being scanned.
   Results table printed when complete.
   File path(s) of saved output printed below table.
```

---

## Search Engine (`search.py`)

### Interface

```python
def search(
    drives: list[str],
    term: str | None,
    use_regex: bool,
    ext_filter: str | None,
    exclude_dirs: list[str],
) -> list[dict]:
```

Returns a list of result dicts: `{ name, path, size, modified, ext }`.

### Matching logic

- Walk each drive with `os.walk`, skipping any directory whose **name** (not full path) is in `exclude_dirs`.
- **Name match** (`term` is set):
  - If `use_regex`: compile `term` with `re.compile(term, re.IGNORECASE)`, test with `.search(filename)`.
  - If plain text: `term.lower() in filename.lower()`.
- **Extension match** (`ext_filter` is set):
  - Normalize input: strip leading `*` and `.`, lowercase → e.g. `.py` → `py`, `*.xlsx` → `xlsx`.
  - Match against `pathlib.Path(filename).suffix.lstrip(".").lower()`.
- **Both mode**: file must pass both the name match AND the extension match.
- **Extension only mode**: only the extension match is applied.
- Permission errors (`PermissionError`, `OSError`) on unreadable directories are silently skipped.
- Results sorted by `modified` descending.

### Result dict fields

| Field | Type | Notes |
|---|---|---|
| `name` | str | Filename only |
| `path` | str | Full directory path (without filename) |
| `size` | str | Human-readable, e.g. `"2.4 MB"` |
| `modified` | str | ISO date `YYYY-MM-DD` |
| `ext` | str | Lowercase, no dot, e.g. `"py"` |

---

## Output (`output.py`)

### Interface

```python
def write_csv(results: list[dict], output_dir: str) -> str  # returns filepath
def write_json(results: list[dict], output_dir: str) -> str  # returns filepath
```

### Filename format

```
fmf-results-MMDDYYYY-HHMMSS.csv
fmf-results-MMDDYYYY-HHMMSS.json
```

Both files generated from the same timestamp when "Both" is selected.

### CSV

`csv.DictWriter` with columns: `name, path, size, modified, ext`. UTF-8 with BOM (`utf-8-sig`) for Excel compatibility.

### JSON

`json.dump` with `indent=2`. Output is a list of result objects with the same five fields.

---

## Settings (`settings.py`)

### Storage path

`~/.fmf/settings.json` — created on first run.

### Interface

```python
def load() -> dict   # returns defaults if file missing
def save(settings: dict) -> None
```

### Fields persisted

```json
{
  "drives": ["C:\\", "D:\\"],
  "mode": "Name search",
  "term": "report",
  "use_regex": false,
  "ext_filter": ".xlsx",
  "exclude_dirs": ["node_modules", ".git", "Windows"],
  "output_formats": ["CSV"],
  "output_path": "C:\\Users\\admin\\cli"
}
```

### Built-in defaults (first run)

```json
{
  "drives": [],
  "mode": "Name search",
  "term": "",
  "use_regex": false,
  "ext_filter": "",
  "exclude_dirs": ["node_modules", ".git", "Windows"],
  "output_formats": ["CSV"],
  "output_path": "<directory of fmf.py>"
}
```

`drives: []` on first run means all auto-detected drives are pre-checked.

---

## Drive Detection

Auto-detection uses `psutil.disk_partitions()` filtered to `fstype != ""` (excludes virtual/system mounts) on Windows. `psutil` is added to `requirements.txt` alongside `questionary` and `rich`.

---

## Requirements

```
questionary
rich
psutil
```

Install: `pip install -r cli/requirements.txt`
Run: `python cli/fmf.py`

---

## Out of Scope

- Scheduled/background scans (roadmap v0.3)
- Full-text content search (roadmap v0.2)
- File size / date range filters (roadmap v0.2)
- macOS / Linux support (backlog)
