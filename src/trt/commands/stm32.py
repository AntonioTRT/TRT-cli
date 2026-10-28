"""STM32 protocol diagnostics."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from trt.protocol.v01 import decode_capability_ids, decode_info_payload
from trt.transport.serial_transport import SerialTransport

console = Console()
app = typer.Typer(help="STM32 board diagnostics", no_args_is_help=True)

_BOARD_ID = "0x0002"
_COMMANDS = (
    (0x0001, "PING", 0x8001),
    (0x0002, "FW_VERSION", 0x8003),
    (0x0003, "BOARD_VERSION", 0x8003),
    (0x0004, "INFO", 0x8003),
    (0x0005, "STATUS", 0x8003),
    (0x0006, "CAPABILITIES", 0x8003),
)
_CAPABILITY_NAMES = {
    0x0001: "SYSTEM",
    0x0002: "GPIO",
    0x0003: "PWM",
    0x0004: "ADC",
    0x0005: "DAC",
    0x0006: "SPI",
    0x0007: "I2C",
    0x0008: "LCD",
    0x0009: "LED",
    0x000A: "RELAY",
}
_STATUS_NAMES = {
    0x00: "BOOT",
    0x01: "READY",
    0x02: "BUSY",
    0x03: "WARNING",
    0x04: "ERROR",
    0x05: "FIRMWARE_UPDATE",
}


@app.command("test", help="Run the full TRT v0.1 serial handshake against an STM32 board")
def test_stm32(
    port: str | None = typer.Option(
        None,
        "--port",
        "-p",
        help="ST-LINK virtual COM port; scans serial ports when omitted",
    ),
    board_id: str = typer.Option(_BOARD_ID, "--board-id", help="TRT board id (default: 0x0002)"),
) -> None:
    ports = [port] if port else SerialTransport.available_ports()
    if not ports:
        console.print("\n  [red]No serial ports found. Connect the Nucleo or pass --port COMx.[/red]\n")
        raise typer.Exit(1)

    errors: list[str] = []
    for candidate in ports:
        transport = SerialTransport(port=candidate, baudrate=115200, timeout=2.0)
        try:
            _run_protocol_test(transport, board_id)
        except (OSError, RuntimeError, TimeoutError, ValueError) as error:
            errors.append(f"{candidate}: {error}")
            if port:
                console.print(f"\n  [red]STM32 protocol test failed on {candidate}:[/red] {error}\n")
                raise typer.Exit(1) from error
        else:
            return
        finally:
            transport.close()

    console.print("\n  [red]No TRT v0.1 STM32 board responded successfully.[/red]")
    for failure in errors:
        console.print(f"  [dim]{failure}[/dim]")
    console.print()
    raise typer.Exit(1)


def _run_protocol_test(transport: SerialTransport, board_id: str) -> None:
    table = Table(show_header=True, header_style="bold bright_white", box=None, padding=(0, 2))
    table.add_column("Command", style="cyan")
    table.add_column("Response", style="green")

    for command, name, expected_response in _COMMANDS:
        response = transport.exchange_command(command, board_id)
        if response.board_id != int(board_id, 0):
            raise ValueError(
                f"Response board id is 0x{response.board_id:04X}; "
                f"expected 0x{int(board_id, 0):04X}"
            )
        if response.command != expected_response:
            raise ValueError(
                f"{name} returned 0x{response.command:04X}; expected 0x{expected_response:04X}"
            )
        table.add_row(name, _format_response(command, response.payload))

    console.print(f"\n  [bold cyan]TRT v0.1 STM32 communication on {transport.port}[/bold cyan]")
    console.print("  [dim]115200 baud, 8N1[/dim]")
    console.print(table)
    console.print("\n  [bold green]All six protocol commands completed successfully.[/bold green]\n")


def _format_response(command: int, payload: bytes) -> str:
    if command == 0x0001:
        if payload:
            raise ValueError("PING ACK must not include a payload")
        return "ACK (0x8001)"
    if command == 0x0002:
        if len(payload) != 3:
            raise ValueError(f"FW_VERSION payload must contain three bytes, got {len(payload)}")
        return f"FW_VERSION {'.'.join(str(part) for part in payload)}"
    if command == 0x0003:
        if not payload:
            raise ValueError("BOARD_VERSION response payload is empty")
        return f"BOARD_VERSION {payload.decode('utf-8', errors='replace')}"
    if command == 0x0004:
        fields = decode_info_payload(payload)
        return "INFO " + ", ".join(f"{key}={value}" for key, value in fields.items())
    if command == 0x0005:
        if len(payload) != 1:
            raise ValueError(f"STATUS payload must contain one byte, got {len(payload)}")
        return f"STATUS {_STATUS_NAMES.get(payload[0], f'UNKNOWN (0x{payload[0]:02X})')}"
    if command == 0x0006:
        return "CAPABILITIES " + ", ".join(_decode_capability_names(payload))
    return payload.hex(" ")


def _decode_capability_names(payload: bytes) -> list[str]:
    identifiers = decode_capability_ids(payload)
    if identifiers is None:
        raise ValueError("CAPABILITIES response length does not match its count")
    return [_CAPABILITY_NAMES.get(identifier, f"0x{identifier:04X}") for identifier in identifiers]
