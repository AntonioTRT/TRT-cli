"""Boards command — list all known boards."""

from rich.console import Console
from rich.table import Table

from trt.core.models import BoardStatus
from trt.services.board_discovery_service import BoardDiscoveryService

console = Console()

_STATUS_STYLE: dict[str, str] = {
    BoardStatus.READY.value:         "bold green",
    BoardStatus.CONNECTED.value:     "green",
    BoardStatus.INITIALIZING.value:  "yellow",
    BoardStatus.DISCONNECTED.value:  "dim",
    BoardStatus.ERROR.value:         "bold red",
    BoardStatus.OFFLINE.value:       "red",
}


def show_boards() -> None:
    """Display all boards currently known to TRT.

    Mock implementation — real boards will be populated via USB discovery
    once TRT Protocol is implemented.
    """
    service = BoardDiscoveryService()
    boards = service.discover()

    console.print()

    if not boards:
        console.print("  [dim]No boards detected.[/dim]")
        console.print("  [dim]Run [cyan]trt discover[/cyan] to scan for boards.[/dim]")
        console.print()
        return

    table = Table(
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        title="[bold cyan]Connected Boards[/bold cyan]",
    )
    table.add_column("Board ID",   style="bold cyan",  min_width=10)
    table.add_column("Type",       style="magenta",    min_width=12)
    table.add_column("Revision",   style="white",      min_width=9)
    table.add_column("Firmware",   style="white",      min_width=9)
    table.add_column("Transport",  style="yellow",     min_width=12)
    table.add_column("Status",     min_width=12)

    for board in boards:
        ident = board.identity
        status_val = board.status.value
        status_style = _STATUS_STYLE.get(status_val, "white")
        transport_str = str(board.transport) if board.transport else "—"

        table.add_row(
            ident.board_id,
            ident.board_type.value,
            ident.revision,
            ident.firmware,
            transport_str,
            f"[{status_style}]{status_val}[/{status_style}]",
        )

    console.print(table)
    console.print(
        f"\n  [dim]{len(boards)} board(s) listed  ·  "
        "Mock data — USB discovery coming in a future release.[/dim]\n"
    )

