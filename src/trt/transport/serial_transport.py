"""Serial transport for minimal real TRT firmware transactions."""

from __future__ import annotations

import struct
import time

from trt.protocol.models import (
    BoardInfoRequest,
    BoardInfoResponse,
    BuildIdRequest,
    BuildIdResponse,
    GetVersionRequest,
    GetVersionResponse,
    GetCapabilitiesRequest,
    GetCapabilitiesResponse,
    BoardCapabilitiesPayload,
    ProtocolOperation,
    ProtocolRequest,
    ProtocolResponse,
)
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

    _OPCODES: dict[ProtocolOperation, int] = {
        ProtocolOperation.GET_VERSION: 0x0002,
        ProtocolOperation.BOARD_INFO: 0x0003,
        ProtocolOperation.GET_CAPABILITIES: 0x0006,
        ProtocolOperation.BUILD_ID: 0x0007,
    }

    def __init__(self, port: str = "COM4", baudrate: int = 115200, timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._sequence_id = 0
        self._connection = None

    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        if serial is None:
            raise RuntimeError("pyserial is required for real serial TRT communication")

        command = self._OPCODES.get(request.operation)
        if command is None:
            raise ValueError(f"Operation {request.operation.value} is not supported by SerialTransport")

        board_id = self._parse_board_id(request.board_id)
        sequence_id = self._next_sequence_id()
        frame = self._encode_frame(board_id=board_id, sequence_id=sequence_id, command=command)

        connection = self._get_connection()
        connection.reset_input_buffer()
        connection.write(frame)
        connection.flush()
        response_frame = connection.read(self._HEADER_SIZE)
        if len(response_frame) < self._HEADER_SIZE:
            raise TimeoutError(f"No complete TRT response received from {self.port}")

        payload_length = struct.unpack(">H", response_frame[10:12])[0]
        payload = connection.read(payload_length)
        crc = connection.read(self._CRC_SIZE)
        if len(payload) != payload_length or len(crc) != self._CRC_SIZE:
            raise TimeoutError(f"Incomplete TRT response received from {self.port}")

        decoded = self._decode_frame(response_frame + payload + crc)
        return self._to_response(request, decoded)

    def is_available(self) -> bool:
        return serial is not None

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
        self._connection = None

    def _get_connection(self):
        if self._connection is None or not self._connection.is_open:
            self._connection = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            time.sleep(2.0)
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
        return body + struct.pack(">H", self._crc16_ccitt(body))

    def _decode_frame(self, data: bytes) -> dict[str, bytes | int]:
        if len(data) < self._HEADER_SIZE + self._CRC_SIZE:
            raise ValueError("TRT response frame is too short")
        if data[:2] != self._SYNC:
            raise ValueError("TRT response does not start with sync bytes")

        board_id, sequence_id, command, payload_length = struct.unpack(">HHHH", data[4:12])
        payload = data[12 : 12 + payload_length]
        return {
            "version": data[2],
            "flags": data[3],
            "board_id": board_id,
            "sequence_id": sequence_id,
            "command": command,
            "payload": payload,
        }

    def _to_response(self, request: ProtocolRequest, frame: dict[str, bytes | int]) -> ProtocolResponse:
        payload = frame["payload"]
        if not isinstance(payload, bytes):
            raise ValueError("Decoded TRT payload is invalid")

        board_id = str(frame["board_id"])
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

    def _parse_board_id(self, board_id: str) -> int:
        try:
            value = int(board_id, 0)
        except ValueError as error:
            raise ValueError(f"Serial TRT board id must be numeric, got {board_id!r}") from error
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"Serial TRT board id out of range: {value}")
        return value

    def _crc16_ccitt(self, data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc
