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
from trt.protocol.models import (
    BoardInfoRequest,
    BuildIdRequest,
    DiscoverRequest,
    DiscoverResponse,
    DiscoveredBoardPayload,
    GetCapabilitiesResponse,
    GetCapabilitiesRequest,
    GetVersionRequest,
    TransportPayload,
)
from trt.protocol.protocol_client import ProtocolClient
from trt.protocol.serial_protocol_client import SerialProtocolClient
from trt.repositories.board_repository import BoardRepository
from trt.transport.serial_transport import SerialTransport


class BoardDiscoveryService:
    """Encapsulates board discovery operations."""

    def __init__(
        self,
        repository: BoardRepository | None = None,
        protocol_client: ProtocolClient | None = None,
    ) -> None:
        self.repository = repository or BoardRepository()
        self.protocol_client = protocol_client

    def discover(self) -> list[Board]:
        if self.protocol_client is None:
            return self.discover_serial()

        response = self.protocol_client.send(DiscoverRequest())
        registry = BoardRegistry()

        if isinstance(response, DiscoverResponse):
            for item in response.boards:
                registry.register(self._board_from_payload(item))

        self.repository = BoardRepository(registry)
        return self.repository.get_all()

    def discover_serial(self) -> list[Board]:
        registry = BoardRegistry()
        for port in SerialTransport.available_ports():
            board = self._probe_port(port)
            if board is not None:
                registry.register(board)

        self.repository = BoardRepository(registry)
        return self.repository.get_all()

    def _probe_port(self, port: str) -> Board | None:
        for candidate_board_id in ("0", "101"):
            transport = SerialTransport(port=port, timeout=1.0)
            try:
                client = SerialProtocolClient(transport)
                info = client.send(BoardInfoRequest(board_id=candidate_board_id))
                version = client.send(GetVersionRequest(board_id=info.board_id or candidate_board_id))
                capabilities = client.send(GetCapabilitiesRequest(board_id=info.board_id or candidate_board_id))
                build = client.send(BuildIdRequest(board_id=info.board_id or candidate_board_id))
            except (OSError, RuntimeError, TimeoutError, ValueError):
                transport.close()
                continue
            transport.close()

            if not isinstance(capabilities, GetCapabilitiesResponse):
                continue

            return self._board_from_payload(
                DiscoveredBoardPayload(
                    board_id=info.board_id or candidate_board_id,
                    board_type=str(info.to_payload().get("board_type", "Unknown")),
                    revision="-",
                    firmware=str(version.to_payload().get("version", "")),
                    serial=str(build.to_payload().get("build_id", "")),
                    status=BoardStatus.READY.value,
                    transport=TransportPayload(transport_type=TransportType.USB.value, port=port),
                    capabilities=capabilities.capabilities,
                    build_id=str(build.to_payload().get("build_id", "")),
                )
            )

        return None

    def _board_from_payload(self, payload: DiscoveredBoardPayload) -> Board:
        capabilities = payload.capabilities
        transport = payload.transport
        try:
            board_type = BoardType(payload.board_type)
        except ValueError:
            board_type = BoardType.UNKNOWN
        return Board(
            identity=BoardIdentity(
                board_id=payload.board_id,
                board_type=board_type,
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
            metadata={
                "board_type": payload.board_type,
                "build_id": payload.build_id or "",
            },
        )
