"""Help UX: `trt` (Quick Start) < `trt --help` (grouped commands) < `trt help` (full reference)."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from trt.cli import app

runner = CliRunner(env={"COLUMNS": "100"})

WORKFLOW = ("trt discover", "trt boards", "trt board info", "trt board update", "trt listen")
HIDDEN = ("lcd", "led", "protocol")


def _lists_command(output: str, name: str) -> bool:
    """True when `name` appears as a command row of a Typer help panel."""
    return re.search(rf"^\W\s+{re.escape(name)}\s{{2,}}", output, flags=re.MULTILINE) is not None


def test_bare_trt_shows_short_quick_start() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Quick Start" in result.output
    for command in WORKFLOW:
        assert command in result.output
    assert "trt help" in result.output and "trt --help" in result.output
    assert len([line for line in result.output.splitlines() if line.strip()]) <= 12
    assert "build" not in result.output and "lcd" not in result.output


def test_dash_dash_help_groups_commands_in_workflow_order() -> None:
    output = runner.invoke(app, ["--help"]).output
    panels = ["Board Discovery", "Board Management", "Monitoring", "Development", "Information"]
    positions = [output.index(panel) for panel in panels]
    assert positions == sorted(positions)
    for text in ("Scan serial ports", "MATCH status", "heartbeat", "trt board update ADDRESS", "trt board hwid ADDRESS"):
        assert text in output
    assert _lists_command(output, "discover")
    for name in HIDDEN:
        assert not _lists_command(output, name), name


def test_trt_help_is_the_full_reference() -> None:
    output = runner.invoke(app, ["help"]).output
    for text in (
        "Concepts", "Board Address", "Board ID", "HWID", "Mode", "Base Mode", "mode_0007_led",
        "Not implemented yet", "Reading the board status", "MATCH", "MISMATCH",
        "HWID read      0010", "HWID expected  0000", "Typical workflow", "Heartbeat",
        "trt board listen <address>", "trt flash stm32 [mode]", "trt list-modes stm32", "Update the TRT CLI itself",
    ):
        assert text in output, text
    assert "gpio" not in output and "--dev" not in output
    assert output.isascii()


def test_board_help_hides_simulated_commands() -> None:
    output = runner.invoke(app, ["board", "--help"]).output
    assert "Status and update" in output and "Single-value queries" in output
    assert _lists_command(output, "update")
    for name in ("gpio", "pwm", "adc", "dac", "i2c", "spi", "debug", "modules", "reset", "reboot", "status"):
        assert not _lists_command(output, name), name
    assert "ADDRESS" in runner.invoke(app, ["board", "info", "--help"]).output


def test_hidden_commands_still_work() -> None:
    assert runner.invoke(app, ["lcd", "info"]).exit_code == 0
    assert runner.invoke(app, ["board", "gpio", "--help"]).exit_code == 0
    assert runner.invoke(app, ["protocol", "--help"]).exit_code == 0


def test_former_names_are_hidden_aliases() -> None:
    assert "list-programs" not in runner.invoke(app, ["--help"]).output
    assert runner.invoke(app, ["list-programs", "--help"]).exit_code == 0
    board_help = runner.invoke(app, ["board", "--help"]).output
    assert _lists_command(board_help, "mode") and not _lists_command(board_help, "active-program")
    assert runner.invoke(app, ["board", "active-program", "--help"]).exit_code == 0
