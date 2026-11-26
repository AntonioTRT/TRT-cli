"""TRT modes and the hardware ID (HWID) they are written for.

A firmware image is TRT-Core + Base Mode + one mode, named mode_<ID, 4 digits>_<name>. The mode ID
is the HWID of the daughter board it drives and is the same on every TRT platform. The board reads
its actual HWID from ID pins at boot; the installed mode matches the hardware when both are equal.
Mode 0000 is Base Mode: the recovery / maintenance runtime, used when no daughter board is fitted.
"""

from __future__ import annotations

import re
from enum import Enum

MODE_NAME = re.compile(r"^mode_(\d{4})_[a-z0-9_]+$")
HWID_BITS = 4  # ID pins on today's carrier: D3 (bit 0) .. D6 (bit 3)
BASE_MODE_ID = 0

# HWID family codes (TRT_CHAINING_SPEC_v0.1, D-09) and the standard modes that drive them.
# The mode ID equals the code and is common to every TRT platform (docs/modes.md in TRT-core).
STANDARD_MODES: dict[int, str] = {
    0: "Base Mode (no daughter board; recovery / maintenance)",
    2: "Analog family",
    3: "Keypad (switch matrix) family",
    4: "Encoder family",
    5: "I2C display (OLED)",
    6: "SPI display (TFT)",
    7: "Addressable LED (rings, strips)",
    12: "Blink / test (experimental, never in production)",
}
# HWID codes that never select a mode.
RESERVED_HWID: dict[int, str] = {
    1: "Self-describing module: read its descriptor",
    8: "Reserved family", 9: "Reserved family", 10: "Reserved family", 11: "Reserved family",
    13: "Experimental / custom",
    14: "Factory test fixture",
    15: "Fault or invalid (all lines high)",
}


def mode_id(mode: str | None) -> int | None:
    """Mode ID (= HWID it expects) from a mode name: mode_0002_analog -> 2; None if not mode_<ID>_*."""
    match = MODE_NAME.match(mode or "")
    return int(match.group(1)) if match else None


class HwidMatch(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NO_HWID = "NO HWID"  # firmware does not report a HWID (predates HWID support)
    NO_MODE = "NO MODE"  # firmware declares no mode, or one not named mode_<ID>_*


def hwid_match(hwid_read: int | None, hwid_expected: int | None) -> HwidMatch:
    if hwid_read is None:
        return HwidMatch.NO_HWID
    if hwid_expected is None:
        return HwidMatch.NO_MODE
    return HwidMatch.MATCH if hwid_read == hwid_expected else HwidMatch.MISMATCH


def format_hwid(hwid: int | None) -> str:
    """HWID as the ID-pin pattern, most significant pin first: 2 -> 0010; unknown -> ----."""
    if hwid is None:
        return "-" * HWID_BITS
    return format(hwid, f"0{HWID_BITS}b")
