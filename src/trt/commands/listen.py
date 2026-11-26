"""Listen command - passively print asynchronous messages from TRT boards."""

from __future__ import annotations

import threading

import typer
from rich.console import Console

from trt.commands.console_io import discard_stdout, stdout_closed
from trt.services.listen_service import ListenService, describe_frame
from trt.transport.frame_reader import ReceivedFrame

console = Console()


def run_listen(board_id: str | None = None) -> None:
    """Print every message received from TRT boards until Ctrl+C.

    Used by ``trt listen`` (all boards) and ``trt board listen <address>`` (one board).
    """
    wanted: int | None = None
    if board_id is not None:
        try:
            wanted = int(board_id, 0)
        except ValueError:
            console.print(f"\n  [red]Listening needs a numeric board address, got {board_id!r}.[/red]\n")
            raise typer.Exit(1) from None

    service = ListenService()
    if not service.ports:
        console.print("\n  [yellow]No serial ports found.[/yellow]\n")
        raise typer.Exit(1)

    lock = threading.Lock()
    stop = threading.Event()
    output_closed = threading.Event()

    def emit(text: str, markup: bool) -> None:
        # Runs in reader threads. If the output pipe closes (`trt listen | grep -m1 HEARTBEAT`),
        # stop listening instead of crashing the thread.
        with lock:
            if output_closed.is_set():
                return
            try:
                console.print(text, markup=markup, highlight=False)
            except OSError:
                if not stdout_closed():
                    raise
                output_closed.set()
                stop.set()

    def on_frame(port: str, frame: ReceivedFrame) -> None:
        emit(f"Board {frame.board_id}: {describe_frame(frame)}", markup=False)

    def on_error(port: str, error: Exception) -> None:
        emit(f"  [dim]{port}: {error}[/dim]", markup=True)

    target = f"board {wanted}" if wanted is not None else "all boards"
    console.print(f"\n  Listening to {target} on {', '.join(service.ports)}  [dim](Ctrl+C to stop)[/dim]\n")

    try:
        opened = service.listen(on_frame, stop, board_id=wanted, on_error=on_error)
    except KeyboardInterrupt:
        stop.set()
        console.print("\n  Stopped.\n")
        return
    if output_closed.is_set():
        discard_stdout()
        raise typer.Exit(0)
    if opened == 0:
        console.print("  [red]Could not open any serial port.[/red]\n")
        raise typer.Exit(1)
