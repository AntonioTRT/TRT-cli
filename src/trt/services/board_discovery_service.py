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
    DiscoveredBoardPayload,
    DiscoverRequest,
    DiscoverResponse,
    GetCapabilitiesRequest,
    GetCapabilitiesResponse,
    GetVersionRequest,
    TransportPayload,
)
from trt.protocol.protocol_client import ProtocolClient
from trt.protocol.serial_protocol_client import SerialProtocolClient
from trt.protocol.v01 import decode_info_payload
from trt.repositories.board_cache import SerialConnection, save_serial_connections
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
        connections: dict[str, SerialConnection] = {}
        for port in SerialTransport.available_ports():
            board = self._probe_port(port)
            if board is not None:
                registry.register(board)
                if board.transport and board.transport.port:
                    connections[board.identity.board_id] = {
                        "port": board.transport.port,
                        "baudrate": board.transport.baudrate or 115200,
                    }

        self.repository = BoardRepository(registry)
        if connections:
            save_serial_connections(connections)
        return self.repository.get_all()

    def _probe_port(self, port: str) -> Board | None:
        for candidate_board_id in ("2", "0", "101"):
            transport = SerialTransport(port=port, baudrate=115200, timeout=1.0)
            try:
                if candidate_board_id == "2":
                    board = self._probe_stm32(transport, candidate_board_id, port)
                    if board is not None:
                        return board
                    continue

                client = SerialProtocolClient(transport)
                info = client.send(BoardInfoRequest(board_id=candidate_board_id))
                version = client.send(GetVersionRequest(board_id=info.board_id or candidate_board_id))
                capabilities = client.send(GetCapabilitiesRequest(board_id=info.board_id or candidate_board_id))
                build = client.send(BuildIdRequest(board_id=info.board_id or candidate_board_id))
                board_type = str(info.to_payload().get("board_type", "Unknown"))
            except (OSError, RuntimeError, TimeoutError, ValueError):
                transport.close()
                continue
            transport.close()

            if not isinstance(capabilities, GetCapabilitiesResponse):
                continue

            return self._board_from_payload(
                DiscoveredBoardPayload(
                    board_id=info.board_id or candidate_board_id,
                    board_type=board_type,
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

    def _probe_stm32(self, transport: SerialTransport, board_id: str, port: str) -> Board | None:
        try:
            ping = transport.exchange_command(0x0001, board_id)
            if ping.command != 0x8001:
                return None

            discovered_id = str(ping.board_id)
            board_version = transport.exchange_command(0x0003, discovered_id)
            info = transport.exchange_command(0x0004, discovered_id)
            capabilities_response = transport.exchange_command(0x0006, discovered_id)
            firmware = transport.exchange_command(0x0002, discovered_id)
            build = transport.exchange_command(0x0007, discovered_id)
            responses = (board_version, info, capabilities_response, firmware, build)
            if any(frame.board_id != ping.board_id or frame.command != 0x8003 for frame in responses):
                return None

            info_fields = decode_info_payload(info.payload)
            capabilities = transport.decode_capabilities(capabilities_response.payload)
            return self._board_from_payload(
                DiscoveredBoardPayload(
                    board_id=discovered_id,
                    board_type=info_fields.get("board_type", "Unknown"),
                    revision=board_version.payload.decode("utf-8", errors="replace"),
                    firmware=".".join(str(value) for value in firmware.payload),
                    serial=info_fields.get("serial"),
                    status=BoardStatus.READY.value,
                    transport=TransportPayload(transport_type=TransportType.USB.value, port=port),
                    capabilities=capabilities,
                    build_id=build.payload.decode("utf-8", errors="replace"),
                )
            )
        except (OSError, RuntimeError, TimeoutError, ValueError):
            return None
        finally:
            transport.close()

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
                baudrate=115200 if transport.port else None,
            ),
            capabilities=BoardCapabilities(
                system=capabilities.system,
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
                led=capabilities.led,
            ),
            metadata={
                "board_type": payload.board_type,
                "build_id": payload.build_id or "",
            },
        )
