"""Board discovery service."""

from __future__ import annotations

from typing import Any

from trt.core.models import (
    Board,
    BoardCapabilities,
    BoardIdentity,
    BoardRegistry,
    BoardStatus,
    BoardType,
    TransportConfig,
    TransportType,
)
from trt.protocol.models import ProtocolRequest
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient
from trt.repositories.board_repository import BoardRepository


class BoardDiscoveryService:
    """Encapsulates board discovery operations.

    This service keeps discovery orchestration out of CLI command handlers and
    Discovery always flows through the protocol client. The current protocol
    client is mock-backed, while future clients can enumerate real transports.
    """

    def __init__(
        self,
        repository: BoardRepository | None = None,
        protocol_client: ProtocolClient | None = None,
    ) -> None:
        self.repository = repository or BoardRepository()
        self.protocol_client = protocol_client or MockProtocolClient()

    def discover(self) -> list[Board]:
        request = ProtocolRequest(operation="discover", board_id="*", capability="discovery")
        response = self.protocol_client.send(request)
        payload = response.payload if isinstance(response.payload, dict) else {}
        boards_payload = payload.get("boards", [])

        registry = BoardRegistry()
        if isinstance(boards_payload, list):
            for item in boards_payload:
                if isinstance(item, dict):
                    registry.register(self._board_from_payload(item))

        self.repository = BoardRepository(registry)
        return self.repository.get_all()

    def _board_from_payload(self, payload: dict[str, Any]) -> Board:
        capabilities = payload.get("capabilities", {})
        transport = payload.get("transport", {})
        return Board(
            identity=BoardIdentity(
                board_id=str(payload.get("board_id", "unknown")),
                board_type=BoardType(str(payload.get("board_type", BoardType.UNKNOWN.value))),
                revision=str(payload.get("revision", "A1")),
                firmware=str(payload.get("firmware", "0.1.0")),
                serial=str(payload.get("serial")) if payload.get("serial") is not None else None,
            ),
            status=BoardStatus(str(payload.get("status", BoardStatus.DISCONNECTED.value))),
            transport=TransportConfig(
                transport_type=TransportType(str(transport.get("transport_type", TransportType.USB.value))),
                port=str(transport.get("port")) if transport.get("port") is not None else None,
            ),
            capabilities=BoardCapabilities(
                gpio=bool(capabilities.get("gpio", False)),
                pwm=bool(capabilities.get("pwm", False)),
                adc=bool(capabilities.get("adc", False)),
                dac=bool(capabilities.get("dac", False)),
                i2c=bool(capabilities.get("i2c", False)),
                spi=bool(capabilities.get("spi", False)),
                uart=bool(capabilities.get("uart", False)),
                can=bool(capabilities.get("can", False)),
                lcd=bool(capabilities.get("lcd", False)),
                relay=bool(capabilities.get("relay", False)),
                debug_shell=bool(capabilities.get("debug_shell", False)),
            ),
        )
