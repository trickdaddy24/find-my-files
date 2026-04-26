"""
Drive index — scan once, search instantly.

Storage: ~/.fmf/index.db  (SQLite)
Tables:  files, meta
"""
import os
import re as re_mod
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

INDEX_FILE = Path.home() / ".fmf" / "index.db"

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS files (
        id       INTEGER PRIMARY KEY,
        name     TEXT NOT NULL,
        path     TEXT NOT NULL,
        size     TEXT NOT NULL,
        modified TEXT NOT NULL,
        ext      TEXT NOT NULL,
        drive    TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_files_drive ON files(drive);
    CREATE INDEX IF NOT EXISTS idx_files_ext   ON files(ext);
    CREATE INDEX IF NOT EXISTS idx_files_name  ON files(name COLLATE NOCASE);
    CREATE TABLE IF NOT EXISTS meta (
        drive       TEXT PRIMARY KEY,
        indexed_at  TEXT NOT NULL,
        file_count  INTEGER NOT NULL
    );
"""


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _normalize_ext(ext: str) -> str:
    return ext.lstrip("*").lstrip(".").lower()


@contextmanager
def _connect():
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(INDEX_FILE))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def build(drive: str, exclude_dirs: list[str], on_dir=None) -> int:
    """Walk drive and (re)build its index entry. Returns file count.

    on_dir: optional callable(dirpath) called on every directory visited.
    """
    exclude_set = {d.lower() for d in exclude_dirs}
    rows = []

    for dirpath, dirnames, filenames in os.walk(drive, onerror=lambda _: None):
        dirnames[:] = [d for d in dirnames if d.lower() not in exclude_set]
        if on_dir:
            on_dir(dirpath)
        for filename in filenames:
            ext = Path(filename).suffix.lstrip(".").lower()
            full = os.path.join(dirpath, filename)
            try:
                st = os.stat(full)
            except OSError:
                continue
            rows.append((
                filename,
                dirpath,
                _human_size(st.st_size),
                datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
                ext,
                drive,
            ))

    with _connect() as conn:
        conn.execute("DELETE FROM files WHERE drive = ?", (drive,))
        conn.executemany(
            "INSERT INTO files (name, path, size, modified, ext, drive) VALUES (?,?,?,?,?,?)",
            rows,
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (drive, indexed_at, file_count) VALUES (?,?,?)",
            (drive, datetime.now().strftime("%Y-%m-%d %H:%M"), len(rows)),
        )

    return len(rows)


def query(
    drives: list[str],
    term: str | None,
    use_regex: bool,
    ext_filter: str | None,
) -> list[dict]:
    """Search the index. SQL filters extension + plain-text name; regex applied in Python."""
    norm_ext = _normalize_ext(ext_filter) if ext_filter else None

    conditions = ["drive IN (" + ",".join("?" * len(drives)) + ")"]
    params: list = list(drives)

    if norm_ext:
        conditions.append("ext = ?")
        params.append(norm_ext)

    if term and not use_regex:
        conditions.append("name LIKE ?")
        params.append(f"%{term}%")

    sql = (
        "SELECT name, path, size, modified, ext FROM files WHERE "
        + " AND ".join(conditions)
        + " ORDER BY modified DESC"
    )

    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    if term and use_regex:
        pattern = re_mod.compile(term, re_mod.IGNORECASE)
        rows = [r for r in rows if pattern.search(r["name"])]

    return [dict(r) for r in rows]


def get_meta(drive: str) -> dict | None:
    """Returns {drive, indexed_at, file_count} or None if drive not indexed."""
    if not INDEX_FILE.exists():
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT drive, indexed_at, file_count FROM meta WHERE drive = ?", (drive,)
        ).fetchone()
    return dict(row) if row else None


def list_all() -> list[dict]:
    """Returns all indexed drives sorted by drive letter."""
    if not INDEX_FILE.exists():
        return []
    with _connect() as conn:
        rows = conn.execute(
            "SELECT drive, indexed_at, file_count FROM meta ORDER BY drive"
        ).fetchall()
    return [dict(r) for r in rows]
