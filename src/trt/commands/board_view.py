"""Rendering of BoardSummary, shared by `trt boards`, `trt discover`, `trt board info` and
`trt board update`: the same fields, labels and match wording everywhere."""

from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console
from rich.table import Table

from trt.core.modes import HwidMatch, format_hwid
from trt.services.board_summary import BoardSummary

_MATCH_STYLE = {
    HwidMatch.MATCH: "bold green",
    HwidMatch.MISMATCH: "bold red",
    HwidMatch.NO_HWID: "yellow",
    HwidMatch.NO_MODE: "yellow",
}
_MATCH_HINT = {
    HwidMatch.MATCH: "mode matches the hardware",
    HwidMatch.MISMATCH: "mode is for other hardware",
    HwidMatch.NO_HWID: "firmware cannot read the HWID",
    HwidMatch.NO_MODE: "no mode_<ID>_* mode declared",
}


def match_text(summary: BoardSummary) -> str:
    style = _MATCH_STYLE[summary.match]
    return f"[{style}]{summary.match.value}[/{style}]"


def hwid_pair(summary: BoardSummary) -> str:
    """'0010 / 0010': HWID read from the hardware / HWID the installed mode expects."""
    return f"{format_hwid(summary.hwid_read)} / {format_hwid(summary.hwid_expected)}"


def _hwid_decimal(hwid: int | None) -> str:
    return "-" if hwid is None else str(hwid)


def render_boards_table(console: Console, summaries: Sequence[BoardSummary]) -> None:
    table = Table(
        show_header=True,
        header_style="bold bright_white underline",
        box=None,
        padding=(0, 1),
        pad_edge=False,
        title_justify="left",
        caption_justify="left",
        title="[bold cyan]Connected Boards[/bold cyan]",
        caption="[dim]HWID: read from hardware / expected by the installed mode[/dim]",
    )
    table.add_column("Addr", style="bold cyan", no_wrap=True)
    table.add_column("Name", style="magenta", overflow="fold")
    table.add_column("Firmware", no_wrap=True)
    table.add_column("Mode", style="white", overflow="fold", min_width=12)
    table.add_column("HWID", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    for summary in summaries:
        firmware = f"{summary.firmware} #{summary.build_id}" if summary.build_id not in ("", "-") else summary.firmware
        table.add_row(
            summary.board_id,
            summary.name,
            firmware,
            summary.active_mode or "[dim]-[/dim]",
            hwid_pair(summary),
            match_text(summary),
        )
    console.print(table)
    render_next_steps(console, summaries)


def render_next_steps(console: Console, summaries: Sequence[BoardSummary]) -> None:
    for summary in summaries:
        if summary.match is HwidMatch.MISMATCH:
            console.print(
                f"  [bold red]Board {summary.board_id}: update required.[/bold red] "
                f"Run [cyan]trt board update {summary.board_id}[/cyan]"
            )
        elif summary.match is HwidMatch.NO_MODE:
            console.print(
                f"  [yellow]Board {summary.board_id}: no standard mode installed.[/yellow] "
                f"Run [cyan]trt board update {summary.board_id}[/cyan]"
            )
        elif summary.match is HwidMatch.NO_HWID:
            console.print(
                f"  [yellow]Board {summary.board_id}: firmware predates HWID.[/yellow] "
                f"Run [cyan]trt board update {summary.board_id}[/cyan] for the steps"
            )


def summary_rows(summary: BoardSummary) -> list[tuple[str, str]]:
    """Key/value rows of the single-board status block (same values as one `trt boards` row)."""
    family = f" ({summary.family})" if summary.family else ""
    return [
        ("Address", summary.board_id),
        ("Name", f"{summary.name}{family}"),
        ("Firmware", f"{summary.firmware}  build {summary.build_id}"),
        ("Mode", summary.active_mode or "[dim]none declared[/dim]"),
        (
            "HWID",
            (
                f"{hwid_pair(summary)}  [dim](read {_hwid_decimal(summary.hwid_read)}"
                f" / expected {_hwid_decimal(summary.hwid_expected)})[/dim]"
            ),
        ),
        ("Status", f"{match_text(summary)}  [dim]{_MATCH_HINT[summary.match]}[/dim]"),
    ]


def summary_table(summary: BoardSummary, extra_rows: Sequence[tuple[str, str]] = ()) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value")
    for key, value in [*summary_rows(summary), *extra_rows]:
        table.add_row(key, value)
    return table
