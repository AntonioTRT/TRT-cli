"""Request/response synchronisation of SerialTransport: heartbeat collisions, stale replies, retries."""

from __future__ import annotations

import struct
from collections.abc import Callable
from types import SimpleNamespace

import pytest

import trt.transport.serial_transport as serial_transport_module
from trt.transport.serial_transport import SerialTransport


def _frame(board_id: int, seq: int, command: int, flags: int = 0, payload: bytes = b"") -> bytes:
    return (
        b"\xaa\x55\x01" + bytes([flags])
        + struct.pack(">HHHH", board_id, seq, command, len(payload))
        + payload + b"\x00\x00"
    )


HEARTBEAT = _frame(201, 7, 0x9001, flags=0x02)


class ScriptedConnection:
    """Serial port double: each write() queues the bytes the board sends back for that request."""

    is_open = True

    def __init__(self, script: Callable[[int, int], bytes]) -> None:
        self.script = script  # (write number, request sequence ID) -> bytes on the line
        self.pending = b""
        self.writes: list[int] = []

    def reset_input_buffer(self) -> None:
        self.pending = b""

    def write(self, request: bytes) -> None:
        sequence_id = struct.unpack(">H", request[6:8])[0]
        self.writes.append(sequence_id)
        self.pending += self.script(len(self.writes), sequence_id)

    def flush(self) -> None:
        return None

    def read(self, length: int) -> bytes:  # empty result = serial read timeout
        result, self.pending = self.pending[:length], self.pending[length:]
        return result

    def close(self) -> None:
        self.is_open = False


def _transport(monkeypatch: pytest.MonkeyPatch, script: Callable[[int, int], bytes], **kwargs) -> tuple[SerialTransport, ScriptedConnection]:
    connection = ScriptedConnection(script)
    fake_serial = SimpleNamespace(
        EIGHTBITS=8, PARITY_NONE="N", STOPBITS_ONE=1, Serial=lambda *a, **k: connection
    )
    monkeypatch.setattr(serial_transport_module, "serial", fake_serial)
    return SerialTransport(port="COM9", **kwargs), connection


def test_heartbeat_before_reply_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    transport, connection = _transport(
        monkeypatch, lambda n, seq: HEARTBEAT + _frame(201, seq, 0x8003, payload=b"\x00\x02")
    )
    reply = transport.exchange_command(0x000B, "201")
    assert reply.payload == b"\x00\x02"
    assert len(connection.writes) == 1


def test_request_lost_to_heartbeat_is_resent(monkeypatch: pytest.MonkeyPatch) -> None:
    # First request collides with a heartbeat and is dropped by the board; the resend is answered.
    def board(n: int, seq: int) -> bytes:
        return HEARTBEAT if n == 1 else _frame(201, seq, 0x8003, payload=b"\x00\x02")

    transport, connection = _transport(monkeypatch, board)
    reply = transport.exchange_command(0x000B, "201")
    assert reply.command == 0x8003
    assert len(connection.writes) == 2
    assert connection.writes[0] != connection.writes[1]  # each attempt has its own sequence ID


def test_stale_reply_from_earlier_request_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    transport, connection = _transport(
        monkeypatch,
        lambda n, seq: _frame(201, seq - 1, 0x8003, payload=b"old") + _frame(201, seq, 0x8003, payload=b"new"),
    )
    assert transport.exchange_command(0x000A, "201").payload == b"new"
    assert len(connection.writes) == 1


def test_silent_port_fails_fast_without_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    transport, connection = _transport(monkeypatch, lambda n, seq: b"")
    with pytest.raises(TimeoutError, match="No TRT response received from COM9$"):
        transport.exchange_command(0x0001, "201")
    assert len(connection.writes) == 1  # discovery stays fast on ports without a TRT board


def test_retries_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    transport, connection = _transport(monkeypatch, lambda n, seq: HEARTBEAT)
    with pytest.raises(TimeoutError, match="after 3 attempts .only event frames."):
        transport.exchange_command(0x000B, "201")
    assert len(connection.writes) == 1 + SerialTransport.DEFAULT_RETRIES


def test_retry_count_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    transport, connection = _transport(monkeypatch, lambda n, seq: HEARTBEAT, retries=0)
    with pytest.raises(TimeoutError, match="only event frames"):
        transport.exchange_command(0x000B, "201")
    assert len(connection.writes) == 1


def test_attempt_window_is_time_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    # A board that streams events forever must not keep one attempt open past the timeout.
    clock = iter(x * 0.4 for x in range(100))
    monkeypatch.setattr(serial_transport_module.time, "monotonic", lambda: next(clock))
    transport, connection = _transport(monkeypatch, lambda n, seq: HEARTBEAT * 50, retries=1)
    with pytest.raises(TimeoutError):
        transport.exchange_command(0x000B, "201")
    assert len(connection.writes) == 2


def test_reply_to_each_attempt_is_matched_by_sequence_id(monkeypatch: pytest.MonkeyPatch) -> None:
    # The board answers the first (lost) request late, during the second attempt: that late reply
    # must not be taken for the second request's reply.
    sequences: list[int] = []

    def board(n: int, seq: int) -> bytes:
        sequences.append(seq)
        if n == 1:
            return HEARTBEAT
        return _frame(201, sequences[0], 0x8003, payload=b"late") + _frame(201, seq, 0x8003, payload=b"ok")

    transport, _ = _transport(monkeypatch, board)
    assert transport.exchange_command(0x000B, "201").payload == b"ok"
