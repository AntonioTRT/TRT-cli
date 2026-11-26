"""Console safety: TRT output must work on consoles that cannot print Unicode.

Windows consoles often use cp1252 (or an OEM code page); Linux in the C locale uses ASCII. Printing a
character the console cannot encode raises UnicodeEncodeError and the command crashes (this happened
with `trt update`). Two layers of protection:

1. No string literal in the CLI source contains non-ASCII characters (docstrings and comments are
   exempt: they are never printed).
2. The real help and status screens run in a subprocess whose stdout is cp1252 or ASCII, so Rich's own
   rendering (tables, panels, box characters) is exercised too.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "trt"


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def test_no_non_ascii_string_literals_in_cli_source() -> None:
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                if not node.value.isascii():
                    bad = "".join(sorted({c for c in node.value if not c.isascii()}))
                    offenders.append(f"{path.relative_to(SRC)}:{node.lineno}: {bad!r}")
    assert not offenders, "Non-ASCII characters in output strings:\n" + "\n".join(offenders)


def _run(args: list[str], encoding: str, script: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": encoding, "COLUMNS": "80", "TERM": "dumb"}
    env.pop("FORCE_COLOR", None)
    command = [sys.executable, "-c", script] if script else [sys.executable, "-m", "trt", *args]
    return subprocess.run(command, capture_output=True, text=True, encoding=encoding, errors="replace", env=env, timeout=60)


HELP_SCREENS = [
    [],
    ["--help"],
    ["help"],
    ["version"],
    ["board", "--help"],
    ["board", "update", "--help"],
    ["list-modes", "--help"],
    ["build", "stm32", "--help"],
    ["flash", "stm32", "--help"],
    ["stm32", "test", "--help"],
    ["update"],
]


@pytest.mark.parametrize("encoding", ["cp1252", "ascii"])
@pytest.mark.parametrize("args", HELP_SCREENS, ids=lambda a: " ".join(a) or "trt")
def test_help_screens_on_legacy_consoles(args: list[str], encoding: str) -> None:
    result = _run(args, encoding)
    assert "UnicodeEncodeError" not in result.stderr, result.stderr
    assert result.returncode == 0, result.stderr


# Status screens need a board: the subprocess replaces the serial transport with a fake one.
_STATUS_DRIVER = textwrap.dedent(
    """
    import sys
    from trt.transport.serial_transport import SerialTransport
    import trt.transport.serial_transport as st
    import trt.services.board_discovery_service as ds

    INFO = bytes([6]) + b"".join(bytes([k, len(v)]) + v for k, v in [
        (1, b"am-modulation"), (2, b"STM32L073RZ"), (3, bytes([0, 1, 0])), (4, b"\\x01"),
        (5, b"am-modulation"), (6, b"STM32")])
    MODE = sys.argv[2].encode()

    class Fake:
        Frame = SerialTransport.Frame
        def __init__(self, port, baudrate=115200, timeout=1.0, **kw): self.port = port
        @staticmethod
        def available_ports(): return ["COM9"]
        def decode_capabilities(self, payload): return SerialTransport(port="X").decode_capabilities(payload)
        def exchange_command(self, command, board_id):
            replies = {1: (0x8001, b""), 2: (0x8003, bytes([0, 1, 0])), 3: (0x8003, b"STM32L073RZ"),
                       4: (0x8003, INFO), 6: (0x8003, bytes([1, 0, 1])), 7: (0x8003, b"000001"),
                       0x0A: (0x8003, MODE), 0x0B: (0x8003, b"\\x00\\x02")}
            code, payload = replies.get(command, (0x8002, b"\\x00\\x02"))
            return self.Frame(board_id=201, sequence_id=1, command=code, payload=payload)
        def close(self): pass

    st.SerialTransport = Fake
    ds.SerialTransport = Fake
    from trt.cli import main
    sys.argv = ["trt"] + sys.argv[1].split()
    main()
    """
)


@pytest.mark.parametrize("encoding", ["cp1252", "ascii"])
@pytest.mark.parametrize("command", ["boards", "discover", "board info 201"])
@pytest.mark.parametrize("mode", ["mode_0002_analog", "mode_0000_base"], ids=["match", "mismatch"])
def test_status_screens_on_legacy_consoles(
    command: str, mode: str, encoding: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _STATUS_DRIVER.replace("sys.argv[1]", repr(command)).replace("sys.argv[2]", repr(mode))
    monkeypatch.setenv("TRT_CLI_BOARD_CACHE", str(tmp_path / "boards.json"))
    result = _run([], encoding, script=script)
    assert "UnicodeEncodeError" not in result.stderr, result.stderr
    assert result.returncode == 0, result.stderr
    assert ("MISMATCH" if mode == "mode_0000_base" else "MATCH") in result.stdout
    assert "0010 / 00" in result.stdout


def test_closed_output_pipe_exits_quietly() -> None:
    # `trt help | head -1`: the reader stops early; trt must not print a traceback.
    process = subprocess.Popen(
        [sys.executable, "-m", "trt", "help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "COLUMNS": "80"},
    )
    assert process.stdout is not None and process.stderr is not None
    process.stdout.readline()
    process.stdout.close()
    stderr = process.stderr.read().decode(errors="replace")
    process.wait(timeout=60)
    assert "Traceback" not in stderr, stderr


def test_listen_stops_quietly_when_output_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    # `trt listen | grep -m1 HEARTBEAT`: printing from the reader thread fails once grep exits.
    import threading

    import typer

    from trt.commands import listen as listen_command
    from trt.transport.frame_reader import ReceivedFrame

    class FakeListenService:
        ports = ["COM9"]

        def listen(self, on_frame, stop: threading.Event, board_id=None, on_error=None) -> int:
            frame = ReceivedFrame(board_id=201, sequence_id=1, command=0x9001, flags=0x02, payload=b"")
            for _ in range(3):
                on_frame("COM9", frame)
            assert stop.is_set()  # the first failed print stopped listening
            return 1

    def broken_print(*args: object, **kwargs: object) -> None:
        if str(args[0]).startswith("Board"):
            raise OSError(22, "Invalid argument")

    monkeypatch.setattr(listen_command, "ListenService", FakeListenService)
    monkeypatch.setattr(listen_command.console, "print", broken_print)
    monkeypatch.setattr(listen_command, "stdout_closed", lambda: True)
    monkeypatch.setattr(listen_command, "discard_stdout", lambda: None)
    with pytest.raises(typer.Exit) as exit_info:
        listen_command.run_listen()
    assert exit_info.value.exit_code == 0
