"""Board applications and the hardware ID (HWID) they are written for.

Production firmware is TRT-Core plus one application, named app_<HWID, 4 digits>_<name>. The HWID in
the name is the daughter-board hardware ID the application expects; the board reads its actual HWID
from ID pins at boot. They match when both values are equal.
"""

from __future__ import annotations

import re
from enum import Enum

APP_NAME = re.compile(r"^app_(\d{4})_[a-z0-9_]+$")
HWID_BITS = 4  # ID pins on today's carrier: D3 (bit 0) .. D6 (bit 3)


def app_hwid(program: str | None) -> int | None:
    """HWID an application is built for: app_0002_analog_family -> 2; None if not named app_<HWID>_*."""
    match = APP_NAME.match(program or "")
    return int(match.group(1)) if match else None


class HwidMatch(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NO_HWID = "NO HWID"  # firmware does not report a HWID (predates HWID support)
    NO_APP = "NO APP"  # firmware declares no application, or one not named app_<HWID>_*


def hwid_match(hwid_read: int | None, hwid_expected: int | None) -> HwidMatch:
    if hwid_read is None:
        return HwidMatch.NO_HWID
    if hwid_expected is None:
        return HwidMatch.NO_APP
    return HwidMatch.MATCH if hwid_read == hwid_expected else HwidMatch.MISMATCH


def format_hwid(hwid: int | None) -> str:
    """HWID as the ID-pin pattern, most significant pin first: 2 -> 0010; unknown -> ----."""
    if hwid is None:
        return "-" * HWID_BITS
    return format(hwid, f"0{HWID_BITS}b")
