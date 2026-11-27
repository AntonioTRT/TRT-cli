"""Test isolation from real hardware.

Tests marked ``hardware`` talk to a real TRT board on a serial port and are skipped by default
(``addopts = -m "not hardware"`` in pyproject.toml). Run them with:

    pytest -m hardware                      # board at address 101 (Arduino Uno)
    TRT_TEST_BOARD=201 pytest -m hardware   # another address, e.g. the STM32 board

Every other test is isolated: it sees no serial ports and uses a temporary board cache, so a plain
``pytest`` never opens a COM port or reads the user's ``~/.trt/boards.json``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

HARDWARE_BOARD = os.environ.get("TRT_TEST_BOARD", "101")


@pytest.fixture()
def hardware_board() -> str:
    """Address of the board used by hardware tests (TRT_TEST_BOARD, default 101)."""
    return HARDWARE_BOARD


@pytest.fixture(autouse=True)
def _isolate_from_hardware(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if request.node.get_closest_marker("hardware"):
        return
    from trt.transport.serial_transport import SerialTransport

    monkeypatch.setenv("TRT_CLI_BOARD_CACHE", str(tmp_path / "boards.json"))
    monkeypatch.setattr(SerialTransport, "available_ports", staticmethod(list))
