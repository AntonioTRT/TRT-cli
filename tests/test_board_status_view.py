"""`trt boards`, `trt discover` and `trt board info` show the same HWID / application status."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import trt.transport.serial_transport as serial_transport_module
from trt.cli import app
from trt.core.modes import HwidMatch, mode_id, format_hwid, hwid_match
from trt.repositories import board_cache
from trt.services import board_discovery_service
from trt.services.board_summary import BoardSummary
from trt.transport.serial_transport import SerialTransport

runner = CliRunner(env={"COLUMNS": "120"})

DATA, ACK, NACK = 0x8003, 0x8001, 0x8002


def _info() -> bytes:
    fields = {1: b"am-modulation", 2: b"STM32L073RZ", 3: bytes((0, 1, 0)), 4: b"\x01", 5: b"am-modulation", 6: b"STM32"}
    return bytes((len(fields),)) + b"".join(bytes((key, len(value))) + value for key, value in fields.items())


class FakeBoard:
    hwid: int | None = 2
    program: str | None = "mode_0002_analog"


class FakeTransport:
    Frame = SerialTransport.Frame

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self.port = port

    @staticmethod
    def available_ports() -> list[str]:
        return ["COM9"]

    def exchange_command(self, command: int, board_id: str | int) -> SerialTransport.Frame:
        replies = {
            0x0001: (ACK, b""),
            0x0002: (DATA, bytes((0, 1, 0))),
            0x0003: (DATA, b"STM32L073RZ"),
            0x0004: (DATA, _info()),
            0x0006: (DATA, bytes((1, 0, 1))),
            0x0007: (DATA, b"000001"),
        }
        if FakeBoard.hwid is not None:
            replies[0x000B] = (DATA, FakeBoard.hwid.to_bytes(2, "big"))
        if FakeBoard.program is not None:
            replies[0x000A] = (DATA, FakeBoard.program.encode())
        response, payload = replies.get(command, (NACK, b"\x00\x02"))
        return self.Frame(board_id=201, sequence_id=1, command=response, payload=payload)

    def decode_capabilities(self, payload: bytes):
        return SerialTransport(port=self.port).decode_capabilities(payload)

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def fake_board(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    FakeBoard.hwid, FakeBoard.program = 2, "mode_0002_analog"
    monkeypatch.setattr(board_cache, "cache_path", lambda: tmp_path / "boards.json")
    monkeypatch.setattr(board_discovery_service, "SerialTransport", FakeTransport)
    monkeypatch.setattr(serial_transport_module, "SerialTransport", FakeTransport)


def _summary(hwid: int | None, program: str | None) -> BoardSummary:
    return BoardSummary("201", "am-modulation", "STM32", "0.1.0", "000001", program, hwid)


def test_hwid_formatting_and_match_rules() -> None:
    assert format_hwid(2) == "0010"
    assert format_hwid(0) == "0000"
    assert format_hwid(None) == "----"
    assert mode_id("mode_0002_analog") == 2
    assert hwid_match(2, 2) is HwidMatch.MATCH
    assert hwid_match(2, 0) is HwidMatch.MISMATCH
    assert hwid_match(None, 2) is HwidMatch.NO_HWID
    assert hwid_match(2, None) is HwidMatch.NO_MODE
    assert _summary(2, "mode_0000_base").hwid_expected == 0
    assert _summary(2, "program_blink").match is HwidMatch.NO_MODE


@pytest.mark.parametrize("command", [["boards"], ["discover"], ["board", "info", "201"]])
def test_match_is_shown_identically(command: list[str]) -> None:
    result = runner.invoke(app, command)
    assert result.exit_code == 0, result.output
    assert "mode_0002_analog" in result.output
    assert "0010 / 0010" in result.output
    assert "MATCH" in result.output and "MISMATCH" not in result.output
    assert "trt board update" not in result.output


@pytest.mark.parametrize("command", [["boards"], ["discover"], ["board", "info", "201"]])
def test_mismatch_is_shown_identically_with_next_step(command: list[str]) -> None:
    FakeBoard.program = "mode_0000_base"
    result = runner.invoke(app, command)
    assert result.exit_code == 0, result.output
    assert "mode_0000_base" in result.output
    assert "0010 / 0000" in result.output
    assert "MISMATCH" in result.output
    assert "trt board update 201" in result.output


def test_board_info_shows_decimal_values_and_details() -> None:
    result = runner.invoke(app, ["board", "info", "201"])
    assert "read 2 / expected 2" in result.output
    assert "Revision" in result.output and "STM32L073RZ" in result.output
    assert "Capabilities" in result.output


def test_firmware_without_hwid_is_flagged() -> None:
    FakeBoard.hwid, FakeBoard.program = None, None
    result = runner.invoke(app, ["boards"])
    assert result.exit_code == 0, result.output
    assert "---- / ----" in result.output
    assert "NO HWID" in result.output
    assert "trt board update 201" in result.output
