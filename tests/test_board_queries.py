from __future__ import annotations

import pytest
from typer.testing import CliRunner

from trt.cli import app
from trt.protocol.v01 import decode_info_payload
from trt.services import board_query_service
from trt.services.board_query_service import (
    BoardQueryService,
    QueryUnsupportedError,
    format_uptime,
)
from trt.transport.serial_transport import SerialTransport

runner = CliRunner()


def _info(fields: dict[int, bytes]) -> bytes:
    return bytes((len(fields),)) + b"".join(
        bytes((identifier, len(value))) + value for identifier, value in fields.items()
    )


INFO_WITH_FAMILY = _info(
    {1: b"am-modulation", 2: b"STM32L073RZ", 3: bytes((0, 1, 0)), 4: b"\x01", 5: b"am-modulation", 6: b"STM32"}
)
INFO_V01 = _info({1: b"NUCLEO-L073RZ", 2: b"unspecified", 3: bytes((0, 1, 0)), 4: b"\x01", 5: b"NUCLEO-L073RZ"})

DATA = 0x8003
NACK = 0x8002


class FakeTransport:
    Frame = SerialTransport.Frame
    replies: dict[int, tuple[int, bytes]] = {}
    commands: list[int] = []
    closed = False

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self.port = port

    def exchange_command(self, command: int, board_id: str | int) -> SerialTransport.Frame:
        FakeTransport.commands.append(command)
        response, payload = FakeTransport.replies.get(command, (NACK, b"\x00\x02"))
        return self.Frame(board_id=201, sequence_id=1, command=response, payload=payload)

    def close(self) -> None:
        FakeTransport.closed = True


@pytest.fixture(autouse=True)
def fake_board(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeTransport.commands = []
    FakeTransport.closed = False
    FakeTransport.replies = {
        0x0002: (DATA, bytes((0, 1, 0))),
        0x0003: (DATA, b"STM32L073RZ"),
        0x0004: (DATA, INFO_WITH_FAMILY),
        0x0007: (DATA, b"000007"),
        0x0008: (DATA, (93_784_567).to_bytes(4, "big")),
        0x0009: (DATA, b"\x01"),
        0x000A: (DATA, b"program_blink"),
    }
    monkeypatch.setattr(board_query_service, "SerialTransport", FakeTransport)
    monkeypatch.setattr(
        board_query_service,
        "resolve_serial_connection",
        lambda board_id, port=None: (str(int(board_id, 0)), port or "COM8", 115200),
    )


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        ("id", "201"),
        ("name", "am-modulation"),
        ("type", "STM32"),
        ("revision", "STM32L073RZ"),
        ("version", "0.1.0"),
        ("build-id", "000007"),
        ("runtime", "RUNNING"),
        ("active-program", "program_blink"),
        ("uptime", "1d 02:03:04.567 (93784567 ms)"),
    ],
)
def test_query_returns_board_value(item: str, expected: str) -> None:
    result = BoardQueryService().query("201", item, port="COM8")
    assert result.value == expected
    assert result.board_id == "201"
    assert FakeTransport.closed


def test_transport_query_asks_nothing_of_the_firmware() -> None:
    result = BoardQueryService().query("201", "transport", port="COM8")
    assert result.value == "serial (COM8, 115200 baud)"
    assert FakeTransport.commands == []


def test_nack_is_reported_as_unsupported() -> None:
    FakeTransport.replies.pop(0x000A)
    with pytest.raises(QueryUnsupportedError):
        BoardQueryService().query("201", "active-program", port="COM8")
    assert FakeTransport.closed


def test_info_without_family_field_is_unsupported() -> None:
    FakeTransport.replies[0x0004] = (DATA, INFO_V01)
    with pytest.raises(QueryUnsupportedError):
        BoardQueryService().query("2", "type", port="COM8")
    # the name still comes from the V0.1 INFO fields
    assert BoardQueryService().query("2", "name", port="COM8").value == "NUCLEO-L073RZ"


def test_unknown_query_is_rejected() -> None:
    with pytest.raises(ValueError):
        BoardQueryService().query("201", "gpio", port="COM8")


def test_info_family_field_is_decoded() -> None:
    assert decode_info_payload(INFO_WITH_FAMILY)["family"] == "STM32"
    assert "family" not in decode_info_payload(INFO_V01)


def test_format_uptime() -> None:
    assert format_uptime(0) == "00:00:00.000 (0 ms)"
    assert format_uptime(3_661_001) == "01:01:01.001 (3661001 ms)"


def test_cli_prints_value() -> None:
    result = runner.invoke(app, ["board", "uptime", "201", "--port", "COM8"])
    assert result.exit_code == 0, result.output
    assert "uptime" in result.output
    assert "93784567 ms" in result.output


def test_cli_unsupported_exits_with_code_2() -> None:
    FakeTransport.replies.pop(0x0008)
    result = runner.invoke(app, ["board", "uptime", "201", "--port", "COM8"])
    assert result.exit_code == 2
    assert "unsupported" in result.output


def test_cli_registers_every_query() -> None:
    result = runner.invoke(app, ["board", "--help"])
    for item in board_query_service.ITEMS:
        assert item in result.output
