"""LED command group — WS2812 / NeoPixel style LEDs.

Architecture Notes:
    LED control is exposed as a top-level convenience command (no board
    qualifier), analogous to `docker ps` vs `docker container ls`.

    Future Implementation:
        - Target the default or active board's LED peripheral.
        - Route through TRT Protocol LED_SET message.
        - Support multiple LED strips / indices.
        - Support animations and sequences.
"""

import typer
from rich.console import Console

console = Console()
app = typer.Typer(
    help="LED control (WS2812 / NeoPixel)",
    no_args_is_help=True,
)


@app.command(help="Turn LEDs on (full white at current brightness)")
def on() -> None:
    """Turn all LEDs on.

    Future: sends TRT Protocol LED_ON to the active board.
    """
    _mock_action("LED ON")


@app.command(help="Turn LEDs off")
def off() -> None:
    """Turn all LEDs off.

    Future: sends TRT Protocol LED_OFF to the active board.
    """
    _mock_action("LED OFF")


@app.command(help="Blink LEDs (toggle pattern)")
def blink(
    count: int = typer.Option(3, "--count", "-n", help="Number of blink cycles"),
    interval_ms: int = typer.Option(500, "--interval", "-i", help="Blink interval in ms"),
) -> None:
    """Blink all LEDs.

    Future: sends TRT Protocol LED_BLINK with count and interval parameters.
    """
    _mock_action(f"LED BLINK  count={count}  interval={interval_ms}ms")


@app.command(help="Set LED brightness.  Range: 0–100")
def brightness(
    level: int = typer.Argument(..., min=0, max=100, help="Brightness level (0-100)"),
) -> None:
    """Set LED brightness level.

    Future: sends TRT Protocol LED_BRIGHTNESS with the given level (0–255 internally).
    """
    _mock_action(f"LED BRIGHTNESS  level={level}%")


@app.command(help="Set LED colour.  Example: trt led color 255 0 0")
def color(
    red:   int = typer.Argument(..., min=0, max=255, help="Red channel (0-255)"),
    green: int = typer.Argument(..., min=0, max=255, help="Green channel (0-255)"),
    blue:  int = typer.Argument(..., min=0, max=255, help="Blue channel (0-255)"),
) -> None:
    """Set LED colour via RGB values.

    Future: sends TRT Protocol LED_COLOR with 24-bit RGB payload.
    """
    swatch = f"rgb({red},{green},{blue})"
    _mock_action(f"LED COLOR  r=[red]{red}[/red]  g=[green]{green}[/green]  b=[blue]{blue}[/blue]  → {swatch}")


def _mock_action(label: str) -> None:
    console.print()
    console.print(f"  [yellow]{label}[/yellow]  [dim](mock: no hardware connected)[/dim]")
    console.print(
        "\n  [dim]Hardware not connected.  "
        "LED support will be activated once TRT Protocol is implemented.[/dim]\n"
    )
