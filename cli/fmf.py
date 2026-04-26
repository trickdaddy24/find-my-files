#!/usr/bin/env python3
import re
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

    # Search — stream results live, updating status per file found
    results = []
    with console.status("") as status:
        for r in search_module.search(
            drives=drives,
            term=term,
            use_regex=use_regex,
            ext_filter=ext_filter,
            exclude_dirs=exclude_dirs,
        ):
            results.append(r)
            status.update(
                f"[cyan]{r['path']}[/cyan]  "
                f"[green]{len(results)} found[/green]"
            )

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
