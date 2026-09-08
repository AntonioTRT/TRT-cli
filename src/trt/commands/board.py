"""Board command group - per-board sub-commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from trt.core.models import Board
from trt.services.board_discovery_service import BoardDiscoveryService
from trt.services.board_service import BoardActionResult, BoardService, RealBoardInfoResult

console = Console()


board_app = typer.Typer(
    help="Operate on a specific board.  Usage: trt board <command> <board_id>",
    no_args_is_help=True,
)


@board_app.command("info", help="Show board identity and firmware information")
def board_info(
    board_id: str = typer.Argument(..., help="Board identifier, e.g. board0"),
) -> None:
    service = BoardService()
    if board_id.isdigit():
        try:
            _render_real_board_info(service.real_board_info(board_id, port="COM4"))
        except (RuntimeError, TimeoutError, ValueError) as error:
            console.print(f"\n  [red]Real TRT transaction failed:[/red] {error}\n")
            raise typer.Exit(1) from error
        return

    board = service.board_info(board_id)
    console.print()
    if board is None:
        _board_not_found(board_id)
        raise typer.Exit(1)
    _render_board_info(board_id, board)


@board_app.command("status", help="Show current board status")
def board_status(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    service = BoardService()
    board = service.get_board(board_id)
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
    _render_action(_run_board_action(board_id, lambda service: service.reset(board_id)))


@board_app.command("reboot", help="Reboot the board into normal firmware")
def board_reboot(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    _render_action(_run_board_action(board_id, lambda service: service.reboot(board_id)))


@board_app.command("capabilities", help="List all capabilities advertised by the board")
def board_capabilities(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    service = BoardService()
    if board_id.isdigit():
        discovery = BoardDiscoveryService()
        discovery.discover()
        board = discovery.repository.get_by_id(board_id)
        console.print()
        if board is None:
            _board_not_found(board_id)
            raise typer.Exit(1)
        _render_capabilities(board_id, board)
        return

    board = service.get_board(board_id)
    console.print()
    if board is None:
        _board_not_found(board_id)
        raise typer.Exit(1)
    _render_capabilities(board_id, board)


@board_app.command("modules", help="List loaded modules on the board")
def board_modules(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.list_modules(board_id))
    payload = _payload(result)
    console.print()
    console.print(f"  [bold cyan]Modules - [yellow]{board_id}[/yellow][/bold cyan]")
    console.print(f"  [dim]{payload.get('message', '')}[/dim]")
    _hardware_note(payload)


gpio_app = typer.Typer(help="GPIO control", no_args_is_help=True)
board_app.add_typer(gpio_app, name="gpio")


@gpio_app.command("list", help="List all GPIO pins and their current state")
def gpio_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.list_gpio(board_id))
    rows = _payload(result).get("pins", [])
    console.print()
    console.print(f"  [bold cyan]GPIO pins on [yellow]{board_id}[/yellow][/bold cyan]")
    _render_table(["Pin", "Direction", "Value"], rows, ["pin", "direction", "value"])
    _hardware_note(_payload(result))


@gpio_app.command("read", help="Read a GPIO pin value.  Example: trt board gpio read board0 PA5")
def gpio_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    pin: str = typer.Argument(..., help="Pin name (e.g. PA5)"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.read_gpio(board_id, pin))
    payload = _payload(result)
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  gpio read  [yellow]{payload.get('pin')}[/yellow]  ->  "
        f"[green]{payload.get('value')}[/green]  [dim](mock)[/dim]"
    )
    console.print()


@gpio_app.command("write", help="Write a GPIO pin value.  Example: trt board gpio write board0 PA5 1")
def gpio_write(
    board_id: str = typer.Argument(..., help="Board identifier"),
    pin: str = typer.Argument(..., help="Pin name (e.g. PA5)"),
    value: int = typer.Argument(..., min=0, max=1, help="Value to write: 0 or 1"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.write_gpio(board_id, pin, value))
    payload = _payload(result)
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  gpio write  [yellow]{payload.get('pin')}[/yellow]  <-  "
        f"[green]{payload.get('value')}[/green]  [dim](mock)[/dim]"
    )
    console.print()


pwm_app = typer.Typer(help="PWM control", no_args_is_help=True)
board_app.add_typer(pwm_app, name="pwm")


@pwm_app.command("list", help="List all PWM channels")
def pwm_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.list_pwm(board_id))
    rows = _payload(result).get("channels", [])
    console.print()
    console.print(f"  [bold cyan]PWM channels on [yellow]{board_id}[/yellow][/bold cyan]")
    _render_table(["Channel", "Frequency (Hz)", "Duty (%)", "State"], rows, ["channel", "frequency", "duty", "state"])
    _hardware_note(_payload(result))


@pwm_app.command("start", help="Start PWM output on a channel")
def pwm_start(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel: int = typer.Argument(..., help="PWM channel number"),
) -> None:
    _render_action(_run_board_action(board_id, lambda service: service.start_pwm(board_id, channel)))


@pwm_app.command("stop", help="Stop PWM output on a channel")
def pwm_stop(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel: int = typer.Argument(..., help="PWM channel number"),
) -> None:
    _render_action(_run_board_action(board_id, lambda service: service.stop_pwm(board_id, channel)))


@pwm_app.command("set", help="Set PWM frequency and duty.  Example: trt board pwm set board0 1 1000 50")
def pwm_set(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel: int = typer.Argument(..., help="PWM channel number"),
    frequency: float = typer.Argument(..., help="Frequency in Hz"),
    duty: float = typer.Argument(..., min=0.0, max=100.0, help="Duty cycle 0-100 %"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.set_pwm(board_id, channel, frequency, duty))
    payload = _payload(result)
    _render_action(
        result,
        f"pwm set  ch=[yellow]{payload.get('channel')}[/yellow]  "
        f"freq=[cyan]{payload.get('frequency')}Hz[/cyan]  duty=[green]{payload.get('duty')}%[/green]",
    )


adc_app = typer.Typer(help="ADC (Analog-to-Digital) control", no_args_is_help=True)
board_app.add_typer(adc_app, name="adc")


@adc_app.command("list", help="List all ADC channels")
def adc_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.list_adc(board_id))
    rows = _payload(result).get("channels", [])
    console.print()
    console.print(f"  [bold cyan]ADC channels on [yellow]{board_id}[/yellow][/bold cyan]")
    _render_table(["Channel", "Resolution (bits)", "Reference", "Last Value"], rows, ["channel", "resolution", "reference", "last_value"])
    _hardware_note(_payload(result))


@adc_app.command("read", help="Read an ADC channel value.  Example: trt board adc read board0 3")
def adc_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel: int = typer.Argument(..., help="ADC channel number"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.read_adc(board_id, channel))
    payload = _payload(result)
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  adc read  ch=[yellow]{payload.get('channel')}[/yellow]  ->  "
        f"[green]{payload.get('value')} ({payload.get('millivolts')} mV)[/green]  [dim](mock)[/dim]"
    )
    console.print()


dac_app = typer.Typer(help="DAC (Digital-to-Analog) control", no_args_is_help=True)
board_app.add_typer(dac_app, name="dac")


@dac_app.command("list", help="List all DAC channels")
def dac_list(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.list_dac(board_id))
    rows = _payload(result).get("channels", [])
    console.print()
    console.print(f"  [bold cyan]DAC channels on [yellow]{board_id}[/yellow][/bold cyan]")
    _render_table(["Channel", "Resolution (bits)", "Reference", "Current Value"], rows, ["channel", "resolution", "reference", "current_value"])
    _hardware_note(_payload(result))


@dac_app.command("read", help="Read a DAC channel value")
def dac_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel: int = typer.Argument(..., help="DAC channel number"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.read_dac(board_id, channel))
    payload = _payload(result)
    console.print()
    console.print(
        f"  [cyan]{board_id}[/cyan]  dac read  ch=[yellow]{payload.get('channel')}[/yellow]  ->  "
        f"[green]{payload.get('value')} ({payload.get('millivolts')} mV)[/green]  [dim](mock)[/dim]"
    )
    console.print()


@dac_app.command("set", help="Set a DAC channel output value.  Example: trt board dac set board0 1 2048")
def dac_set(
    board_id: str = typer.Argument(..., help="Board identifier"),
    channel: int = typer.Argument(..., help="DAC channel number"),
    value: int = typer.Argument(..., help="Raw DAC value (0-4095 for 12-bit)"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.set_dac(board_id, channel, value))
    payload = _payload(result)
    _render_action(result, f"dac set  ch=[yellow]{payload.get('channel')}[/yellow]  value=[green]{payload.get('value')}[/green]")


i2c_app = typer.Typer(help="I2C master interface", no_args_is_help=True)
board_app.add_typer(i2c_app, name="i2c")


@i2c_app.command("scan", help="Scan the I2C bus for devices")
def i2c_scan(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.scan_i2c(board_id))
    payload = _payload(result)
    console.print()
    console.print(f"  [bold cyan]I2C scan on [yellow]{board_id}[/yellow][/bold cyan]")
    if not payload.get("devices"):
        console.print(f"  [dim]{payload.get('message', '')}[/dim]")
    console.print()
    _hardware_note(payload)


@i2c_app.command("read", help="Read bytes from an I2C device")
def i2c_read(
    board_id: str = typer.Argument(..., help="Board identifier"),
    address: str = typer.Option("0x48", "--addr", "-a", help="I2C device address (hex)"),
    register: str = typer.Option("0x00", "--reg", "-r", help="Register address (hex)"),
    length: int = typer.Option(1, "--len", "-n", help="Number of bytes to read"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.read_i2c(board_id, address, register, length))
    payload = _payload(result)
    _render_action(
        result,
        f"i2c read  addr=[yellow]{payload.get('address')}[/yellow]  "
        f"reg=[cyan]{payload.get('register')}[/cyan]  len=[white]{payload.get('length')}[/white]",
    )


@i2c_app.command("write", help="Write bytes to an I2C device")
def i2c_write(
    board_id: str = typer.Argument(..., help="Board identifier"),
    address: str = typer.Option("0x48", "--addr", "-a", help="I2C device address (hex)"),
    register: str = typer.Option("0x00", "--reg", "-r", help="Register address (hex)"),
    data: str = typer.Option("0x00", "--data", "-d", help="Hex bytes to write"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.write_i2c(board_id, address, register, data))
    payload = _payload(result)
    _render_action(
        result,
        f"i2c write  addr=[yellow]{payload.get('address')}[/yellow]  "
        f"reg=[cyan]{payload.get('register')}[/cyan]  data=[green]{payload.get('data')}[/green]",
    )


spi_app = typer.Typer(help="SPI master interface", no_args_is_help=True)
board_app.add_typer(spi_app, name="spi")


@spi_app.command("transfer", help="Perform a full-duplex SPI transfer")
def spi_transfer(
    board_id: str = typer.Argument(..., help="Board identifier"),
    data: str = typer.Option("0x00", "--data", "-d", help="Hex bytes to transmit"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.transfer_spi(board_id, data))
    payload = _payload(result)
    _render_action(result, f"spi transfer  tx=[green]{payload.get('tx')}[/green]  rx=[dim]{payload.get('rx')} (mock)[/dim]")


@spi_app.command("config", help="Configure SPI parameters")
def spi_config(
    board_id: str = typer.Argument(..., help="Board identifier"),
    baudrate: int = typer.Option(1_000_000, "--baud", "-b", help="Baudrate in Hz"),
    mode: int = typer.Option(0, "--mode", "-m", min=0, max=3, help="SPI mode (0-3)"),
    msb_first: bool = typer.Option(True, "--msb/--lsb", help="Bit order"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.config_spi(board_id, baudrate, mode, msb_first))
    payload = _payload(result)
    order = "MSB" if payload.get("msb_first") else "LSB"
    _render_action(
        result,
        f"spi config  baud=[cyan]{payload.get('baudrate')}Hz[/cyan]  "
        f"mode=[yellow]{payload.get('mode')}[/yellow]  order=[white]{order}[/white]",
    )


debug_app = typer.Typer(help="Debug and diagnostics", no_args_is_help=True)
board_app.add_typer(debug_app, name="debug")


@debug_app.command("logs", help="Stream firmware debug logs from the board")
def debug_logs(
    board_id: str = typer.Argument(..., help="Board identifier"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.debug_logs(board_id, follow))
    _render_debug_result(board_id, "Debug logs", result)


@debug_app.command("monitor", help="Live system monitor (CPU, memory, tasks)")
def debug_monitor(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.debug_monitor(board_id))
    _render_debug_result(board_id, "System monitor", result)


@debug_app.command("shell", help="Open an interactive firmware debug shell")
def debug_shell(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    result = _run_board_action(board_id, lambda service: service.debug_shell(board_id))
    payload = _payload(result)
    console.print()
    console.print(f"  [bold cyan]Debug shell - [yellow]{board_id}[/yellow][/bold cyan]  [dim](mock - not connected)[/dim]")
    console.print(f"  [dim]{payload.get('message', '')}[/dim]")
    console.print()


def _run_board_action(board_id: str, action: Callable[[BoardService], BoardActionResult]) -> BoardActionResult:
    service = BoardService()
    try:
        return action(service)
    except ValueError as error:
        message = str(error)
        if "not found" in message:
            _board_not_found(board_id)
        else:
            console.print(f"\n  [yellow]{message}[/yellow]\n")
        raise typer.Exit(1) from error


def _payload(result: BoardActionResult) -> dict[str, Any]:
    return result.payload if isinstance(result.payload, dict) else {}


def _render_board_info(board_id: str, board: Board) -> None:
    ident = board.identity
    board_type = board.metadata.get("board_type", ident.board_type.value)
    build_id = board.metadata.get("build_id", ident.serial or "-")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="dim", min_width=18)
    table.add_column("value", style="bold white")
    table.add_row("Board ID", ident.board_id)
    table.add_row("Type", board_type)
    table.add_row("Revision", ident.revision)
    table.add_row("Firmware", ident.firmware)
    table.add_row("Build ID", build_id)
    table.add_row("Status", board.status.value)
    table.add_row("Transport", str(board.transport) if board.transport else "-")
    console.print(Panel(table, title=f"[bold cyan]{board_id}[/bold cyan]", border_style="bright_blue", expand=False))
    console.print()


def _render_real_board_info(result: RealBoardInfoResult) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="dim", min_width=18)
    table.add_column("value", style="bold white")
    table.add_row("Board ID", result.board_id)
    table.add_row("Port", result.port)
    table.add_row("BOARD_INFO", result.board_info)
    table.add_row("FW_VERSION", result.fw_version)
    table.add_row("BUILD_ID", result.build_id)
    console.print()
    console.print(Panel(table, title=f"[bold cyan]{result.board_id}[/bold cyan]", border_style="bright_blue", expand=False))
    console.print()


def _render_capabilities(board_id: str, board: Board) -> None:
    table = Table(show_header=True, header_style="bold bright_white", border_style="dim", box=None, padding=(0, 2))
    table.add_column("Capability", style="bold cyan", min_width=18)
    table.add_column("Supported", min_width=10)
    for capability, supported in board.capabilities.as_dict().items():
        table.add_row(capability, "[green]yes[/green]" if supported else "[dim]no[/dim]")
    console.print(f"  [bold cyan]Capabilities - [yellow]{board_id}[/yellow][/bold cyan]")
    console.print(table)
    console.print()


def _render_action(result: BoardActionResult, label: str | None = None) -> None:
    payload = _payload(result)
    console.print()
    console.print(f"  [cyan]{result.board_id}[/cyan]  [yellow]{label or payload.get('label', payload.get('operation', 'operation'))}[/yellow]  [dim](mock)[/dim]")
    console.print()


def _render_debug_result(board_id: str, title: str, result: BoardActionResult) -> None:
    payload = _payload(result)
    console.print()
    console.print(f"  [bold cyan]{title} - [yellow]{board_id}[/yellow][/bold cyan]")
    console.print(f"  [dim]{payload.get('message', '')}[/dim]")
    console.print()
    _hardware_note(payload)


def _render_table(headers: list[str], rows: object, keys: list[str]) -> None:
    table = Table(show_header=True, header_style="bold bright_white", border_style="dim", box=None, padding=(0, 2))
    for header in headers:
        table.add_column(header)
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                table.add_row(*(str(row.get(key, "")) for key in keys))
    console.print(table)


def _board_not_found(board_id: str) -> None:
    console.print(f"  [red]Board [bold]{board_id}[/bold] not found.[/red]")
    console.print("  Run [cyan]trt boards[/cyan] to see available boards.\n")


def _hardware_note(payload: dict[str, Any]) -> None:
    console.print(f"  [dim]{payload.get('note', '')}[/dim]\n")
