import json
from unittest.mock import patch
import settings


def test_load_returns_defaults_when_file_missing(tmp_path):
    with patch.object(settings, "SETTINGS_FILE", tmp_path / "nonexistent.json"), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        result = settings.load()
    assert result["mode"] == "Name search"
    assert result["exclude_dirs"] == ["node_modules", ".git", "Windows", "$RECYCLE.BIN", "System Volume Information"]
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
    assert result["exclude_dirs"] == ["node_modules", ".git", "Windows", "$RECYCLE.BIN", "System Volume Information"]


def test_load_returns_defaults_on_corrupt_json(tmp_path):
    test_file = tmp_path / "settings.json"
    test_file.write_text("not valid json {{", encoding="utf-8")
    with patch.object(settings, "SETTINGS_FILE", test_file), \
         patch.object(settings, "SETTINGS_DIR", tmp_path):
        result = settings.load()
    assert result["mode"] == "Name search"
