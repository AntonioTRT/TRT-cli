"""LCD command group - HD44780-style LCD over I2C."""

from typing import Any

import typer
from rich.console import Console

from trt.protocol.models import ProtocolResponse
from trt.services.lcd_service import LCDService

console = Console()
app = typer.Typer(
    help="LCD display control (HD44780-style over I2C)",
    no_args_is_help=True,
)


@app.command(help="Show LCD module information")
def info() -> None:
    response = LCDService().info()
    payload = _payload(response)
    console.print()
    console.print("  [bold cyan]LCD Module[/bold cyan]")
    console.print(f"  Type      : {payload.get('type')}")
    console.print(f"  Columns   : [dim]{payload.get('columns')}[/dim]")
    console.print(f"  Rows      : [dim]{payload.get('rows')}[/dim]")
    console.print(f"  Backlight : [dim]{payload.get('backlight')}[/dim]")
    console.print()
    _hardware_note(payload)


@app.command(help="Reset the LCD display")
def reset() -> None:
    response = LCDService().reset()
    console.print()
    console.print(f"  [yellow]{_payload(response).get('label')}[/yellow] - [dim](mock: no hardware connected)[/dim]")
    console.print()
    _hardware_note(_payload(response))


@app.command(help="Clear the LCD display")
def clear() -> None:
    response = LCDService().clear()
    console.print()
    console.print(f"  [yellow]{_payload(response).get('label')}[/yellow] - [dim](mock: no hardware connected)[/dim]")
    console.print()
    _hardware_note(_payload(response))


@app.command(help='Write text to the LCD display.  Example: trt lcd write "Hello"')
def write(
    text: str = typer.Argument(..., help="Text string to display on the LCD"),
    line: int = typer.Option(0, "--line", "-l", help="Target line (0-indexed)"),
    col: int = typer.Option(0, "--col", "-c", help="Start column (0-indexed)"),
) -> None:
    response = LCDService().write(text, line, col)
    payload = _payload(response)
    console.print()
    console.print(
        f"  [yellow]{payload.get('label')}[/yellow]  line=[cyan]{payload.get('line')}[/cyan]  "
        f"col=[cyan]{payload.get('col')}[/cyan]  text=[green]\"{payload.get('text')}\"[/green]"
        "  [dim](mock)[/dim]"
    )
    console.print()
    _hardware_note(payload)


def _payload(response: ProtocolResponse) -> dict[str, Any]:
    return response.payload if isinstance(response.payload, dict) else {}


def _hardware_note(payload: dict[str, Any]) -> None:
    console.print(f"  [dim]{payload.get('note', '')}[/dim]\n")
