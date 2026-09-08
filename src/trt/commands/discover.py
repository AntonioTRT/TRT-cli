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
        board_type = board.metadata.get("board_type", ident.board_type.value)
        build_id = board.metadata.get("build_id", ident.serial or "-")
        transport_str = str(board.transport) if board.transport else "-"
        console.print(
            f"  [cyan]{ident.board_id}[/cyan]  "
            f"[magenta]{board_type}[/magenta]  "
            f"fw=[white]{ident.firmware}[/white]  "
            f"build=[white]{build_id}[/white]  "
            f"via=[yellow]{transport_str}[/yellow]"
        )

    console.print("\n  [dim]Real serial discovery via TRT protocol.[/dim]\n")
