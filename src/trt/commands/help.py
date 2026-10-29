"""Help command — rich overview of the full TRT command tree."""

from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def show_help() -> None:
    """Display the full TRT command tree with descriptions."""
    console.print()

    # Header
    title = Text("TRT  ·  Tool Runtime Terminal", style="bold cyan")
    mission = Text(
        "A modular hardware control ecosystem for embedded boards and expansion modules.",
        style="dim",
    )
    console.print(Panel(mission, title=title, border_style="bright_blue", expand=False))
    console.print()

    # Top-level commands table
    top = Table(
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        box=None,
        padding=(0, 2),
    )
    top.add_column("Command", style="bold cyan", min_width=20)
    top.add_column("Description", style="white")

    top.add_row("trt help", "Show this help message")
    top.add_row("trt version", "Display TRT CLI version")
    top.add_row("trt update", "Check for TRT CLI updates (--install to install)")
    top.add_row("trt discover", "Scan serial ports for TRT boards")
    top.add_row("trt listen", "Print heartbeat/event messages from all boards")
    top.add_row("trt boards", "List boards found by serial discovery")
    top.add_row("trt board <command> <id>", "Query a discovered board (see below)")
    top.add_row("trt flash stm32", "Build and upload STM32 firmware")
    top.add_row("trt stm32 test", "Test the full TRT v0.1 serial protocol")
    top.add_row("trt board <board> ...", "Operate on a specific board")
    top.add_row("trt lcd ...", "LCD display control")
    top.add_row("trt led ...", "LED control (WS2812 / NeoPixel)")
    top.add_row("trt protocol ...", "TRT Protocol information")

    console.print(Padding("[bold]Top-level commands[/bold]", (0, 2)))
    console.print(Padding(top, (0, 2)))
    console.print()

    # Board sub-commands
    board = Table(
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        box=None,
        padding=(0, 2),
    )
    board.add_column("Sub-command", style="bold green", min_width=30)
    board.add_column("Description", style="white")

    rows = [
        ("board info <id>",         "Board identity and firmware info"),
        ("board status <id>",       "Current board status"),
        ("board capabilities <id>", "List board capabilities"),
        ("board listen <id>",       "Print heartbeat/event messages from one board"),
    ]
    for cmd, desc in rows:
        board.add_row(cmd, desc)

    console.print(Padding("[bold]Board sub-commands[/bold]", (0, 2)))
    console.print(Padding(board, (0, 2)))
    console.print()

    # Footer
    console.print(
        Padding(
            "[dim]Run [cyan]trt <command> --help[/cyan] for detailed usage of any command.[/dim]",
            (0, 2),
        )
    )
    console.print()
