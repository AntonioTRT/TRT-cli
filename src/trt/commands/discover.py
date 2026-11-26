"""Discover command - rescan for connected boards."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from trt.commands.board_view import render_boards_table
from trt.services.board_discovery_service import BoardDiscoveryService
from trt.services.board_summary import summary_from_board

console = Console()


def run_discover() -> None:
    service = BoardDiscoveryService()

    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("[cyan]Scanning USB transport for boards...", total=None)
        boards = service.discover()

    console.print(f"  [bold green]Discovery complete.[/bold green]  Found [cyan]{len(boards)}[/cyan] board(s).\n")

    if boards:
        render_boards_table(console, [summary_from_board(board) for board in boards])

    console.print("\n  [dim]Real serial discovery via TRT protocol.[/dim]\n")
