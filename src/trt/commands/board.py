"""Board command group — all per-board sub-commands.

Usage:
    trt board <sub-command> <board_id> [args]

Examples:
    trt board info board0
    trt board gpio write board0 PA5 1
    trt board pwm set board0 1 1000 50
    trt board adc read board0 3
    trt board i2c scan board0

Command Philosophy:
    TRT follows the <verb> <resource> pattern used by docker, git, and kubectl:
        trt board info board0         (verb=info, board=board0)
        trt board gpio read board0 PA5 (verb=read, board=board0, pin=PA5)

    This is consistent and requires no callback trickery across Typer versions.
"""

from typing import Optional

import typer
from rich.console import Console

from trt.core.models import make_mock_registry

console = Console()


# ---------------------------------------------------------------------------
# Top-level board app
# ---------------------------------------------------------------------------

board_app = typer.Typer(
    help="Operate on a specific board.  Usage: trt board <command> <board_id>",
    no_args_is_help=True,
)

# ---------------------------------------------------------------------------
# Top-level board sub-commands
# ---------------------------------------------------------------------------

@board_app.command("info", help="Show board identity and firmware information")
def board_info(
    board_id: str = typer.Argument(..., help="Board identifier, e.g. board0"),
) -> None:
    """Display board identity from the registry."""
    registry = make_mock_registry()
    board = registry.get(board_id)
    console.print()
    if board is None:
        _board_not_found(board_id)
        raise typer.Exit(1)
    ident = board.identity
    from rich.panel import Panel
    from rich.table import Table as RichTable
    table = RichTable(show_header=False, box=None, padding=(0, 2))
    table.add_column("key",   style="dim",        min_width=18)
    table.add_column("value", style="bold white")
    table.add_row("Board ID",   ident.board_id)
    table.add_row("Type",       ident.board_type.value)
    table.add_row("Revision",   ident.revision)
    table.add_row("Firmware",   ident.firmware)
    table.add_row("Serial",     ident.serial or "—")
    table.add_row("Status",     board.status.value)
    table.add_row("Transport",  str(board.transport) if board.transport else "—")
    console.print(Panel(table, title=f"[bold cyan]{board_id}[/bold cyan]", border_style="bright_blue", expand=False))
    console.print()


@board_app.command("status", help="Show current board status")
def board_status(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    """Show the operational status of the board."""
    registry = make_mock_registry()
    board = registry.get(board_id)
    console.print()
    if board is None:
        _board_not_found(board_id)
        raise typer.Exit(1)
    style = "green" if board.is_ready() else "yellow"
    console.print(f"  [cyan]{board_id}[/cyan]  status: [{style}]{board.status.value}[/{style}]")
    console.print()


@board_app.command("reset", help="Reset the board")
def board_reset(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    """Send a reset command to the board."""
    _mock_action(board_id, "board reset")


@board_app.command("reboot", help="Reboot the board into normal firmware")
def board_reboot(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    """Reboot the board."""
    _mock_action(board_id, "board reboot")


@board_app.command("capabilities", help="List all capabilities advertised by the board")
def board_capabilities(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    """List capabilities advertised by the board."""
    registry = make_mock_registry()
    board = registry.get(board_id)
    console.print()
    if board is None:
        _board_not_found(board_id)
        raise typer.Exit(1)
    from rich.table import Table as RichTable
    caps = board.capabilities.as_dict()
    table = RichTable(show_header=True, header_style="bold bright_white", border_style="dim", box=None, padding=(0, 2))
    table.add_column("Capability", style="bold cyan", min_width=18)
    table.add_column("Supported",  min_width=10)
    for cap, supported in caps.items():
        icon = "[green]✓ yes[/green]" if supported else "[dim]✗ no[/dim]"
        table.add_row(cap, icon)
    console.print(f"  [bold cyan]Capabilities — [yellow]{board_id}[/yellow][/bold cyan]")
    console.print(table)
    console.print()


@board_app.command("modules", help="List loaded modules on the board")
def board_modules(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    """List firmware modules loaded on the board."""
    console.print()
    console.print(f"  [bold cyan]Modules — [yellow]{board_id}[/yellow][/bold cyan]")
    console.print("  [dim]No module data — firmware not connected.[/dim]")
    _mock_note(board_id)


# ---------------------------------------------------------------------------
# GPIO sub-app
# ---------------------------------------------------------------------------

gpio_app = typer.Typer(help="GPIO control", no_args_is_help=True)
board_app.add_typer(gpio_app, name="gpio")


@gpio_app.command("list", help="List all GPIO pins and their current state")
def gpio_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "gpio")
    console.print()
    console.print(f"  [bold cyan]GPIO pins on [yellow]{board_id}[/yellow][/bold cyan]")
    _mock_table(
        ["Pin", "Direction", "Value"],
        [("PA0", "INPUT", "0"), ("PA1", "INPUT", "1"),
         ("PA5", "OUTPUT", "1"), ("PB3", "OUTPUT", "0")],
    )
    _mock_note(board_id)


@gpio_app.command("read", help="Read a GPIO pin value.  Example: trt board gpio read board0 PA5")
def gpio_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    pin: str = typer.Argument(..., help="Pin name (e.g. PA5)"),
) -> None:
    _require_board(board_id, "gpio")
    console.print()
    console.print(f"  [cyan]{board_id}[/cyan]  gpio read  [yellow]{pin}[/yellow]  →  [green]0[/green]  [dim](mock)[/dim]")
    console.print()


@gpio_app.command("write", help="Write a GPIO pin value.  Example: trt board gpio write board0 PA5 1")
def gpio_write(
    board_id: str = typer.Argument(..., help="Board identifier"),
    pin:      str = typer.Argument(..., help="Pin name (e.g. PA5)"),
    value:    int = typer.Argument(..., min=0, max=1, help="Value to write: 0 or 1"),
) -> None:
    _require_board(board_id, "gpio")
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  gpio write  [yellow]{pin}[/yellow]  ←  [green]{value}[/green]"
        "  [dim](mock)[/dim]"
    )
    console.print()


# ---------------------------------------------------------------------------
# PWM sub-app
# ---------------------------------------------------------------------------

pwm_app = typer.Typer(help="PWM control", no_args_is_help=True)
board_app.add_typer(pwm_app, name="pwm")


@pwm_app.command("list", help="List all PWM channels")
def pwm_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "pwm")
    console.print()
    console.print(f"  [bold cyan]PWM channels on [yellow]{board_id}[/yellow][/bold cyan]")
    _mock_table(
        ["Channel", "Frequency (Hz)", "Duty (%)", "State"],
        [("1", "1000", "50", "STOPPED"), ("2", "20000", "25", "STOPPED")],
    )
    _mock_note(board_id)


@pwm_app.command("start", help="Start PWM output on a channel")
def pwm_start(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel:  int = typer.Argument(..., help="PWM channel number"),
) -> None:
    _require_board(board_id, "pwm")
    _mock_action(board_id, f"pwm start  channel=[yellow]{channel}[/yellow]")


@pwm_app.command("stop", help="Stop PWM output on a channel")
def pwm_stop(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel:  int = typer.Argument(..., help="PWM channel number"),
) -> None:
    _require_board(board_id, "pwm")
    _mock_action(board_id, f"pwm stop  channel=[yellow]{channel}[/yellow]")


@pwm_app.command("set", help="Set PWM frequency and duty.  Example: trt board pwm set board0 1 1000 50")
def pwm_set(
    board_id:  str   = typer.Argument(..., help="Board identifier"),
    channel:   int   = typer.Argument(..., help="PWM channel number"),
    frequency: float = typer.Argument(..., help="Frequency in Hz"),
    duty:      float = typer.Argument(..., min=0.0, max=100.0, help="Duty cycle 0–100 %"),
) -> None:
    _require_board(board_id, "pwm")
    _mock_action(
        board_id,
        f"pwm set  ch=[yellow]{channel}[/yellow]  freq=[cyan]{frequency}Hz[/cyan]  duty=[green]{duty}%[/green]",
    )


# ---------------------------------------------------------------------------
# ADC sub-app
# ---------------------------------------------------------------------------

adc_app = typer.Typer(help="ADC (Analog-to-Digital) control", no_args_is_help=True)
board_app.add_typer(adc_app, name="adc")


@adc_app.command("list", help="List all ADC channels")
def adc_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "adc")
    console.print()
    console.print(f"  [bold cyan]ADC channels on [yellow]{board_id}[/yellow][/bold cyan]")
    _mock_table(
        ["Channel", "Resolution (bits)", "Reference", "Last Value"],
        [("1", "12", "3.3V", "—"), ("2", "12", "3.3V", "—"), ("3", "12", "3.3V", "—")],
    )
    _mock_note(board_id)


@adc_app.command("read", help="Read an ADC channel value.  Example: trt board adc read board0 3")
def adc_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel:  int = typer.Argument(..., help="ADC channel number"),
) -> None:
    _require_board(board_id, "adc")
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  adc read  ch=[yellow]{channel}[/yellow]  →  "
        "[green]0 (0.00 mV)[/green]  [dim](mock)[/dim]"
    )
    console.print()


# ---------------------------------------------------------------------------
# DAC sub-app
# ---------------------------------------------------------------------------

dac_app = typer.Typer(help="DAC (Digital-to-Analog) control", no_args_is_help=True)
board_app.add_typer(dac_app, name="dac")


@dac_app.command("list", help="List all DAC channels")
def dac_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "dac")
    console.print()
    console.print(f"  [bold cyan]DAC channels on [yellow]{board_id}[/yellow][/bold cyan]")
    _mock_table(
        ["Channel", "Resolution (bits)", "Reference", "Current Value"],
        [("1", "12", "3.3V", "0"), ("2", "12", "3.3V", "0")],
    )
    _mock_note(board_id)


@dac_app.command("read", help="Read a DAC channel value")
def dac_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel:  int = typer.Argument(..., help="DAC channel number"),
) -> None:
    _require_board(board_id, "dac")
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  dac read  ch=[yellow]{channel}[/yellow]  →  "
        "[green]0 (0.00 mV)[/green]  [dim](mock)[/dim]"
    )
    console.print()


@dac_app.command("set", help="Set a DAC channel output value.  Example: trt board dac set board0 1 2048")
def dac_set(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel:  int = typer.Argument(..., help="DAC channel number"),
    value:    int = typer.Argument(..., help="Raw DAC value (0–4095 for 12-bit)"),
) -> None:
    _require_board(board_id, "dac")
    _mock_action(board_id, f"dac set  ch=[yellow]{channel}[/yellow]  value=[green]{value}[/green]")


# ---------------------------------------------------------------------------
# I2C sub-app
# ---------------------------------------------------------------------------

i2c_app = typer.Typer(help="I2C master interface", no_args_is_help=True)
board_app.add_typer(i2c_app, name="i2c")


@i2c_app.command("scan", help="Scan the I2C bus for devices")
def i2c_scan(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "i2c")
    console.print()
    console.print(f"  [bold cyan]I2C scan on [yellow]{board_id}[/yellow][/bold cyan]")
    console.print("  [dim]No devices found — mock scan, no hardware connected.[/dim]")
    console.print()
    _mock_note(board_id)


@i2c_app.command("read", help="Read bytes from an I2C device")
def i2c_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    address:  str = typer.Option("0x48", "--addr", "-a", help="I2C device address (hex)"),
    register: str = typer.Option("0x00", "--reg",  "-r", help="Register address (hex)"),
    length:   int = typer.Option(1,      "--len",  "-n", help="Number of bytes to read"),
) -> None:
    _require_board(board_id, "i2c")
    _mock_action(
        board_id,
        f"i2c read  addr=[yellow]{address}[/yellow]  reg=[cyan]{register}[/cyan]  len=[white]{length}[/white]",
    )


@i2c_app.command("write", help="Write bytes to an I2C device")
def i2c_write(
    board_id: str = typer.Argument(..., help="Board identifier"),
    address:  str = typer.Option("0x48", "--addr", "-a", help="I2C device address (hex)"),
    register: str = typer.Option("0x00", "--reg",  "-r", help="Register address (hex)"),
    data:     str = typer.Option("0x00", "--data", "-d", help="Hex bytes to write"),
) -> None:
    _require_board(board_id, "i2c")
    _mock_action(
        board_id,
        f"i2c write  addr=[yellow]{address}[/yellow]  reg=[cyan]{register}[/cyan]  data=[green]{data}[/green]",
    )


# ---------------------------------------------------------------------------
# SPI sub-app
# ---------------------------------------------------------------------------

spi_app = typer.Typer(help="SPI master interface", no_args_is_help=True)
board_app.add_typer(spi_app, name="spi")


@spi_app.command("transfer", help="Perform a full-duplex SPI transfer")
def spi_transfer(
    board_id: str = typer.Argument(..., help="Board identifier"),
    data:     str = typer.Option("0x00", "--data", "-d", help="Hex bytes to transmit"),
) -> None:
    _require_board(board_id, "spi")
    _mock_action(board_id, f"spi transfer  tx=[green]{data}[/green]  rx=[dim]0x00 (mock)[/dim]")


@spi_app.command("config", help="Configure SPI parameters")
def spi_config(
    board_id:  str  = typer.Argument(..., help="Board identifier"),
    baudrate:  int  = typer.Option(1_000_000, "--baud", "-b", help="Baudrate in Hz"),
    mode:      int  = typer.Option(0, "--mode", "-m", min=0, max=3, help="SPI mode (0-3)"),
    msb_first: bool = typer.Option(True, "--msb/--lsb", help="Bit order"),
) -> None:
    _require_board(board_id, "spi")
    _mock_action(
        board_id,
        f"spi config  baud=[cyan]{baudrate}Hz[/cyan]  mode=[yellow]{mode}[/yellow]  "
        f"order=[white]{'MSB' if msb_first else 'LSB'}[/white]",
    )


# ---------------------------------------------------------------------------
# Debug sub-app
# ---------------------------------------------------------------------------

debug_app = typer.Typer(help="Debug and diagnostics", no_args_is_help=True)
board_app.add_typer(debug_app, name="debug")


@debug_app.command("logs", help="Stream firmware debug logs from the board")
def debug_logs(
    board_id: str  = typer.Argument(..., help="Board identifier"),
    follow:   bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    _require_board(board_id, "debug_shell")
    console.print()
    console.print(f"  [bold cyan]Debug logs — [yellow]{board_id}[/yellow][/bold cyan]")
    console.print("  [dim]No log data — firmware not connected.[/dim]")
    console.print()
    _mock_note(board_id)


@debug_app.command("monitor", help="Live system monitor (CPU, memory, tasks)")
def debug_monitor(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "debug_shell")
    console.print()
    console.print(f"  [bold cyan]System monitor — [yellow]{board_id}[/yellow][/bold cyan]")
    console.print("  [dim]No data — firmware not connected.[/dim]")
    console.print()
    _mock_note(board_id)


@debug_app.command("shell", help="Open an interactive firmware debug shell")
def debug_shell(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _require_board(board_id, "debug_shell")
    console.print()
    console.print(
        f"  [bold cyan]Debug shell — [yellow]{board_id}[/yellow][/bold cyan]  "
        "[dim](mock — not connected)[/dim]"
    )
    console.print("  [dim]Interactive shell will be available once TRT Protocol is implemented.[/dim]")
    console.print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_board(board_id: str, capability: Optional[str] = None) -> None:
    registry = make_mock_registry()
    board = registry.get(board_id)
    if board is None:
        _board_not_found(board_id)
        raise typer.Exit(1)
    if capability and not board.capabilities.has(capability):
        console.print(
            f"\n  [yellow]Board [bold]{board_id}[/bold] does not advertise "
            f"capability [bold]{capability}[/bold].[/yellow]\n"
        )
        raise typer.Exit(1)


def _board_not_found(board_id: str) -> None:
    console.print(f"  [red]Board [bold]{board_id}[/bold] not found.[/red]")
    console.print("  Run [cyan]trt boards[/cyan] to see available boards.\n")


def _mock_action(board_id: str, label: str) -> None:
    console.print()
    console.print(f"  [cyan]{board_id}[/cyan]  [yellow]{label}[/yellow]  [dim](mock)[/dim]")
    console.print()


def _mock_note(board_id: str) -> None:
    console.print(
        f"  [dim]Mock data for [cyan]{board_id}[/cyan].  "
        "Real values will appear once TRT Protocol is implemented.[/dim]\n"
    )


def _mock_table(headers: list[str], rows: list[tuple[str, ...]]) -> None:
    from rich.table import Table as RichTable
    table = RichTable(show_header=True, header_style="bold bright_white", border_style="dim", box=None, padding=(0, 2))
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*row)
    console.print(table)
