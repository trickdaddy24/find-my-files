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
