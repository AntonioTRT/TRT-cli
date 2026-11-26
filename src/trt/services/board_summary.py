"""One status summary per board, shared by `trt boards`, `trt discover`, `trt board info` and
`trt board update`, so every command shows the same values with the same meaning."""

from __future__ import annotations

from dataclasses import dataclass

from trt.core.models import Board
from trt.core.modes import HwidMatch, hwid_match, mode_id
from trt.transport.serial_transport import SerialTransport

CMD_ACTIVE_MODE = 0x000A
CMD_HWID = 0x000B
RESP_DATA = 0x8003

# Board.metadata keys written by discovery.
META_NAME = "board_type"  # INFO field 0x01 (V0.1 calls the board name "board type")
META_FAMILY = "family"
META_BUILD_ID = "build_id"
META_ACTIVE_MODE = "active_mode"
META_HWID = "hwid"


@dataclass(frozen=True)
class BoardSummary:
    board_id: str
    name: str
    family: str
    firmware: str
    build_id: str
    active_mode: str | None
    hwid_read: int | None
    port: str | None = None

    @property
    def hwid_expected(self) -> int | None:
        return mode_id(self.active_mode)

    @property
    def match(self) -> HwidMatch:
        return hwid_match(self.hwid_read, self.hwid_expected)


def read_mode_state(transport: SerialTransport, board_id: str) -> tuple[int | None, str | None]:
    """(HWID, ACTIVE_MODE) from the board; None for each value the firmware does not report."""
    hwid_frame = transport.exchange_command(CMD_HWID, board_id)
    hwid = None
    if hwid_frame.command == RESP_DATA and len(hwid_frame.payload) == 2:
        hwid = int.from_bytes(hwid_frame.payload, byteorder="big")
    program_frame = transport.exchange_command(CMD_ACTIVE_MODE, board_id)
    program = None
    if program_frame.command == RESP_DATA and program_frame.payload:
        program = program_frame.payload.decode("utf-8", errors="replace")
    return hwid, program


def mode_metadata(hwid: int | None, program: str | None) -> dict[str, str]:
    return {META_HWID: "" if hwid is None else str(hwid), META_ACTIVE_MODE: program or ""}


def summary_from_board(board: Board) -> BoardSummary:
    meta = board.metadata
    hwid_text = meta.get(META_HWID, "")
    return BoardSummary(
        board_id=board.identity.board_id,
        name=meta.get(META_NAME) or board.identity.board_type.value,
        family=meta.get(META_FAMILY, ""),
        firmware=board.identity.firmware or "-",
        build_id=meta.get(META_BUILD_ID) or board.identity.serial or "-",
        active_mode=meta.get(META_ACTIVE_MODE) or None,
        hwid_read=int(hwid_text) if hwid_text.isdigit() else None,
        port=board.transport.port if board.transport else None,
    )
