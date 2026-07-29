"""Protocol command group — TRT Protocol information and version.

Architecture Notes:
    TRT Protocol is the binary communication layer between trt-cli and
    embedded firmware.  It is not yet implemented; this module exposes
    documentation and version information as placeholders.

    Future Repository: trt-protocol
    Future Transport:  USB CDC (Full-Speed USB, CDC-ACM class)

    Packet Structure (planned):
        ┌──────────────────────────────────────────┐
        │  HEADER   │ 2 bytes │ Magic 0xTR 0x54    │
        │  VERSION  │ 1 byte  │ Protocol version   │
        │  CMD      │ 1 byte  │ Command opcode     │
        │  LENGTH   │ 2 bytes │ Payload length     │
        │  PAYLOAD  │ N bytes │ Command data       │
        │  CRC      │ 2 bytes │ CRC-16/CCITT       │
        └──────────────────────────────────────────┘
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(
    help="TRT Protocol information",
    no_args_is_help=True,
)

_PROTOCOL_VERSION = "0.1.0-draft"


@app.command(help="Show TRT Protocol specification summary")
def info() -> None:
    """Display TRT Protocol design and planned specification.

    This command shows the planned protocol structure and design goals.
    No protocol implementation exists yet.
    """
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key",   style="dim",        min_width=20)
    table.add_column("value", style="bold white")

    table.add_row("Protocol Name",    "TRT Protocol")
    table.add_row("Version",          _PROTOCOL_VERSION)
    table.add_row("Status",           "[yellow]Planned — not yet implemented[/yellow]")
    table.add_row("Transport",        "USB CDC (USB Full-Speed, CDC-ACM class)")
    table.add_row("Future Transports","CAN bus, Ethernet / TCP")
    table.add_row("Encoding",         "Binary, little-endian")
    table.add_row("Error Detection",  "CRC-16/CCITT")
    table.add_row("Repository",       "[cyan]trt-protocol[/cyan]  (future)")

    panel = Panel(
        table,
        title="[bold cyan]TRT Protocol[/bold cyan]",
        border_style="bright_blue",
        expand=False,
    )
    console.print(panel)

    console.print()
    console.print(
        "  [bold]Planned packet structure:[/bold]\n"
        "  [dim]┌─────────────────────────────────────────┐[/dim]\n"
        "  [dim]│[/dim]  HEADER   [dim]│[/dim] 2 bytes [dim]│[/dim] Magic 0x54 0x52 ([cyan]TR[/cyan])  [dim]│[/dim]\n"
        "  [dim]│[/dim]  VERSION  [dim]│[/dim] 1 byte  [dim]│[/dim] Protocol version        [dim]│[/dim]\n"
        "  [dim]│[/dim]  CMD      [dim]│[/dim] 1 byte  [dim]│[/dim] Command opcode          [dim]│[/dim]\n"
        "  [dim]│[/dim]  LENGTH   [dim]│[/dim] 2 bytes [dim]│[/dim] Payload length          [dim]│[/dim]\n"
        "  [dim]│[/dim]  PAYLOAD  [dim]│[/dim] N bytes [dim]│[/dim] Command data            [dim]│[/dim]\n"
        "  [dim]│[/dim]  CRC      [dim]│[/dim] 2 bytes [dim]│[/dim] CRC-16/CCITT            [dim]│[/dim]\n"
        "  [dim]└─────────────────────────────────────────┘[/dim]\n"
    )

    console.print(
        "  [dim]See [cyan]docs/future-protocol.md[/cyan] for full specification notes.[/dim]\n"
    )


@app.command(help="Display TRT Protocol version")
def version() -> None:
    """Show the current TRT Protocol version string.

    Future: will query the connected board and compare host vs firmware
    protocol versions to verify compatibility.
    """
    console.print()
    console.print(f"  [bold cyan]TRT Protocol[/bold cyan]")
    console.print(f"  Version : [yellow]{_PROTOCOL_VERSION}[/yellow]")
    console.print(f"  Status  : [dim]Planned — not yet implemented[/dim]")
    console.print()
