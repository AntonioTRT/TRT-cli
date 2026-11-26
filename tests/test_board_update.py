"""HWID query and `trt board update`: firmware/HWID mismatch detection, update and verification."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from trt.cli import app
from trt.commands import build, flash
from trt.services import board_query_service, board_update_service
from trt.services.board_query_service import BoardQueryService, QueryUnsupportedError
from trt.transport.serial_transport import SerialTransport

runner = CliRunner()

DATA = 0x8003
NACK = 0x8002
UNSUPPORTED = b"\x00\x02"
APPS = ("app_0000_idle", "app_0001_blink", "app_0002_analog_family", "app_0004_encoder_family")


def _info(family: bytes) -> bytes:
    fields = {1: b"am-modulation", 2: b"STM32L073RZ", 3: bytes((0, 1, 0)), 4: b"\x01", 6: family}
    return bytes((len(fields),)) + b"".join(bytes((key, len(value))) + value for key, value in fields.items())


class FakeBoard:
    """What the board answers; `flash` changes the installed application like a real reflash."""

    hwid: int | None = 2
    program: str | None = "app_0000_idle"
    family: bytes = b"STM32"
    commands: list[int] = []


class FakeTransport:
    Frame = SerialTransport.Frame

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self.port = port

    def exchange_command(self, command: int, board_id: str | int) -> SerialTransport.Frame:
        FakeBoard.commands.append(command)
        if command == 0x000B:
            reply = (NACK, UNSUPPORTED) if FakeBoard.hwid is None else (DATA, FakeBoard.hwid.to_bytes(2, "big"))
        elif command == 0x000A:
            reply = (NACK, UNSUPPORTED) if FakeBoard.program is None else (DATA, FakeBoard.program.encode())
        elif command == 0x0004:
            reply = (DATA, _info(FakeBoard.family))
        else:
            reply = (NACK, UNSUPPORTED)
        return self.Frame(board_id=201, sequence_id=1, command=reply[0], payload=reply[1])

    def close(self) -> None:
        pass


@pytest.fixture()
def cube_dir(tmp_path: Path) -> Path:
    project = tmp_path / "TRT-stm32" / "am modulation"
    programs = project / "Sources" / "programs"
    programs.mkdir(parents=True)
    (project / "CMakeLists.txt").write_text("project(trt01)\n", encoding="utf-8")
    for name in APPS:
        (programs / f"{name}.c").write_text("", encoding="utf-8")
    return project


@pytest.fixture()
def toolchain(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """Fake build/flash; flashing installs the application on FakeBoard."""
    FakeBoard.hwid, FakeBoard.program, FakeBoard.family, FakeBoard.commands = 2, "app_0000_idle", b"STM32", []
    calls: dict[str, list[str]] = {"build": [], "flash": []}

    def fake_build(cube: Path, program: str) -> Path:
        calls["build"].append(program)
        return cube / "artifacts" / program / f"{program}.elf"

    def fake_flash(elf: Path, name: str) -> None:
        calls["flash"].append(name)
        FakeBoard.program = name

    monkeypatch.setattr(build, "build_stm32_app", fake_build)
    monkeypatch.setattr(flash, "flash_stm32_elf", fake_flash)
    monkeypatch.setattr(board_update_service, "SerialTransport", FakeTransport)
    monkeypatch.setattr(board_query_service, "SerialTransport", FakeTransport)
    resolve = lambda board_id, port=None: (str(int(board_id, 0)), port or "COM9", 115200)  # noqa: E731
    monkeypatch.setattr(board_update_service, "resolve_serial_connection", resolve)
    monkeypatch.setattr(board_query_service, "resolve_serial_connection", resolve)
    return calls


def _update(cube: Path, *args: str):
    return runner.invoke(app, ["board", "update", "201", *args, "--project-dir", str(cube)])


def test_app_hwid_parses_application_names() -> None:
    assert build.app_hwid("app_0002_analog_family") == 2
    assert build.app_hwid("app_0000_idle") == 0
    assert build.app_hwid("program_blink") is None
    assert build.app_hwid("app_2_short") is None


def test_app_for_hwid(cube_dir: Path) -> None:
    assert build.app_for_hwid(cube_dir, 2) == "app_0002_analog_family"
    assert build.app_for_hwid(cube_dir, 3) is None
    (cube_dir / "Sources" / "programs" / "app_0002_other.c").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Several applications claim HWID 2"):
        build.app_for_hwid(cube_dir, 2)


def test_hwid_query(toolchain: dict[str, list[str]]) -> None:
    assert BoardQueryService().query("201", "hwid").value == "2"
    FakeBoard.hwid = None
    with pytest.raises(QueryUnsupportedError):
        BoardQueryService().query("201", "hwid")


def test_update_does_nothing_when_application_matches(cube_dir: Path, toolchain: dict[str, list[str]]) -> None:
    FakeBoard.program = "app_0002_analog_family"
    result = _update(cube_dir)
    assert result.exit_code == 0, result.output
    assert "MATCH" in result.output and "MISMATCH" not in result.output
    assert toolchain == {"build": [], "flash": []}


def test_check_reports_mismatch_without_flashing(cube_dir: Path, toolchain: dict[str, list[str]]) -> None:
    result = _update(cube_dir, "--check")
    assert result.exit_code == 1
    assert "MISMATCH" in result.output
    assert "app_0002_analog_family" in result.output
    assert toolchain == {"build": [], "flash": []}
    assert FakeBoard.program == "app_0000_idle"


def test_update_builds_flashes_and_verifies(cube_dir: Path, toolchain: dict[str, list[str]]) -> None:
    result = _update(cube_dir)
    assert result.exit_code == 0, result.output
    assert toolchain == {"build": ["app_0002_analog_family"], "flash": ["app_0002_analog_family"]}
    assert "Updated and verified" in result.output


def test_update_fails_when_board_does_not_report_new_application(
    cube_dir: Path, toolchain: dict[str, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(flash, "flash_stm32_elf", lambda elf, name: None)  # flash "succeeds", nothing changes
    result = _update(cube_dir)
    assert result.exit_code == 1
    assert "Verification failed" in result.output


def test_update_explains_bootstrap_for_firmware_without_hwid(
    cube_dir: Path, toolchain: dict[str, list[str]]
) -> None:
    FakeBoard.hwid = None
    result = _update(cube_dir)
    assert result.exit_code == 2
    assert "trt build stm32 app_0000_idle" in result.output
    assert toolchain == {"build": [], "flash": []}


def test_update_rejects_hwid_without_application(cube_dir: Path, toolchain: dict[str, list[str]]) -> None:
    FakeBoard.hwid = 3
    result = _update(cube_dir)
    assert result.exit_code == 1
    assert "No application for HWID 3" in result.output
    assert toolchain == {"build": [], "flash": []}


def test_update_rejects_non_stm32_boards(cube_dir: Path, toolchain: dict[str, list[str]]) -> None:
    FakeBoard.family = b"Arduino"
    result = _update(cube_dir)
    assert result.exit_code == 1
    assert "STM32 only" in result.output
