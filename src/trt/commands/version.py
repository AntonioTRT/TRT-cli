"""Version command — display TRT CLI version information."""

from rich.console import Console
from rich.table import Table

from trt.version import get_version

console = Console()


def show_version() -> None:
    """Print the TRT CLI version."""
    version = get_version()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("key", style="dim")
    table.add_column("value", style="bold cyan")
    table.add_row("TRT CLI", "")
    table.add_row("Version:", version)

    console.print()
    console.print(table)
    console.print()

