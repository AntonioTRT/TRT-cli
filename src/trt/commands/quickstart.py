"""Quick Start shown by `trt` with no arguments: the board workflow in five commands."""

from rich.console import Console
from rich.table import Table

console = Console()

# The core workflow, printed identically by trt, trt --help and trt help.
WORKFLOW = "discover -> boards -> info -> hwid -> update -> MATCH -> listen"

QUICK_START = (
    ("trt discover", "Discover TRT boards"),
    ("trt boards", "Show discovered boards and their MATCH status"),
    ("trt board info <address>", "Show board information"),
    ("trt board update <address>", "Install the mode that matches the HWID"),
    ("trt listen", "Monitor heartbeat and events"),
)


def show_quickstart() -> None:
    console.print()
    console.print("[bold cyan]TRT - Tool Runtime Terminal[/bold cyan]")
    console.print()
    console.print("[bold]Quick Start[/bold]")
    table = Table(show_header=False, box=None, padding=(0, 2), pad_edge=False)
    table.add_column(style="cyan", no_wrap=True)
    table.add_column()
    for command, description in QUICK_START:
        table.add_row(f"  {command}", description)
    console.print(table)
    console.print()
    console.print(f"Workflow: {WORKFLOW}")
    console.print("[dim]<address> is the board address shown by trt boards (e.g. 201).[/dim]")
    console.print("More: [cyan]trt --help[/cyan] (all commands)  |  [cyan]trt help[/cyan] (concepts and full reference)")
    console.print()
