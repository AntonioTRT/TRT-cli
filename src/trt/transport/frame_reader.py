"""Incremental reader for TRT frames arriving on a byte stream."""

from __future__ import annotations

import struct
from dataclasses import dataclass

SYNC = b"\xaa\x55"
VERSION = 1
HEADER_SIZE = 12
CRC_SIZE = 2
MAX_FRAME_SIZE = 256

FLAG_EVENT = 0x02
EVENT_HEARTBEAT = 0x9001


@dataclass(frozen=True)
class ReceivedFrame:
    """A decoded TRT frame (any direction), including its FLAGS byte."""

    board_id: int
    sequence_id: int
    command: int
    flags: int
    payload: bytes

    @property
    def is_event(self) -> bool:
        return bool(self.flags & FLAG_EVENT)


class FrameReader:
    """Resynchronising TRT frame parser.

    Feed it raw bytes in any chunking; it returns the complete frames found and
    silently skips noise (for example boot messages) before the sync word.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[ReceivedFrame]:
        self._buffer.extend(data)
        frames: list[ReceivedFrame] = []
        while True:
            start = self._buffer.find(SYNC)
            if start < 0:
                # Keep a trailing 0xAA: it may be the first half of a sync word.
                del self._buffer[: max(len(self._buffer) - 1, 0)]
                break
            del self._buffer[:start]
            if len(self._buffer) < HEADER_SIZE:
                break
            payload_length = struct.unpack(">H", self._buffer[10:12])[0]
            total = HEADER_SIZE + payload_length + CRC_SIZE
            if self._buffer[2] != VERSION or total > MAX_FRAME_SIZE:
                del self._buffer[:1]  # false sync: skip one byte and look again
                continue
            if len(self._buffer) < total:
                break
            board_id, sequence_id, command = struct.unpack(">HHH", self._buffer[4:10])
            frames.append(
                ReceivedFrame(
                    board_id=board_id,
                    sequence_id=sequence_id,
                    command=command,
                    flags=self._buffer[3],
                    payload=bytes(self._buffer[HEADER_SIZE : HEADER_SIZE + payload_length]),
                )
            )
            del self._buffer[:total]
        return frames
