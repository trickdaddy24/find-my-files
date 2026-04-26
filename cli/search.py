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
    drives: list[str],
    term: str | None,
    use_regex: bool,
    ext_filter: str | None,
    exclude_dirs: list[str],
    on_dir=None,
):
    """Generator — yields one result dict per matching file as it is found.

    on_dir: optional callable(dirpath) called on every directory entered,
            even when no files in it match. Use this to update a progress display.
    """
    pattern = re.compile(term, re.IGNORECASE) if (term and use_regex) else None
    norm_ext = _normalize_ext(ext_filter) if ext_filter else None
    exclude_set = {d.lower() for d in exclude_dirs}

    for drive in drives:
        for dirpath, dirnames, filenames in os.walk(drive, onerror=lambda _: None):
            dirnames[:] = [d for d in dirnames if d.lower() not in exclude_set]
            if on_dir:
                on_dir(dirpath)
            for filename in filenames:
                file_ext = Path(filename).suffix.lstrip(".").lower()
                # Name match
                if term:
                    if pattern:
                        if not pattern.search(filename):
                            continue
                    else:
                        if term.lower() not in filename.lower():
                            continue
                # Extension match
                if norm_ext and file_ext != norm_ext:
                    continue
                # Stat
                full = os.path.join(dirpath, filename)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                yield {
                    "name": filename,
                    "path": dirpath,
                    "size": _human_size(st.st_size),
                    "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
                    "ext": file_ext,
                }
