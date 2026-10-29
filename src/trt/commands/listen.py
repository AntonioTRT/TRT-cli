"""Listen command - passively print asynchronous messages from TRT boards."""

from __future__ import annotations

import threading

import typer
from rich.console import Console

from trt.services.listen_service import ListenService, describe_frame
from trt.transport.frame_reader import ReceivedFrame

console = Console()


def run_listen(board_id: str | None = None) -> None:
    """Print every message received from TRT boards until Ctrl+C.

    Used by ``trt listen`` (all boards) and ``trt board <id> listen`` (one board).
    """
    wanted: int | None = None
    if board_id is not None:
        try:
            wanted = int(board_id, 0)
        except ValueError:
            console.print(f"\n  [red]Listening needs a numeric board id, got {board_id!r}.[/red]\n")
            raise typer.Exit(1)

    service = ListenService()
    if not service.ports:
        console.print("\n  [yellow]No serial ports found.[/yellow]\n")
        raise typer.Exit(1)

    lock = threading.Lock()

    def on_frame(port: str, frame: ReceivedFrame) -> None:
        with lock:
            console.print(f"Board {frame.board_id}: {describe_frame(frame)}", markup=False, highlight=False)

    def on_error(port: str, error: Exception) -> None:
        with lock:
            console.print(f"  [dim]{port}: {error}[/dim]")

    target = f"board {wanted}" if wanted is not None else "all boards"
    console.print(f"\n  Listening to {target} on {', '.join(service.ports)}  [dim](Ctrl+C to stop)[/dim]\n")

    stop = threading.Event()
    try:
        opened = service.listen(on_frame, stop, board_id=wanted, on_error=on_error)
    except KeyboardInterrupt:
        stop.set()
        console.print("\n  Stopped.\n")
        return
    if opened == 0:
        console.print("  [red]Could not open any serial port.[/red]\n")
        raise typer.Exit(1)
