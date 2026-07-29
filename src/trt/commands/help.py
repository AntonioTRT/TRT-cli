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
    top.add_row("trt boards", "List all known boards")
    top.add_row("trt discover", "Rescan for connected boards (USB)")
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
        ("board info <id>",               "Board identity and firmware info"),
        ("board status <id>",             "Current board status"),
        ("board reset <id>",              "Reset the board"),
        ("board reboot <id>",             "Reboot the board"),
        ("board capabilities <id>",       "List board capabilities"),
        ("board modules <id>",            "List loaded modules on the board"),
        ("board gpio list <id>",          "List GPIO pins"),
        ("board gpio read <id> <pin>",    "Read a GPIO pin value"),
        ("board gpio write <id> <pin> <v>","Write a GPIO pin value"),
        ("board pwm list <id>",           "List PWM channels"),
        ("board pwm start <id> <ch>",     "Start PWM output on a channel"),
        ("board pwm stop <id> <ch>",      "Stop PWM output on a channel"),
        ("board pwm set <id> <ch> <f> <d>","Set PWM frequency and duty cycle"),
        ("board adc list <id>",           "List ADC channels"),
        ("board adc read <id> <ch>",      "Read an ADC channel value"),
        ("board dac list <id>",           "List DAC channels"),
        ("board dac read <id> <ch>",      "Read a DAC channel value"),
        ("board dac set <id> <ch> <v>",   "Set a DAC channel output value"),
        ("board i2c scan <id>",           "Scan I2C bus for devices"),
        ("board i2c read <id>",           "Read from an I2C device"),
        ("board i2c write <id>",          "Write to an I2C device"),
        ("board spi transfer <id>",       "SPI data transfer"),
        ("board spi config <id>",         "Configure SPI parameters"),
        ("board debug logs <id>",         "Stream firmware debug logs"),
        ("board debug monitor <id>",      "Live system monitor"),
        ("board debug shell <id>",        "Interactive firmware debug shell"),
    ]
    for cmd, desc in rows:
        board.add_row(cmd, desc)

    console.print(Padding("[bold]Board sub-commands[/bold]", (0, 2)))
    console.print(Padding(board, (0, 2)))
    console.print()

    # LCD / LED / Protocol
    extra = Table(
        show_header=True,
        header_style="bold bright_white",
        border_style="dim",
        box=None,
        padding=(0, 2),
    )
    extra.add_column("Command", style="bold yellow", min_width=30)
    extra.add_column("Description", style="white")

    extra.add_row("lcd info",             "LCD module information")
    extra.add_row("lcd reset",            "Reset the LCD display")
    extra.add_row("lcd clear",            "Clear the LCD display")
    extra.add_row('lcd write "<text>"',   "Write text to the LCD display")
    extra.add_row("led on",               "Turn LEDs on")
    extra.add_row("led off",              "Turn LEDs off")
    extra.add_row("led blink",            "Blink LEDs")
    extra.add_row("led brightness <n>",   "Set LED brightness (0-100)")
    extra.add_row("led color <r> <g> <b>","Set LED colour (RGB 0-255)")
    extra.add_row("protocol info",        "TRT Protocol specification info")
    extra.add_row("protocol version",     "TRT Protocol version")

    console.print(Padding("[bold]Peripheral commands[/bold]", (0, 2)))
    console.print(Padding(extra, (0, 2)))
    console.print()

    # Footer
    console.print(
        Padding(
            "[dim]Run [cyan]trt <command> --help[/cyan] for detailed usage of any command.[/dim]",
            (0, 2),
        )
    )
    console.print()

