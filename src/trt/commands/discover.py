"""Discover command - rescan for connected boards."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from trt.services.board_discovery_service import BoardDiscoveryService

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

    for board in boards:
        ident = board.identity
        transport_str = str(board.transport) if board.transport else "-"
        console.print(
            f"  [cyan]{ident.board_id}[/cyan]  "
            f"[magenta]{ident.board_type.value}[/magenta]  "
            f"fw=[white]{ident.firmware}[/white]  "
            f"via=[yellow]{transport_str}[/yellow]"
        )

    console.print("\n  [dim]Mock discovery - real USB enumeration coming in a future release.[/dim]\n")
