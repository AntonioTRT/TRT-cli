"""Boards command — list all known boards with the same status summary as `trt board info`."""

from rich.console import Console

from trt.commands.board_view import render_boards_table
from trt.services.board_discovery_service import BoardDiscoveryService
from trt.services.board_summary import summary_from_board

console = Console()


def show_boards() -> None:
    """Display all boards currently known to TRT."""
    service = BoardDiscoveryService()
    boards = service.discover()

    console.print()

    if not boards:
        console.print("  [dim]No boards detected.[/dim]")
        console.print("  [dim]Run [cyan]trt discover[/cyan] to scan for boards.[/dim]")
        console.print()
        return

    render_boards_table(console, [summary_from_board(board) for board in boards])
    console.print(
        f"\n  [dim]{len(boards)} board(s) listed via TRT serial discovery. "
        "Details: trt board info <address>.[/dim]\n"
    )
