#!/usr/bin/env python3
"""Find My Files CLI — interactive drive search wizard."""
__version__ = "0.2.0"

import re
import sys
from pathlib import Path

import questionary
import psutil
from rich.console import Console
from rich.table import Table

import index as index_module
import output as output_module
import search as search_module
import settings as settings_module

console = Console()
_CUSTOM = "[ Enter custom path ]"


# ---------------------------------------------------------------------------
# Drive helpers
# ---------------------------------------------------------------------------

def _detect_drives() -> list[str]:
    return [p.mountpoint for p in psutil.disk_partitions() if p.fstype]


def _ask_drives(saved_drives: list, available: list) -> list[str]:
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


# ---------------------------------------------------------------------------
# Search-parameter helpers
# ---------------------------------------------------------------------------

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
        use_regex = questionary.confirm("Treat as regex?", default=saved_regex).ask()
        if use_regex is None:
            sys.exit(0)
        if use_regex:
            try:
                re.compile(term)
            except re.error as exc:
                console.print(f"[red]Invalid regex: {exc}. Falling back to plain text.[/red]")
                use_regex = False

    return term, use_regex


def _ask_ext(saved_ext: str) -> str | None:
    ext = questionary.text(
        "Extension filter (e.g. .py, .xlsx):", default=saved_ext
    ).ask()
    if ext is None:
        sys.exit(0)
    return ext.strip() or None


def _ask_exclude(saved: list) -> list[str]:
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


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_summary(drives, mode, term, use_regex, ext_filter, exclude_dirs, formats, out_path):
    console.print("\n[bold]Search summary:[/bold]")
    console.print(f"  Drives:    {', '.join(drives)}")
    console.print(f"  Mode:      {mode}")
    if term:
        console.print(f"  Term:      {term}{'  (regex)' if use_regex else ''}")
    if ext_filter:
        console.print(f"  Extension: {ext_filter}")
    if exclude_dirs:
        console.print(f"  Excluding: {', '.join(exclude_dirs)}")
    console.print(f"  Output:    {', '.join(formats)} → {out_path}\n")


def _highlight_name(filename: str, term: str | None, use_regex: bool) -> str:
    """Return the filename with the matched portion wrapped in yellow bold markup."""
    if not term:
        return filename
    if use_regex:
        try:
            return re.sub(
                term,
                lambda m: f"[bold yellow]{m.group()}[/bold yellow]",
                filename,
                flags=re.IGNORECASE,
            )
        except re.error:
            return filename
    else:
        idx = filename.lower().find(term.lower())
        if idx == -1:
            return filename
        return (
            filename[:idx]
            + f"[bold yellow]{filename[idx:idx + len(term)]}[/bold yellow]"
            + filename[idx + len(term):]
        )


def _display_results(results: list[dict], term: str | None = None, use_regex: bool = False) -> None:
    if not results:
        console.print("[yellow]No files found.[/yellow]")
        return
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name",     no_wrap=True)
    table.add_column("Path",     style="dim")
    table.add_column("Size",     justify="right")
    table.add_column("Modified", justify="center")
    table.add_column("Ext",      justify="center")
    for r in results:
        table.add_row(
            _highlight_name(r["name"], term, use_regex),
            r["path"], r["size"], r["modified"], r["ext"],
        )
    console.print(table)
    console.print(f"\n[green]{len(results)} file(s) found.[/green]")


def _save_results(results, out_path, formats):
    if results:
        for p in output_module.write_outputs(results, out_path, formats):
            console.print(f"[green]Saved:[/green] {p}")


# ---------------------------------------------------------------------------
# Workflow: live scan
# ---------------------------------------------------------------------------

def _run_live_search(saved: dict, available: list) -> None:
    drives       = _ask_drives(saved["drives"], available)
    mode         = _ask_mode(saved["mode"])
    term, use_regex = (None, False)
    ext_filter   = None

    if mode != "Extension only":
        term, use_regex = _ask_term(saved["term"], saved["use_regex"])
    if mode != "Name search":
        ext_filter = _ask_ext(saved["ext_filter"])

    exclude_dirs        = _ask_exclude(saved["exclude_dirs"])
    formats, out_path   = _ask_output(saved["output_formats"], saved["output_path"])

    _print_summary(drives, mode, term, use_regex, ext_filter, exclude_dirs, formats, out_path)

    if not questionary.confirm("Start search?", default=True).ask():
        sys.exit(0)

    results = []
    current_dir = [""]

    def _on_dir(d: str) -> None:
        current_dir[0] = d

    with console.status("") as status:
        for r in search_module.search(
            drives=drives, term=term, use_regex=use_regex,
            ext_filter=ext_filter, exclude_dirs=exclude_dirs,
            on_dir=_on_dir,
        ):
            results.append(r)
            status.update(
                f"[cyan]{current_dir[0]}[/cyan]\n"
                f"[dim]{len(results)} match{'es' if len(results) != 1 else ''} found[/dim]"
            )

    # Show final directory even if last dirs had no matches
    console.print(f"[dim]Scanned through: {current_dir[0]}[/dim]")

    results.sort(key=lambda r: r["modified"], reverse=True)
    _display_results(results, term=term, use_regex=use_regex)
    _save_results(results, out_path, formats)

    settings_module.save({
        "drives": drives, "mode": mode, "term": term or "",
        "use_regex": use_regex, "ext_filter": ext_filter or "",
        "exclude_dirs": exclude_dirs, "output_formats": formats, "output_path": out_path,
    })


# ---------------------------------------------------------------------------
# Workflow: build index
# ---------------------------------------------------------------------------

def _run_build_index(saved: dict, available: list) -> None:
    drive = questionary.select("Select drive to index:", choices=available).ask()
    if drive is None:
        sys.exit(0)

    exclude_dirs = _ask_exclude(saved["exclude_dirs"])

    meta = index_module.get_meta(drive)
    if meta:
        console.print(
            f"[dim]Existing index: {meta['file_count']:,} files, "
            f"built {meta['indexed_at']}[/dim]"
        )

    if not questionary.confirm(f"Build index for {drive}?", default=True).ask():
        sys.exit(0)

    with console.status("") as status:
        def _on_dir(d: str) -> None:
            status.update(f"[cyan]{d}[/cyan]")

        count = index_module.build(drive, exclude_dirs, on_dir=_on_dir)

    console.print(f"\n[green]Indexed {count:,} files from {drive}[/green]")
    console.print(f"[dim]Stored at: {index_module.INDEX_FILE}[/dim]")

    settings_module.save({**saved, "exclude_dirs": exclude_dirs})


# ---------------------------------------------------------------------------
# Workflow: search from index
# ---------------------------------------------------------------------------

def _run_search_index(saved: dict, available: list) -> None:
    all_meta = index_module.list_all()
    if not all_meta:
        console.print("[yellow]No drives indexed yet. Use 'Build / update drive index' first.[/yellow]")
        sys.exit(1)

    # Build drive choices — show file count + index date for indexed drives
    meta_by_drive = {m["drive"]: m for m in all_meta}
    choices = []
    for m in all_meta:
        label = (
            f"{m['drive']}  "
            f"({m['file_count']:,} files · indexed {m['indexed_at']})"
        )
        checked = m["drive"] in saved["drives"]
        choices.append(questionary.Choice(label, value=m["drive"], checked=checked))

    selected = questionary.checkbox("Select indexed drives to search:", choices=choices).ask()
    if not selected:
        sys.exit(0)
    drives = selected

    mode         = _ask_mode(saved["mode"])
    term, use_regex = (None, False)
    ext_filter   = None

    if mode != "Extension only":
        term, use_regex = _ask_term(saved["term"], saved["use_regex"])
    if mode != "Name search":
        ext_filter = _ask_ext(saved["ext_filter"])

    formats, out_path = _ask_output(saved["output_formats"], saved["output_path"])

    _print_summary(drives, mode, term, use_regex, ext_filter, [], formats, out_path)

    if not questionary.confirm("Search index?", default=True).ask():
        sys.exit(0)

    with console.status("[cyan]Querying index...[/cyan]"):
        results = index_module.query(drives, term, use_regex, ext_filter)

    _display_results(results, term=term, use_regex=use_regex)
    _save_results(results, out_path, formats)

    settings_module.save({
        "drives": drives, "mode": mode, "term": term or "",
        "use_regex": use_regex, "ext_filter": ext_filter or "",
        "exclude_dirs": saved["exclude_dirs"], "output_formats": formats,
        "output_path": out_path,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> None:
    saved     = settings_module.load()
    available = _detect_drives()

    action = questionary.select(
        "What would you like to do?",
        choices=[
            "Search drives (live scan)",
            "Search from index (fast)",
            "Build / update drive index",
        ],
    ).ask()
    if action is None:
        sys.exit(0)

    if action == "Build / update drive index":
        _run_build_index(saved, available)
    elif action == "Search from index (fast)":
        _run_search_index(saved, available)
    else:
        _run_live_search(saved, available)


if __name__ == "__main__":
    run()
