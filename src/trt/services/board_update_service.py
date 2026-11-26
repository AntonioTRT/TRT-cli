"""Firmware/HWID consistency check and update for one board.

Production model: a board carries TRT-Core (Base Mode) plus exactly one mode, chosen for the daughter
board fitted to it. The daughter board is identified by its hardware ID (HWID), which the firmware
reads from ID pins at boot and reports with the HWID query (0x000B). The firmware reports its mode
with ACTIVE_MODE (0x000A); modes are named mode_<ID, 4 digits>_<name> and the mode ID is the HWID it
expects, so the installed mode matches the board when that ID equals the board's HWID.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from trt.commands.build import mode_for_hwid
from trt.core.modes import mode_id
from trt.protocol.v01 import decode_info_payload
from trt.services.board_query_service import (
    CMD_ACTIVE_MODE,
    CMD_HWID,
    CMD_INFO,
    RESP_DATA,
    RESP_NACK,
    decode_hwid,
)
from trt.services.board_service import resolve_serial_connection
from trt.transport.serial_transport import SerialTransport

SUPPORTED_FAMILIES = ("STM32",)


class HwidUnsupportedError(RuntimeError):
    """The board's firmware does not report a HWID (it predates HWID support)."""


@dataclass(frozen=True)
class BoardState:
    board_id: str
    port: str
    family: str
    hwid: int
    installed: str | None  # ACTIVE_MODE; None when the firmware declares no mode


@dataclass(frozen=True)
class UpdatePlan:
    state: BoardState
    required: str | None  # mode for the board's HWID; None when the project has none

    @property
    def installed_hwid(self) -> int | None:
        return mode_id(self.state.installed) if self.state.installed else None

    @property
    def matches(self) -> bool:
        return self.required is not None and self.state.installed == self.required


def read_board_state(board_id: str, port: str | None = None) -> BoardState:
    resolved_id, port, baudrate = resolve_serial_connection(board_id, port)
    transport = SerialTransport(port=port, baudrate=baudrate)
    try:
        hwid_frame = transport.exchange_command(CMD_HWID, resolved_id)
        if hwid_frame.command == RESP_NACK:
            raise HwidUnsupportedError(f"Board {resolved_id} firmware does not report a HWID")
        _require_data(hwid_frame.command, "HWID")
        hwid = decode_hwid(hwid_frame.payload)

        program_frame = transport.exchange_command(CMD_ACTIVE_MODE, resolved_id)
        installed = None
        if program_frame.command == RESP_DATA:
            installed = program_frame.payload.decode("utf-8", errors="replace")
        elif program_frame.command != RESP_NACK:
            _require_data(program_frame.command, "ACTIVE_MODE")

        info_frame = transport.exchange_command(CMD_INFO, resolved_id)
        _require_data(info_frame.command, "INFO")
        family = decode_info_payload(info_frame.payload).get("family", "")
    finally:
        transport.close()
    return BoardState(str(hwid_frame.board_id), port, family, hwid, installed)


def plan_update(state: BoardState, cube_dir: Path) -> UpdatePlan:
    return UpdatePlan(state=state, required=mode_for_hwid(cube_dir, state.hwid))


def wait_for_board(board_id: str, port: str, timeout: float = 20.0, interval: float = 1.0) -> BoardState:
    """Re-read the board after a reset until it answers again (the serial port survives an SWD reset)."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return read_board_state(board_id, port)
        except (OSError, RuntimeError, TimeoutError, ValueError) as error:
            last_error = error
            time.sleep(interval)
    raise TimeoutError(f"Board {board_id} did not answer on {port} after the update: {last_error}")


def _require_data(command: int, item: str) -> None:
    if command != RESP_DATA:
        raise ValueError(f"Unexpected response 0x{command:04X} to {item}")
