"""Application service layer for board operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from trt.core.models import Board
from trt.protocol.models import (
    AdcListRequest,
    AdcReadRequest,
    BoardInfoRequest,
    BoardRebootRequest,
    BoardResetRequest,
    BuildIdRequest,
    DacListRequest,
    DacReadRequest,
    DacSetRequest,
    DebugLogsRequest,
    DebugMonitorRequest,
    DebugShellRequest,
    GetVersionRequest,
    GpioListRequest,
    GpioReadRequest,
    GpioWriteRequest,
    I2cReadRequest,
    I2cScanRequest,
    I2cWriteRequest,
    ModulesListRequest,
    ProtocolRequest,
    PwmListRequest,
    PwmSetRequest,
    PwmStartRequest,
    PwmStopRequest,
    SpiConfigRequest,
    SpiTransferRequest,
)
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient
from trt.protocol.v01 import decode_capability_ids, decode_info_payload
from trt.repositories.board_cache import load_serial_connections, save_serial_connections
from trt.repositories.board_repository import BoardRepository
from trt.services.board_discovery_service import BoardDiscoveryService
from trt.services.capability_service import CapabilityService


@dataclass
class BoardActionResult:
    """Simple result DTO for a board action."""

    status: str
    payload: str | dict[str, Any] | list[dict[str, Any]] | None = None
    board_id: str | None = None
    mock: bool = False


@dataclass(frozen=True)
class RealBoardInfoResult:
    """Real board identity read from TRT firmware."""

    board_id: str
    board_info: str
    fw_version: str
    build_id: str
    port: str
    board_version: str = ""
    info: dict[str, str] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()


class BoardService:
    """Application service responsible for board-level operations."""

    def __init__(
        self,
        repository: BoardRepository | None = None,
        capability_service: CapabilityService | None = None,
        protocol_client: ProtocolClient | None = None,
    ) -> None:
        self.repository = repository or BoardRepository()
        self.capability_service = capability_service or CapabilityService()
        self.protocol_client = protocol_client or MockProtocolClient()
        if repository is None:
            discovery = BoardDiscoveryService(self.repository, protocol_client)
            discovery.discover()
            self.repository = discovery.repository

    def get_board(self, board_id: str) -> Board | None:
        return self.repository.get_by_id(board_id)

    def list_boards(self) -> list[Board]:
        return self.repository.get_all()

    def require_board(self, board_id: str) -> Board:
        board = self.get_board(board_id)
        if board is None:
            raise ValueError(f"Board {board_id} not found")
        return board

    def ensure_capability(self, board_id: str, capability: str) -> Board:
        board = self.require_board(board_id)
        if not self.capability_service.supports(board, capability):
            raise ValueError(f"Board {board_id} does not support {capability}")
        return board

    def execute(self, request: ProtocolRequest) -> BoardActionResult:
        if request.capability:
            self.ensure_capability(request.board_id, request.capability)
        else:
            self.require_board(request.board_id)

        response = self.protocol_client.send(request)
        return BoardActionResult(
            status=response.status,
            payload=response.to_payload(),
            board_id=request.board_id,
            mock=response.mock,
        )

    def list_modules(self, board_id: str) -> BoardActionResult:
        return self.execute(ModulesListRequest(board_id=board_id))

    def reset(self, board_id: str) -> BoardActionResult:
        return self.execute(BoardResetRequest(board_id=board_id))

    def reboot(self, board_id: str) -> BoardActionResult:
        return self.execute(BoardRebootRequest(board_id=board_id))

    def list_gpio(self, board_id: str) -> BoardActionResult:
        return self.execute(GpioListRequest(board_id=board_id))

    def read_gpio(self, board_id: str, pin: str) -> BoardActionResult:
        return self.execute(GpioReadRequest(board_id=board_id, pin=pin))

    def write_gpio(self, board_id: str, pin: str, value: int) -> BoardActionResult:
        return self.execute(GpioWriteRequest(board_id=board_id, pin=pin, value=value))

    def list_pwm(self, board_id: str) -> BoardActionResult:
        return self.execute(PwmListRequest(board_id=board_id))

    def start_pwm(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(PwmStartRequest(board_id=board_id, channel=channel))

    def stop_pwm(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(PwmStopRequest(board_id=board_id, channel=channel))

    def set_pwm(self, board_id: str, channel: int, frequency: float, duty: float) -> BoardActionResult:
        return self.execute(PwmSetRequest(board_id=board_id, channel=channel, frequency=frequency, duty=duty))

    def list_adc(self, board_id: str) -> BoardActionResult:
        return self.execute(AdcListRequest(board_id=board_id))

    def read_adc(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(AdcReadRequest(board_id=board_id, channel=channel))

    def list_dac(self, board_id: str) -> BoardActionResult:
        return self.execute(DacListRequest(board_id=board_id))

    def read_dac(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(DacReadRequest(board_id=board_id, channel=channel))

    def set_dac(self, board_id: str, channel: int, value: int) -> BoardActionResult:
        return self.execute(DacSetRequest(board_id=board_id, channel=channel, value=value))

    def scan_i2c(self, board_id: str) -> BoardActionResult:
        return self.execute(I2cScanRequest(board_id=board_id))

    def read_i2c(self, board_id: str, address: str, register: str, length: int) -> BoardActionResult:
        return self.execute(I2cReadRequest(board_id=board_id, address=address, register=register, length=length))

    def write_i2c(self, board_id: str, address: str, register: str, data: str) -> BoardActionResult:
        return self.execute(I2cWriteRequest(board_id=board_id, address=address, register=register, data=data))

    def transfer_spi(self, board_id: str, data: str) -> BoardActionResult:
        return self.execute(SpiTransferRequest(board_id=board_id, data=data))

    def config_spi(self, board_id: str, baudrate: int, mode: int, msb_first: bool) -> BoardActionResult:
        return self.execute(SpiConfigRequest(board_id=board_id, baudrate=baudrate, mode=mode, msb_first=msb_first))

    def debug_logs(self, board_id: str, follow: bool = False) -> BoardActionResult:
        return self.execute(DebugLogsRequest(board_id=board_id, follow=follow))

    def debug_monitor(self, board_id: str) -> BoardActionResult:
        return self.execute(DebugMonitorRequest(board_id=board_id))

    def debug_shell(self, board_id: str) -> BoardActionResult:
        return self.execute(DebugShellRequest(board_id=board_id))

    def board_info(self, board_id: str) -> Board | None:
        return self.get_board(board_id)

    def real_board_info(self, board_id: str, port: str | None = None) -> RealBoardInfoResult:
        from trt.protocol.serial_protocol_client import SerialProtocolClient
        from trt.transport.serial_transport import SerialTransport

        try:
            numeric_board_id = int(board_id, 0)
        except ValueError:
            if not board_id.isdigit():
                raise ValueError(f"Serial TRT board id must be numeric, got {board_id!r}")
            numeric_board_id = int(board_id)
        resolved_board_id = str(numeric_board_id)
        baudrate = 115200
        if port is None:
            saved_connection = load_serial_connections().get(resolved_board_id)
            if saved_connection is not None:
                port = saved_connection["port"]
                baudrate = saved_connection["baudrate"]
            else:
                discovery = BoardDiscoveryService()
                discovery.discover_serial()
                board = discovery.repository.get_by_id(resolved_board_id)
                if board is None or board.transport is None or board.transport.port is None:
                    raise ValueError(
                        f"Board {resolved_board_id} was not discovered. "
                        "Run 'trt discover' or pass --port COMx."
                    )
                port = board.transport.port
                baudrate = board.transport.baudrate or baudrate

        transport = SerialTransport(port=port, baudrate=baudrate)
        try:
            ping = transport.exchange_command(0x0001, resolved_board_id)
            if ping.command == 0x8001:
                resolved_board_id = str(ping.board_id)
                board_version = transport.exchange_command(0x0003, resolved_board_id)
                info_frame = transport.exchange_command(0x0004, resolved_board_id)
                capabilities_frame = transport.exchange_command(0x0006, resolved_board_id)
                version_frame = transport.exchange_command(0x0002, resolved_board_id)
                build_frame = transport.exchange_command(0x0007, resolved_board_id)
                frames = (board_version, info_frame, capabilities_frame, version_frame, build_frame)
                for response in frames:
                    if response.board_id != ping.board_id or response.command != 0x8003:
                        raise ValueError(
                            f"Unexpected response 0x{response.command:04X} "
                            f"for board {resolved_board_id}"
                        )
                info = decode_info_payload(info_frame.payload)
                capability_ids = decode_capability_ids(capabilities_frame.payload)
                if capability_ids is None:
                    raise ValueError("CAPABILITIES response has an invalid V0.1 payload")
                capability_names = {
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
                result = RealBoardInfoResult(
                    board_id=resolved_board_id,
                    board_info=info.get("board_type", "Unknown"),
                    fw_version=".".join(str(value) for value in version_frame.payload),
                    build_id=build_frame.payload.decode("utf-8", errors="replace"),
                    port=port,
                    board_version=board_version.payload.decode("utf-8", errors="replace"),
                    info=info,
                    capabilities=tuple(
                        capability_names.get(value, f"0x{value:04X}")
                        for value in capability_ids
                    ),
                )
                save_serial_connections(
                    {resolved_board_id: {"port": port, "baudrate": baudrate}}
                )
                return result
            if ping.command != 0x8002:
                raise ValueError(f"PING returned unexpected response 0x{ping.command:04X}")

            protocol_client = SerialProtocolClient(transport)
            info_response = protocol_client.send(BoardInfoRequest(board_id=resolved_board_id))
            version_response = protocol_client.send(GetVersionRequest(board_id=resolved_board_id))
            build_response = protocol_client.send(BuildIdRequest(board_id=resolved_board_id))
        finally:
            transport.close()

        result = RealBoardInfoResult(
            board_id=resolved_board_id,
            board_info=str(info_response.to_payload().get("board_type", "")),
            fw_version=str(version_response.to_payload().get("version", "")),
            build_id=str(build_response.to_payload().get("build_id", "")),
            port=port,
        )
        save_serial_connections({resolved_board_id: {"port": port, "baudrate": baudrate}})
        return result
