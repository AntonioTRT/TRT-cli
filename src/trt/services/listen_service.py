"""Passive monitoring of asynchronous TRT messages (heartbeat and future events)."""

from __future__ import annotations

import threading
from collections.abc import Callable

from trt.transport.frame_reader import EVENT_HEARTBEAT, FrameReader, ReceivedFrame
from trt.transport.serial_transport import SerialTransport, serial

BAUDRATE = 115200
_READ_TIMEOUT_S = 0.2


def describe_frame(frame: ReceivedFrame) -> str:
    """Return a one-line description of a received frame."""
    if frame.is_event and frame.command == EVENT_HEARTBEAT:
        return "HEARTBEAT"
    kind = "EVENT" if frame.is_event else "FRAME"
    text = f"{kind} 0x{frame.command:04X}"
    if frame.payload:
        text += f" payload={frame.payload.hex()}"
    return text


class ListenService:
    """Read TRT frames from serial ports without sending anything."""

    def __init__(self, ports: list[str] | None = None, baudrate: int = BAUDRATE) -> None:
        self.ports = ports if ports is not None else SerialTransport.available_ports()
        self.baudrate = baudrate

    def listen(
        self,
        on_frame: Callable[[str, ReceivedFrame], None],
        stop: threading.Event,
        board_id: int | None = None,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> int:
        """Block until ``stop`` is set. Returns how many ports could be opened.

        ``on_frame`` is called from reader threads as ``on_frame(port, frame)``.
        When ``board_id`` is given, frames from other boards are ignored.
        """
        if serial is None:
            raise RuntimeError("pyserial is required to listen to TRT boards")

        opened: list[serial.Serial] = []
        for port in self.ports:
            try:
                opened.append(serial.Serial(port, self.baudrate, timeout=_READ_TIMEOUT_S))
            except (OSError, ValueError) as error:  # port busy / not accessible
                if on_error is not None:
                    on_error(port, error)

        threads = [
            threading.Thread(target=self._read_loop, args=(connection, on_frame, stop, board_id, on_error), daemon=True)
            for connection in opened
        ]
        for thread in threads:
            thread.start()
        try:
            for thread in threads:
                while thread.is_alive() and not stop.is_set():
                    thread.join(timeout=0.2)
        finally:
            stop.set()
            for thread in threads:
                thread.join(timeout=1.0)
            for connection in opened:
                connection.close()
        return len(opened)

    @staticmethod
    def _read_loop(connection, on_frame, stop, board_id, on_error) -> None:
        reader = FrameReader()
        while not stop.is_set():
            try:
                data = connection.read(max(connection.in_waiting, 1))
            except (OSError, serial.SerialException) as error:
                if on_error is not None:
                    on_error(connection.port, error)
                return
            for frame in reader.feed(data):
                if board_id is None or frame.board_id == board_id:
                    on_frame(connection.port, frame)
