"""LCD command group — HD44780-style LCD over I2C.

Architecture Notes:
    The LCD is treated as a peripheral connected to a board's I2C bus.
    Commands here operate at the "session" level (no board qualifier) for
    convenience, matching the pattern used by tools like `docker`.

    Future Implementation:
        - Detect LCD via I2C scan on the active/default board.
        - Route commands through TRT Protocol LCD message type.
        - Support line/column addressing.
        - Support custom characters.
"""

import typer
from rich.console import Console

console = Console()
app = typer.Typer(
    help="LCD display control (HD44780-style over I2C)",
    no_args_is_help=True,
)


@app.command(help="Show LCD module information")
def info() -> None:
    """Display LCD module information.

    Future: queries the connected board for attached LCD details
    (columns, rows, backlight state, I2C address).
    """
    console.print()
    console.print("  [bold cyan]LCD Module[/bold cyan]")
    console.print("  Type      : HD44780-compatible (I2C)")
    console.print("  Columns   : [dim]unknown — not connected[/dim]")
    console.print("  Rows      : [dim]unknown — not connected[/dim]")
    console.print("  Backlight : [dim]unknown — not connected[/dim]")
    console.print()
    _mock_note()


@app.command(help="Reset the LCD display")
def reset() -> None:
    """Send a reset command to the LCD display.

    Future: sends TRT Protocol LCD_RESET message to the active board.
    """
    console.print()
    console.print("  [yellow]LCD reset[/yellow] — [dim](mock: no hardware connected)[/dim]")
    console.print()
    _mock_note()


@app.command(help="Clear the LCD display")
def clear() -> None:
    """Clear all characters on the LCD display.

    Future: sends TRT Protocol LCD_CLEAR message.
    """
    console.print()
    console.print("  [yellow]LCD clear[/yellow] — [dim](mock: no hardware connected)[/dim]")
    console.print()
    _mock_note()


@app.command(help='Write text to the LCD display.  Example: trt lcd write "Hello"')
def write(
    text: str = typer.Argument(..., help="Text string to display on the LCD"),
    line: int = typer.Option(0, "--line", "-l", help="Target line (0-indexed)"),
    col: int = typer.Option(0, "--col", "-c", help="Start column (0-indexed)"),
) -> None:
    """Write a text string to the LCD display.

    Future: encodes *text* in a TRT Protocol LCD_WRITE packet and transmits
    it to the active board over USB.
    """
    console.print()
    console.print(
        f"  [yellow]LCD write[/yellow]  line=[cyan]{line}[/cyan]  "
        f"col=[cyan]{col}[/cyan]  text=[green]\"{text}\"[/green]"
        "  [dim](mock)[/dim]"
    )
    console.print()
    _mock_note()


def _mock_note() -> None:
    console.print(
        "  [dim]Hardware not connected.  "
        "LCD support will be activated once TRT Protocol is implemented.[/dim]\n"
    )
