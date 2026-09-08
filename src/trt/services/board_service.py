"""Application service layer for board operations."""

from __future__ import annotations

from dataclasses import dataclass
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
    GpioListRequest,
    GpioReadRequest,
    GpioWriteRequest,
    GetVersionRequest,
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
            discovery = BoardDiscoveryService(self.repository, self.protocol_client)
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

    def real_board_info(self, board_id: str, port: str = "COM4") -> RealBoardInfoResult:
        from trt.protocol.serial_protocol_client import SerialProtocolClient
        from trt.transport.serial_transport import SerialTransport

        protocol_client = SerialProtocolClient(SerialTransport(port=port))
        info_response = protocol_client.send(BoardInfoRequest(board_id=board_id))
        version_response = protocol_client.send(GetVersionRequest(board_id=board_id))
        build_response = protocol_client.send(BuildIdRequest(board_id=board_id))

        return RealBoardInfoResult(
            board_id=board_id,
            board_info=str(info_response.to_payload().get("board_type", "")),
            fw_version=str(version_response.to_payload().get("version", "")),
            build_id=str(build_response.to_payload().get("build_id", "")),
            port=port,
        )
