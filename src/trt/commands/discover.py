"""Discover command — rescan for connected boards."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from trt.services.board_discovery_service import BoardDiscoveryService

console = Console()


def run_discover() -> None:
    """Force a rescan for available boards on all transports.

    Mock implementation — future versions will trigger real USB enumeration
    via TRT Protocol and update the persistent board registry.

    Future:
        1. Enumerate all active transports (USB, CAN, TCP).
        2. Broadcast a TRT Protocol discovery packet on each transport.
        3. Collect responses, build Board objects, update the registry.
        4. Persist the updated registry to a local cache.
    """
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("[cyan]Scanning USB transport for boards…", total=None)
        import time
        time.sleep(0.8)  # Simulate scan latency

    service = BoardDiscoveryService()
    boards = service.discover()

    console.print(f"  [bold green]Discovery complete.[/bold green]  Found [cyan]{len(boards)}[/cyan] board(s).\n")

    for board in boards:
        ident = board.identity
        transport_str = str(board.transport) if board.transport else "—"
        console.print(
            f"  [cyan]{ident.board_id}[/cyan]  "
            f"[magenta]{ident.board_type.value}[/magenta]  "
            f"fw=[white]{ident.firmware}[/white]  "
            f"via=[yellow]{transport_str}[/yellow]"
        )

    console.print(
        "\n  [dim]Mock discovery — real USB enumeration coming in a future release.[/dim]\n"
    )
