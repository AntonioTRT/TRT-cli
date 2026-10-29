from __future__ import annotations

import json
import struct
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

import trt.transport.serial_transport as serial_transport_module
from trt.cli import app
from trt.commands import build, flash, stm32
from trt.repositories import board_cache
from trt.services import board_discovery_service
from trt.transport.serial_transport import SerialTransport

runner = CliRunner()


def _info_payload() -> bytes:
    fields = [
        (0x01, b"NUCLEO-L073RZ"),
        (0x02, b"unspecified"),
        (0x03, bytes((0, 1, 0))),
        (0x04, bytes((1,))),
        (0x05, b"NUCLEO-L073RZ"),
    ]
    return bytes((len(fields),)) + b"".join(
        bytes((identifier, len(value))) + value for identifier, value in fields
    )


class FakeSerialTransport:
    Frame = SerialTransport.Frame

    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.commands: list[int] = []
        self.closed = False

    @staticmethod
    def available_ports() -> list[str]:
        return ["COM8"]

    def exchange_command(self, command: int, board_id: str) -> SerialTransport.Frame:
        self.commands.append(command)
        payloads = {
            0x0001: b"",
            0x0002: bytes((0, 1, 0)),
            0x0003: b"unspecified",
            0x0004: _info_payload(),
            0x0005: b"\x01",
            0x0006: bytes((4, 0, 1, 0, 2, 0, 5, 0, 9)),
        }
        response_id = 0x8001 if command == 0x0001 else 0x8003
        return self.Frame(
            board_id=int(board_id, 0),
            sequence_id=len(self.commands),
            command=response_id,
            payload=payloads[command],
        )

    def close(self) -> None:
        self.closed = True


class FakeStm32Transport:
    Frame = SerialTransport.Frame
    requested_baudrates: list[int] = []
    commands: list[int] = []

    def __init__(self, port: str, baudrate: int, timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.closed = False
        self.requested_baudrates.append(baudrate)

    @staticmethod
    def available_ports() -> list[str]:
        return ["COM7"]

    def exchange_command(self, command: int, board_id: str) -> SerialTransport.Frame:
        self.commands.append(command)
        responses = {
            0x0001: (0x8001, b""),
            0x0002: (0x8003, bytes((0, 1, 0))),
            0x0003: (0x8003, b"unspecified"),
            0x0004: (0x8003, _info_payload()),
            0x0006: (0x8003, bytes((4, 0, 1, 0, 2, 0, 5, 0, 9))),
            0x0007: (0x8003, b"000123"),
        }
        response_id, payload = responses[command]
        return self.Frame(
            board_id=int(board_id, 0),
            sequence_id=len(self.commands),
            command=response_id,
            payload=payload,
        )

    def decode_capabilities(self, payload: bytes):
        return SerialTransport(port=self.port).decode_capabilities(payload)

    def close(self) -> None:
        self.closed = True


def test_v01_frame_uses_zero_crc_and_big_endian_fields() -> None:
    transport = SerialTransport(port="COM1")
    frame = transport._encode_frame(board_id=2, sequence_id=1, command=1)
    assert frame == bytes.fromhex("AA55010000020001000100000000")
    assert struct.unpack(">HHHH", frame[4:12]) == (2, 1, 1, 0)


def test_v01_frame_decoder_rejects_mismatched_length() -> None:
    transport = SerialTransport(port="COM1")
    with pytest.raises(ValueError, match="payload length"):
        transport._decode_frame(bytes.fromhex("AA55010000020001000100010000"))


def test_serial_transport_sends_and_receives_v01_ack(monkeypatch: pytest.MonkeyPatch) -> None:
    class SimulatedConnection:
        is_open = True

        def __init__(self) -> None:
            self.pending = b""
            self.request = b""

        def reset_input_buffer(self) -> None:
            self.pending = b""

        def write(self, request: bytes) -> None:
            self.request = request
            board_id, sequence_id, command, _ = struct.unpack(">HHHH", request[4:12])
            assert command == 0x0001
            self.pending = (
                b"\xaa\x55\x01\x00"
                + struct.pack(">HHHH", board_id, sequence_id, 0x8001, 0)
                + b"\x00\x00"
            )

        def flush(self) -> None:
            return None

        def read(self, length: int) -> bytes:
            result, self.pending = self.pending[:length], self.pending[length:]
            return result

    connection = SimulatedConnection()
    serial_arguments: dict[str, object] = {}

    def open_serial(*args: object, **kwargs: object) -> SimulatedConnection:
        serial_arguments.update(kwargs)
        return connection

    fake_serial = SimpleNamespace(
        EIGHTBITS=8,
        PARITY_NONE="N",
        STOPBITS_ONE=1,
        Serial=open_serial,
    )
    monkeypatch.setattr(serial_transport_module, "serial", fake_serial)

    response = SerialTransport(port="COM1").exchange_command(0x0001, "0x0002")

    assert response.command == 0x8001
    assert response.payload == b""
    assert connection.request == bytes.fromhex("AA55010000020001000100000000")
    assert serial_arguments == {
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "timeout": 1.0,
        "write_timeout": 1.0,
    }


def test_capability_decoder_accepts_v01_identifier_list() -> None:
    capabilities = SerialTransport(port="COM1")._decode_capabilities(
        bytes((4, 0, 1, 0, 2, 0, 5, 0, 9))
    )
    assert capabilities.system is True
    assert capabilities.gpio is True
    assert capabilities.dac is True
    assert capabilities.led is True
    assert capabilities.pwm is False


def test_stm32_test_scans_ports_and_checks_all_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stm32, "SerialTransport", FakeSerialTransport)
    result = runner.invoke(app, ["stm32", "test"])
    assert result.exit_code == 0, result.stdout
    assert "COM8" in result.stdout
    assert "ACK (0x8001)" in result.stdout
    assert "NUCLEO-L073RZ" in result.stdout
    assert "SYSTEM, GPIO, DAC, LED" in result.stdout


def test_stm32_test_fails_on_unexpected_ping_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class BadPingTransport(FakeSerialTransport):
        def exchange_command(self, command: int, board_id: str) -> SerialTransport.Frame:
            response = super().exchange_command(command, board_id)
            if command == 1:
                return self.Frame(response.board_id, response.sequence_id, 0x8003, b"PONG")
            return response

    monkeypatch.setattr(stm32, "SerialTransport", BadPingTransport)
    result = runner.invoke(app, ["stm32", "test", "--port", "COM8"])
    assert result.exit_code == 1
    assert "expected 0x8001" in result.stdout


def test_flash_stm32_invokes_platformio_upload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_dir = tmp_path / "TRT-stm32"
    project_dir.mkdir()
    (project_dir / "platformio.ini").write_text("[platformio]\n", encoding="utf-8")
    called: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> SimpleNamespace:
        called.append(command)
        assert check is False
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(flash.subprocess, "run", fake_run)
    result = runner.invoke(
        app,
        ["flash", "stm32", "--platformio", "--project-dir", str(project_dir), "--port", "COM8"],
    )
    assert result.exit_code == 0, result.stdout
    assert called[0][-5:] == [
        str(project_dir.resolve()),
        "-t",
        "upload",
        "--upload-port",
        "COM8",
    ]


def test_flash_stm32_propagates_platformio_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_dir = tmp_path / "TRT-stm32"
    project_dir.mkdir()
    (project_dir / "platformio.ini").write_text("[platformio]\n", encoding="utf-8")
    monkeypatch.setattr(
        flash.subprocess,
        "run",
        lambda command, check: SimpleNamespace(returncode=2),
    )
    result = runner.invoke(app, ["flash", "stm32", "--platformio", "--project-dir", str(project_dir)])
    assert result.exit_code == 2
    assert "upload failed" in result.stdout


def _cubeide_project(tmp_path: Path) -> Path:
    cube_dir = tmp_path / "TRT-stm32" / "am modulation"
    programs = cube_dir / "Sources" / "programs"
    programs.mkdir(parents=True)
    (cube_dir / "CMakeLists.txt").write_text("project(trt01)\n", encoding="utf-8")
    for name in ("program_blink", "program_pulse_train"):
        (programs / f"{name}.c").write_text("", encoding="utf-8")
    return cube_dir


def _fake_toolchain(monkeypatch: pytest.MonkeyPatch, tools: set[str]) -> list[list[str]]:
    called: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> SimpleNamespace:
        called.append(command)
        if command[:2] == ["cmake", "--build"]:
            Path(command[2]).mkdir(parents=True, exist_ok=True)
            (Path(command[2]) / "trt01.elf").write_text("elf:" + Path(command[2]).name, encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(build.subprocess, "run", fake_run)
    monkeypatch.setattr(flash.subprocess, "run", fake_run)
    monkeypatch.setattr(build.shutil, "which", lambda tool: tool if tool in tools else None)
    monkeypatch.setattr(flash.shutil, "which", lambda tool: tool if tool in tools else None)
    return called


def _build(program: str, tmp_path: Path):
    return runner.invoke(app, ["build", "stm32", program, "--project-dir", str(tmp_path / "TRT-stm32")])


def _flash(tmp_path: Path, *args: str):
    return runner.invoke(app, ["flash", "stm32", *args, "--project-dir", str(tmp_path / "TRT-stm32")])


def test_build_stores_artifact_and_does_not_flash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cube_dir = _cubeide_project(tmp_path)
    called = _fake_toolchain(
        monkeypatch, {"cmake", "arm-none-eabi-gcc", "ninja", "STM32_Programmer_CLI"}
    )
    result = _build("program_pulse_train", tmp_path)
    assert result.exit_code == 0, result.stdout
    configure, build_cmd = called
    assert "-DACTIVE_PROGRAM=PROGRAM_PULSE_TRAIN" in configure
    assert configure[1:3] == ["-G", "Ninja"]
    assert build_cmd[:2] == ["cmake", "--build"]
    assert all("STM32_Programmer_CLI" not in command[0] for command in called)
    stored = cube_dir / "artifacts" / "program_pulse_train" / "program_pulse_train.elf"
    assert stored.read_text(encoding="utf-8") == "elf:program_pulse_train"
    manifest = json.loads((cube_dir / "artifacts" / "latest.json").read_text(encoding="utf-8"))
    assert manifest["program"] == "program_pulse_train"


def test_build_rejects_unknown_program(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _cubeide_project(tmp_path)
    called = _fake_toolchain(monkeypatch, {"cmake", "arm-none-eabi-gcc"})
    result = _build("program_nope", tmp_path)
    assert result.exit_code != 0
    assert "program_blink" in result.output
    assert called == []


def test_build_reports_missing_toolchain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _cubeide_project(tmp_path)
    called = _fake_toolchain(monkeypatch, set())
    result = _build("program_blink", tmp_path)
    assert result.exit_code == 1
    assert "Missing build tools" in result.stdout
    assert called == []


def test_flash_defaults_to_most_recent_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cube_dir = _cubeide_project(tmp_path)
    called = _fake_toolchain(
        monkeypatch, {"cmake", "arm-none-eabi-gcc", "STM32_Programmer_CLI"}
    )
    assert _build("program_blink", tmp_path).exit_code == 0
    assert _build("program_pulse_train", tmp_path).exit_code == 0
    called.clear()
    result = _flash(tmp_path)
    assert result.exit_code == 0, result.stdout
    assert len(called) == 1
    assert called[0][0] == "STM32_Programmer_CLI"
    assert str(cube_dir / "artifacts" / "program_pulse_train" / "program_pulse_train.elf") in called[0]


def test_flash_named_program_uses_that_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cube_dir = _cubeide_project(tmp_path)
    called = _fake_toolchain(
        monkeypatch, {"cmake", "arm-none-eabi-gcc", "STM32_Programmer_CLI"}
    )
    assert _build("program_blink", tmp_path).exit_code == 0
    assert _build("program_pulse_train", tmp_path).exit_code == 0
    called.clear()
    result = _flash(tmp_path, "program_blink")
    assert result.exit_code == 0, result.stdout
    assert str(cube_dir / "artifacts" / "program_blink" / "program_blink.elf") in called[0]


def test_flash_without_any_build_points_to_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _cubeide_project(tmp_path)
    called = _fake_toolchain(monkeypatch, {"STM32_Programmer_CLI"})
    result = _flash(tmp_path)
    assert result.exit_code == 1
    assert "trt build stm32" in result.stdout
    assert called == []


def test_flash_unbuilt_program_does_not_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _cubeide_project(tmp_path)
    called = _fake_toolchain(monkeypatch, {"cmake", "arm-none-eabi-gcc", "STM32_Programmer_CLI"})
    result = _flash(tmp_path, "program_blink")
    assert result.exit_code == 1
    assert "trt build stm32 program_blink" in result.stdout
    assert called == []


def test_flash_requires_programmer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _cubeide_project(tmp_path)
    _fake_toolchain(monkeypatch, {"cmake", "arm-none-eabi-gcc"})
    assert _build("program_blink", tmp_path).exit_code == 0
    result = _flash(tmp_path)
    assert result.exit_code == 1
    assert "STM32_Programmer_CLI not found" in result.stdout


def test_discovery_handshakes_and_persists_stm32_port(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    FakeStm32Transport.commands = []
    FakeStm32Transport.requested_baudrates = []
    cache = tmp_path / "boards.json"
    monkeypatch.setattr(board_cache, "cache_path", lambda: cache)
    monkeypatch.setattr(board_discovery_service, "SerialTransport", FakeStm32Transport)

    service = board_discovery_service.BoardDiscoveryService()
    discovered = service.discover_serial()

    assert len(discovered) == 1
    board = discovered[0]
    assert board.identity.board_id == "2"
    assert board.metadata["board_type"] == "NUCLEO-L073RZ"
    assert board.transport is not None
    assert board.transport.port == "COM7"
    assert board.transport.baudrate == 115200
    assert FakeStm32Transport.commands == [1, 3, 4, 6, 2, 7]
    assert FakeStm32Transport.requested_baudrates == [115200]
    assert board_cache.load_serial_connections() == {
        "2": {"port": "COM7", "baudrate": 115200}
    }


def test_board_info_resolves_cached_stm32_port_and_shows_v01_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    FakeStm32Transport.commands = []
    FakeStm32Transport.requested_baudrates = []
    cache = tmp_path / "boards.json"
    cache.write_text(
        '{"boards":{"2":{"port":"COM7","baudrate":115200}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(board_cache, "cache_path", lambda: cache)
    monkeypatch.setattr(serial_transport_module, "SerialTransport", FakeStm32Transport)

    result = runner.invoke(app, ["board", "info", "2"])

    assert result.exit_code == 0, result.stdout
    assert "NUCLEO-L073RZ" in result.stdout
    assert "BOARD_VERSION" in result.stdout
    assert "CAPABILITIES" in result.stdout
    assert "SYSTEM, GPIO, DAC, LED" in result.stdout
    assert FakeStm32Transport.commands == [1, 3, 4, 6, 2, 7]
    assert FakeStm32Transport.requested_baudrates == [115200]


def test_list_programs_discovers_every_program_file(tmp_path: Path) -> None:
    cube_dir = _cubeide_project(tmp_path)
    (cube_dir / "Sources" / "programs" / "program_encoder.c").write_text("", encoding="utf-8")
    (cube_dir / "Sources" / "programs" / "helper.c").write_text("", encoding="utf-8")
    (cube_dir / "Sources" / "programs" / "program_notes.txt").write_text("", encoding="utf-8")
    result = runner.invoke(
        app, ["list-programs", "stm32", "--project-dir", str(tmp_path / "TRT-stm32")]
    )
    assert result.exit_code == 0, result.output
    assert result.stdout.split() == ["program_blink", "program_encoder", "program_pulse_train"]


def test_list_programs_fails_when_no_programs(tmp_path: Path) -> None:
    cube_dir = _cubeide_project(tmp_path)
    for source in (cube_dir / "Sources" / "programs").glob("*.c"):
        source.unlink()
    result = runner.invoke(
        app, ["list-programs", "stm32", "--project-dir", str(tmp_path / "TRT-stm32")]
    )
    assert result.exit_code == 1
    assert "No STM32 programs found" in result.output


def test_list_programs_does_not_run_build_tools(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _cubeide_project(tmp_path)
    called = _fake_toolchain(monkeypatch, {"cmake", "arm-none-eabi-gcc"})
    result = runner.invoke(
        app, ["list-programs", "stm32", "--project-dir", str(tmp_path / "TRT-stm32")]
    )
    assert result.exit_code == 0
    assert called == []
    assert not (tmp_path / "TRT-stm32" / "am modulation" / "artifacts").exists()
