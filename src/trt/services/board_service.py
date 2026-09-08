"""Application service layer for board operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trt.core.models import Board
from trt.protocol.models import ProtocolRequest
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


class BoardService:
    """Application service responsible for board-level operations.

    The CLI layer invokes this service, which then coordinates the repository,
    capability policy, and protocol client. Mock hardware behavior remains in the
    protocol transport layer rather than in the CLI command handlers.
    """

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

    def execute(
        self,
        board_id: str,
        operation: str,
        capability: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BoardActionResult:
        if capability:
            self.ensure_capability(board_id, capability)
        else:
            self.require_board(board_id)

        request = ProtocolRequest(
            operation=operation,
            board_id=board_id,
            capability=capability,
            payload=payload or {},
        )
        response = self.protocol_client.send(request)
        return BoardActionResult(status=response.status, payload=response.payload, board_id=board_id, mock=response.mock)

    def list_modules(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "modules_list", payload={})

    def reset(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "board_reset", payload={})

    def reboot(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "board_reboot", payload={})

    def list_gpio(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "gpio_list", "gpio")

    def read_gpio(self, board_id: str, pin: str) -> BoardActionResult:
        result = self.execute(board_id, "gpio_read", "gpio", {"pin": pin})
        return BoardActionResult(status=result.status, payload=f"{pin} -> {result.payload}", board_id=board_id, mock=result.mock)

    def write_gpio(self, board_id: str, pin: str, value: int) -> BoardActionResult:
        return self.execute(board_id, "gpio_write", "gpio", {"pin": pin, "value": value})

    def list_pwm(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "pwm_list", "pwm")

    def start_pwm(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(board_id, "pwm_start", "pwm", {"channel": channel})

    def stop_pwm(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(board_id, "pwm_stop", "pwm", {"channel": channel})

    def set_pwm(self, board_id: str, channel: int, frequency: float, duty: float) -> BoardActionResult:
        return self.execute(
            board_id,
            "pwm_set",
            "pwm",
            {"channel": channel, "frequency": frequency, "duty": duty},
        )

    def list_adc(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "adc_list", "adc")

    def read_adc(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(board_id, "adc_read", "adc", {"channel": channel})

    def list_dac(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "dac_list", "dac")

    def read_dac(self, board_id: str, channel: int) -> BoardActionResult:
        return self.execute(board_id, "dac_read", "dac", {"channel": channel})

    def set_dac(self, board_id: str, channel: int, value: int) -> BoardActionResult:
        return self.execute(board_id, "dac_set", "dac", {"channel": channel, "value": value})

    def scan_i2c(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "i2c_scan", "i2c")

    def read_i2c(self, board_id: str, address: str, register: str, length: int) -> BoardActionResult:
        return self.execute(
            board_id,
            "i2c_read",
            "i2c",
            {"address": address, "register": register, "length": length},
        )

    def write_i2c(self, board_id: str, address: str, register: str, data: str) -> BoardActionResult:
        return self.execute(
            board_id,
            "i2c_write",
            "i2c",
            {"address": address, "register": register, "data": data},
        )

    def transfer_spi(self, board_id: str, data: str) -> BoardActionResult:
        return self.execute(board_id, "spi_transfer", "spi", {"data": data})

    def config_spi(self, board_id: str, baudrate: int, mode: int, msb_first: bool) -> BoardActionResult:
        return self.execute(
            board_id,
            "spi_config",
            "spi",
            {"baudrate": baudrate, "mode": mode, "msb_first": msb_first},
        )

    def debug_logs(self, board_id: str, follow: bool = False) -> BoardActionResult:
        return self.execute(board_id, "debug_logs", "debug_shell", {"follow": follow})

    def debug_monitor(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "debug_monitor", "debug_shell")

    def debug_shell(self, board_id: str) -> BoardActionResult:
        return self.execute(board_id, "debug_shell", "debug_shell")

    def board_info(self, board_id: str) -> Board | None:
        return self.get_board(board_id)
