"""Read-only board queries: information a board already knows, one value per command."""

from __future__ import annotations

from dataclasses import dataclass

from trt.protocol.v01 import decode_info_payload
from trt.services.board_service import resolve_serial_connection
from trt.transport.serial_transport import SerialTransport

CMD_FW_VERSION = 0x0002
CMD_BOARD_VERSION = 0x0003
CMD_INFO = 0x0004
CMD_BUILD_ID = 0x0007
CMD_UPTIME = 0x0008
CMD_RUNTIME = 0x0009
CMD_ACTIVE_PROGRAM = 0x000A

RESP_NACK = 0x8002
RESP_DATA = 0x8003

RUNTIME_STATES = {0x01: "RUNNING"}


class QueryUnsupportedError(RuntimeError):
    """The board's firmware does not provide this information."""


@dataclass(frozen=True)
class QueryResult:
    board_id: str
    item: str
    value: str


# Queries answered by one request: item -> (command, decoder of the DATA payload).
def _text(payload: bytes) -> str:
    return payload.decode("utf-8", errors="replace")


def _version(payload: bytes) -> str:
    return ".".join(str(part) for part in payload)


def _runtime(payload: bytes) -> str:
    if len(payload) != 1:
        raise ValueError("RUNTIME response must be 1 byte")
    return RUNTIME_STATES.get(payload[0], f"0x{payload[0]:02X}")


def format_uptime(milliseconds: int) -> str:
    seconds, ms = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    prefix = f"{days}d " if days else ""
    return f"{prefix}{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d} ({milliseconds} ms)"


def _uptime(payload: bytes) -> str:
    if len(payload) != 4:
        raise ValueError("UPTIME response must be 4 bytes")
    return format_uptime(int.from_bytes(payload, byteorder="big"))


_SIMPLE = {
    "version": (CMD_FW_VERSION, _version),
    "build-id": (CMD_BUILD_ID, _text),
    "revision": (CMD_BOARD_VERSION, _text),
    "runtime": (CMD_RUNTIME, _runtime),
    "uptime": (CMD_UPTIME, _uptime),
    "active-program": (CMD_ACTIVE_PROGRAM, _text),
}
# Queries answered from the INFO fields: item -> decoded field name.
_INFO_FIELDS = {"name": "board_type", "type": "family"}

ITEMS = ("id", "name", "type", "revision", "version", "build-id", "runtime", "active-program", "uptime", "transport")


class BoardQueryService:
    def query(self, board_id: str, item: str, port: str | None = None) -> QueryResult:
        if item not in ITEMS:
            raise ValueError(f"Unknown query {item!r}")
        resolved_id, port, baudrate = resolve_serial_connection(board_id, port)

        if item == "transport":
            # The host already knows how it reached the board; nothing is asked of the firmware.
            return QueryResult(resolved_id, item, f"serial ({port}, {baudrate} baud)")

        transport = SerialTransport(port=port, baudrate=baudrate)
        try:
            if item == "id":
                frame = transport.exchange_command(CMD_FW_VERSION, resolved_id)
                self._require_data(frame, item)
                return QueryResult(str(frame.board_id), item, str(frame.board_id))
            if item in _INFO_FIELDS:
                frame = transport.exchange_command(CMD_INFO, resolved_id)
                self._require_data(frame, item)
                fields = decode_info_payload(frame.payload)
                key = _INFO_FIELDS[item]
                if key not in fields:
                    raise QueryUnsupportedError(f"{item} is not reported by this board's firmware")
                return QueryResult(str(frame.board_id), item, fields[key])
            command, decode = _SIMPLE[item]
            frame = transport.exchange_command(command, resolved_id)
            self._require_data(frame, item)
            return QueryResult(str(frame.board_id), item, decode(frame.payload))
        finally:
            transport.close()

    @staticmethod
    def _require_data(frame: SerialTransport.Frame, item: str) -> None:
        if frame.command == RESP_NACK:
            raise QueryUnsupportedError(f"{item} is not supported by this board's firmware")
        if frame.command != RESP_DATA:
            raise ValueError(f"Unexpected response 0x{frame.command:04X} to {item} query")
