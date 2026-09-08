"""LED command group - WS2812 / NeoPixel style LEDs."""

from typing import Any

import typer
from rich.console import Console

from trt.protocol.models import ProtocolResponse
from trt.services.led_service import LEDService

console = Console()
app = typer.Typer(
    help="LED control (WS2812 / NeoPixel)",
    no_args_is_help=True,
)


@app.command(help="Turn LEDs on (full white at current brightness)")
def on() -> None:
    _render_action(LEDService().on())


@app.command(help="Turn LEDs off")
def off() -> None:
    _render_action(LEDService().off())


@app.command(help="Blink LEDs (toggle pattern)")
def blink(
    count: int = typer.Option(3, "--count", "-n", help="Number of blink cycles"),
    interval_ms: int = typer.Option(500, "--interval", "-i", help="Blink interval in ms"),
) -> None:
    response = LEDService().blink(count, interval_ms)
    payload = _payload(response)
    _render_action(response, f"{payload.get('label')}  count={payload.get('count')}  interval={payload.get('interval_ms')}ms")


@app.command(help="Set LED brightness.  Range: 0-100")
def brightness(
    level: int = typer.Argument(..., min=0, max=100, help="Brightness level (0-100)"),
) -> None:
    response = LEDService().brightness(level)
    payload = _payload(response)
    _render_action(response, f"{payload.get('label')}  level={payload.get('level')}%")


@app.command(help="Set LED colour.  Example: trt led color 255 0 0")
def color(
    red: int = typer.Argument(..., min=0, max=255, help="Red channel (0-255)"),
    green: int = typer.Argument(..., min=0, max=255, help="Green channel (0-255)"),
    blue: int = typer.Argument(..., min=0, max=255, help="Blue channel (0-255)"),
) -> None:
    response = LEDService().color(red, green, blue)
    payload = _payload(response)
    swatch = f"rgb({payload.get('red')},{payload.get('green')},{payload.get('blue')})"
    _render_action(
        response,
        f"{payload.get('label')}  r=[red]{payload.get('red')}[/red]  "
        f"g=[green]{payload.get('green')}[/green]  b=[blue]{payload.get('blue')}[/blue]  -> {swatch}",
    )


def _payload(response: ProtocolResponse) -> dict[str, Any]:
    return response.payload if isinstance(response.payload, dict) else {}


def _render_action(response: ProtocolResponse, label: str | None = None) -> None:
    payload = _payload(response)
    console.print()
    console.print(f"  [yellow]{label or payload.get('label')}[/yellow]  [dim](mock: no hardware connected)[/dim]")
    console.print(f"\n  [dim]{payload.get('note', '')}[/dim]\n")
