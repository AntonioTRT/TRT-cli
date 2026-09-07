"""Application service layer for board operations."""

from __future__ import annotations

from dataclasses import dataclass

from trt.core.models import Board
from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.protocol.protocol_client import MockProtocolClient
from trt.repositories.board_repository import BoardRepository
from trt.services.capability_service import CapabilityService


@dataclass
class BoardActionResult:
    """Simple result DTO for a board action."""

    status: str
    payload: str | dict[str, object] | None = None
    board_id: str | None = None


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
        protocol_client: MockProtocolClient | None = None,
    ) -> None:
        self.repository = repository or BoardRepository()
        self.capability_service = capability_service or CapabilityService()
        self.protocol_client = protocol_client or MockProtocolClient()

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

    def read_gpio(self, board_id: str, pin: str) -> BoardActionResult:
        board = self.ensure_capability(board_id, "gpio")
        request = ProtocolRequest(
            operation="gpio_read",
            board_id=board_id,
            capability="gpio",
            payload={"pin": pin, "value": "0"},
        )
        response = self.protocol_client.send(request)
        return BoardActionResult(status=response.status, payload=f"{pin} -> {response.payload}", board_id=board_id)

    def read_adc(self, board_id: str, channel: int) -> BoardActionResult:
        board = self.ensure_capability(board_id, "adc")
        request = ProtocolRequest(
            operation="adc_read",
            board_id=board_id,
            capability="adc",
            payload={"channel": channel},
        )
        response = self.protocol_client.send(request)
        return BoardActionResult(status=response.status, payload=f"ch{channel} -> {response.payload}", board_id=board_id)

    def scan_i2c(self, board_id: str) -> BoardActionResult:
        board = self.ensure_capability(board_id, "i2c")
        request = ProtocolRequest(
            operation="i2c_scan",
            board_id=board_id,
            capability="i2c",
            payload={},
        )
        response = self.protocol_client.send(request)
        return BoardActionResult(status=response.status, payload=response.payload, board_id=board_id)

    def transfer_spi(self, board_id: str, data: str) -> BoardActionResult:
        board = self.ensure_capability(board_id, "spi")
        request = ProtocolRequest(
            operation="spi_transfer",
            board_id=board_id,
            capability="spi",
            payload={"data": data},
        )
        response = self.protocol_client.send(request)
        return BoardActionResult(status=response.status, payload=response.payload, board_id=board_id)

    def board_info(self, board_id: str) -> Board | None:
        return self.get_board(board_id)
