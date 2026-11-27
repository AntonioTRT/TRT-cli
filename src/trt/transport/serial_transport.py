"""Serial transport for TRT V0.1 request/response transactions.

Request/response synchronisation: boards send unsolicited event frames (HEARTBEAT, about once per
second) on the same line. While waiting for a reply the transport skips event frames and stale replies
(a reply whose sequence ID belongs to an earlier, timed-out request). A request that collides with a
heartbeat can be lost on the board side (the frame is dropped); when the board is evidently alive
(it sent frames, just not our reply) the request is sent again, up to ``retries`` times. A silent port
fails after one attempt, so discovery stays fast on ports without a TRT board. Every command sent
through this transport is a read-only query, so repeating it is safe.
"""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Any

from trt.protocol.models import (
    BoardCapabilitiesPayload,
    BoardInfoRequest,
    BoardInfoResponse,
    BuildIdRequest,
    BuildIdResponse,
    GetCapabilitiesRequest,
    GetCapabilitiesResponse,
    GetVersionRequest,
    GetVersionResponse,
    ProtocolOperation,
    ProtocolRequest,
    ProtocolResponse,
)
from trt.protocol.v01 import decode_capability_ids
from trt.transport.base import Transport

try:
    import serial
    import serial.tools.list_ports
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    serial = None  # type: ignore[assignment]


class SerialTransport(Transport):
    """Open a serial port and exchange one TRT frame per request."""

    _SYNC = b"\xaa\x55"
    _VERSION = 1
    _FLAGS = 0
    _HEADER_SIZE = 12
    _CRC_SIZE = 2
    _MAX_FRAME_SIZE = 256
    _FLAG_EVENT = 0x02
    # Extra attempts after a lost request (board alive but no reply). Internal tuning knob.
    DEFAULT_RETRIES = 2

    _OPCODES: dict[ProtocolOperation, int] = {
        ProtocolOperation.GET_VERSION: 0x0002,
        ProtocolOperation.BOARD_INFO: 0x0003,
        ProtocolOperation.GET_CAPABILITIES: 0x0006,
        ProtocolOperation.BUILD_ID: 0x0007,
    }

    @dataclass(frozen=True)
    class Frame:
        board_id: int
        sequence_id: int
        command: int
        payload: bytes

    def __init__(
        self,
        port: str = "COM4",
        baudrate: int = 115200,
        timeout: float = 1.0,
        retries: int = DEFAULT_RETRIES,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = max(0, retries)
        self._sequence_id = 0
        self._connection: serial.Serial | None = None

    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        command = self._OPCODES.get(request.operation)
        if command is None:
            raise ValueError(f"Operation {request.operation.value} is not supported by SerialTransport")

        decoded = self.exchange_command(command, request.board_id)
        if decoded.command != 0x8003:
            raise ValueError(
                f"{request.operation.value} returned unexpected response 0x{decoded.command:04X}"
            )
        return self._to_response(request, decoded)

    def exchange_command(self, command: int, board_id: str | int) -> Frame:
        """Send one V0.1 command and return its reply frame.

        Within one attempt, frames are read until the reply with the request's sequence ID arrives or
        ``timeout`` seconds pass; event frames and stale replies are skipped. If the attempt ends
        without a reply but the board sent other frames, the request was lost and is sent again
        (at most ``retries`` more times). Raises TimeoutError when no reply arrives.
        """
        if serial is None:
            raise RuntimeError("pyserial is required for real serial TRT communication")
        parsed_board_id = self._parse_board_id(str(board_id))
        connection = self._get_connection()
        board_alive = False
        tries = 0
        for _ in range(1 + self.retries):
            tries += 1
            sequence_id = self._next_sequence_id()
            connection.reset_input_buffer()
            connection.write(
                self._encode_frame(board_id=parsed_board_id, sequence_id=sequence_id, command=command)
            )
            connection.flush()
            reply, alive = self._await_reply(connection, sequence_id)
            if reply is not None:
                return reply
            board_alive = board_alive or alive
            if not board_alive:
                break  # nothing on the line: no TRT board here, do not retry
        detail = " (only event frames)" if board_alive else ""
        after = f" after {tries} attempts" if tries > 1 else ""
        raise TimeoutError(f"No TRT response received from {self.port}{after}{detail}")

    def _await_reply(self, connection: Any, sequence_id: int) -> tuple[Frame | None, bool]:
        """Read frames until the reply to ``sequence_id`` or the timeout.

        Returns (reply or None, whether any TRT frame arrived).
        """
        deadline = time.monotonic() + self.timeout
        alive = False
        while time.monotonic() < deadline:
            try:
                raw_frame = self._read_raw_frame(connection)
            except TimeoutError:
                return None, alive
            alive = True
            if raw_frame[3] & self._FLAG_EVENT:
                continue  # heartbeat or other unsolicited event
            decoded = self._decode_frame(raw_frame)
            if decoded.sequence_id != sequence_id:
                continue  # late reply to an earlier request
            return decoded, alive
        return None, alive

    def _read_raw_frame(self, connection: Any) -> bytes:
        """Read one complete TRT frame, resynchronising on the sync word."""
        previous = b""
        for _ in range(self._MAX_FRAME_SIZE):
            byte = connection.read(1)
            if len(byte) < 1:
                raise TimeoutError(f"No complete TRT response received from {self.port}")
            if previous + byte == self._SYNC:
                break
            previous = byte
        else:
            raise ValueError(f"TRT response does not start with sync bytes on {self.port}")

        header = self._SYNC + connection.read(self._HEADER_SIZE - 2)
        if len(header) < self._HEADER_SIZE:
            raise TimeoutError(f"No complete TRT response received from {self.port}")
        if header[2] != self._VERSION:
            raise ValueError(f"Unsupported TRT response version {header[2]} on {self.port}")

        payload_length = struct.unpack(">H", header[10:12])[0]
        if self._HEADER_SIZE + payload_length + self._CRC_SIZE > self._MAX_FRAME_SIZE:
            raise ValueError(f"TRT response exceeds the {self._MAX_FRAME_SIZE}-byte frame limit")
        payload = connection.read(payload_length)
        crc = connection.read(self._CRC_SIZE)
        if len(payload) != payload_length or len(crc) != self._CRC_SIZE:
            raise TimeoutError(f"Incomplete TRT response received from {self.port}")
        return bytes(header + payload + crc)

    def is_available(self) -> bool:
        return serial is not None

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
        self._connection = None

    def _get_connection(self) -> serial.Serial:
        if self._connection is None or not self._connection.is_open:
            self._connection = serial.Serial(
                self.port,
                self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
        return self._connection

    @staticmethod
    def available_ports() -> list[str]:
        if serial is None:
            return []
        return [port.device for port in serial.tools.list_ports.comports()]

    def _next_sequence_id(self) -> int:
        self._sequence_id = (self._sequence_id + 1) & 0xFFFF
        return self._sequence_id

    def _encode_frame(self, board_id: int, sequence_id: int, command: int) -> bytes:
        body = self._SYNC + bytes([self._VERSION, self._FLAGS]) + struct.pack(
            ">HHHH",
            board_id,
            sequence_id,
            command,
            0,
        )
        return body + b"\x00\x00"

    def _decode_frame(self, data: bytes) -> Frame:
        if len(data) < self._HEADER_SIZE + self._CRC_SIZE:
            raise ValueError("TRT response frame is too short")
        if data[:2] != self._SYNC:
            raise ValueError("TRT response does not start with sync bytes")
        if data[2] != self._VERSION:
            raise ValueError(f"Unsupported TRT response version {data[2]}")

        board_id, sequence_id, command, payload_length = struct.unpack(">HHHH", data[4:12])
        if len(data) != self._HEADER_SIZE + payload_length + self._CRC_SIZE:
            raise ValueError("TRT response payload length does not match frame size")
        payload = data[12 : 12 + payload_length]
        return self.Frame(
            board_id=board_id,
            sequence_id=sequence_id,
            command=command,
            payload=payload,
        )

    def _to_response(self, request: ProtocolRequest, frame: Frame) -> ProtocolResponse:
        payload = frame.payload
        board_id = str(frame.board_id)
        if isinstance(request, GetVersionRequest):
            return GetVersionResponse(board_id=board_id, version=self._decode_version(payload), mock=False)
        if isinstance(request, BoardInfoRequest):
            return BoardInfoResponse(board_id=board_id, board_type=self._decode_text(payload), mock=False)
        if isinstance(request, GetCapabilitiesRequest):
            return GetCapabilitiesResponse(board_id=board_id, capabilities=self._decode_capabilities(payload), mock=False)
        if isinstance(request, BuildIdRequest):
            return BuildIdResponse(board_id=board_id, build_id=self._decode_text(payload), mock=False)
        raise ValueError(f"Unsupported serial response for {request.operation.value}")

    def _decode_text(self, payload: bytes) -> str:
        return payload.decode("utf-8", errors="replace").rstrip("\x00")

    def _decode_version(self, payload: bytes) -> str:
        if len(payload) >= 3:
            return f"{payload[0]}.{payload[1]}.{payload[2]}"
        return self._decode_text(payload)

    def _decode_capabilities(self, payload: bytes) -> BoardCapabilitiesPayload:
        decoded_ids = decode_capability_ids(payload)
        capability_ids = set(decoded_ids) if decoded_ids is not None else None
        if capability_ids is not None:
            return BoardCapabilitiesPayload(
                system=0x0001 in capability_ids,
                gpio=0x0002 in capability_ids,
                pwm=0x0003 in capability_ids,
                adc=0x0004 in capability_ids,
                dac=0x0005 in capability_ids,
                spi=0x0006 in capability_ids,
                i2c=0x0007 in capability_ids,
                lcd=0x0008 in capability_ids,
                relay=0x000A in capability_ids,
                led=0x0009 in capability_ids,
            )

        value = int.from_bytes(payload, byteorder="big") if payload else 0
        return BoardCapabilitiesPayload(
            gpio=bool(value & 0x000001),
            pwm=bool(value & 0x000002),
            adc=bool(value & 0x000004),
            dac=bool(value & 0x000008),
            i2c=bool(value & 0x000010),
            spi=bool(value & 0x000020),
            uart=bool(value & 0x000040),
            can=bool(value & 0x000080),
            lcd=bool(value & 0x000100),
            relay=bool(value & 0x000200),
            debug_shell=bool(value & 0x000400),
        )

    def decode_capabilities(self, payload: bytes) -> BoardCapabilitiesPayload:
        """Decode either the V0.1 capability list or the legacy bit mask."""
        return self._decode_capabilities(payload)

    def _parse_board_id(self, board_id: str) -> int:
        try:
            value = int(board_id, 0)
        except ValueError as error:
            raise ValueError(f"Serial TRT board id must be numeric, got {board_id!r}") from error
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"Serial TRT board id out of range: {value}")
        return value
