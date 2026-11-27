"""STM32 protocol diagnostics."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from trt.protocol.v01 import decode_capability_ids, decode_info_payload
from trt.services.board_discovery_service import BoardDiscoveryService
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


@app.command(
    "test",
    help=(
        "Run the full TRT v0.1 serial handshake against an STM32 board. Without --board-id the board is "
        "discovered automatically; if several boards answer, pass --board-id (and --port) to pick one."
    ),
)
def test_stm32(
    port: str | None = typer.Option(
        None,
        "--port",
        "-p",
        help="ST-LINK virtual COM port; scans serial ports when omitted",
    ),
    board_id: str | None = typer.Option(
        None,
        "--board-id",
        help=f"Board address to test, e.g. 201 for the current STM32 firmware. Default: discovered; {_BOARD_ID} (legacy PlatformIO image) if nothing is discovered",
    ),
) -> None:
    ports = [port] if port else SerialTransport.available_ports()
    if not ports:
        console.print("\n  [red]No serial ports found. Connect the Nucleo or pass --port COMx.[/red]\n")
        raise typer.Exit(1)

    if board_id is None:
        target = _discover_target(ports)
        if target is not None:
            board_id, ports = target
            console.print(f"  [dim]Discovered board {board_id} on {ports[0]}[/dim]")
        else:
            board_id = _BOARD_ID

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


def _discover_target(ports: list[str]) -> tuple[str, list[str]] | None:
    """Find the one board to test: ``(board_id, [port])``, or None to keep the legacy default.

    Uses the same probe as ``trt discover``. One board found: use its address. Several: prefer the
    single STM32 among them; if that is still ambiguous, refuse to guess and ask for --board-id.
    Nothing found (or discovery failed): None, so the caller keeps the pre-discovery behaviour.
    """
    try:
        boards = BoardDiscoveryService().discover_serial(ports)
    except (OSError, RuntimeError):
        return None
    found = [board for board in boards if board.transport is not None and board.transport.port]
    if len(found) > 1:
        stm32_boards = [b for b in found if "stm32" in str(b.metadata.get("board_type", "")).lower()]
        found = stm32_boards if len(stm32_boards) == 1 else found
    if not found:
        return None
    if len(found) > 1:
        console.print("\n  [red]Several TRT boards answered; choose one with --board-id (and --port):[/red]")
        for board in found:
            console.print(f"    {board.identity.board_id}  on {board.transport.port}")  # type: ignore[union-attr]
        console.print()
        raise typer.Exit(2)
    board = found[0]
    return board.identity.board_id, [str(board.transport.port)]  # type: ignore[union-attr]


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
