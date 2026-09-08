"""Board discovery service."""

from __future__ import annotations

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
from trt.protocol.models import DiscoverRequest, DiscoverResponse, DiscoveredBoardPayload
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient
from trt.repositories.board_repository import BoardRepository


class BoardDiscoveryService:
    """Encapsulates board discovery operations."""

    def __init__(
        self,
        repository: BoardRepository | None = None,
        protocol_client: ProtocolClient | None = None,
    ) -> None:
        self.repository = repository or BoardRepository()
        self.protocol_client = protocol_client or MockProtocolClient()

    def discover(self) -> list[Board]:
        response = self.protocol_client.send(DiscoverRequest())
        registry = BoardRegistry()

        if isinstance(response, DiscoverResponse):
            for item in response.boards:
                registry.register(self._board_from_payload(item))

        self.repository = BoardRepository(registry)
        return self.repository.get_all()

    def _board_from_payload(self, payload: DiscoveredBoardPayload) -> Board:
        capabilities = payload.capabilities
        transport = payload.transport
        return Board(
            identity=BoardIdentity(
                board_id=payload.board_id,
                board_type=BoardType(payload.board_type),
                revision=payload.revision,
                firmware=payload.firmware,
                serial=payload.serial,
            ),
            status=BoardStatus(payload.status),
            transport=TransportConfig(
                transport_type=TransportType(transport.transport_type),
                port=transport.port,
            ),
            capabilities=BoardCapabilities(
                gpio=capabilities.gpio,
                pwm=capabilities.pwm,
                adc=capabilities.adc,
                dac=capabilities.dac,
                i2c=capabilities.i2c,
                spi=capabilities.spi,
                uart=capabilities.uart,
                can=capabilities.can,
                lcd=capabilities.lcd,
                relay=capabilities.relay,
                debug_shell=capabilities.debug_shell,
            ),
        )
