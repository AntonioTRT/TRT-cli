"""Core models for TRT.

Defines all data structures for boards, capabilities, transports, and modules.
These models are intentionally hardware-agnostic. Boards are identified by type,
revision, and capabilities — never by MCU family.

Design Principles:
    - Boards advertise capabilities; the CLI adapts to what a board can do.
    - No MCU-specific logic belongs here (no "STM32", "RP2040", "Arduino" names).
    - TransportConfig is defined for USB now; CAN and TCP are extension points.
    - All models are fully typed dataclasses suitable for serialisation.

Future Expansion Points:
    - BoardConnection: integrates with TRT Protocol (trt-protocol repo)
    - BoardCapabilities: populated via protocol handshake with real firmware
    - TransportConfig: extended to CAN / TCP when those transports land
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class TransportType(str, Enum):
    """Physical transport layer used to reach a board.

    Only USB is active for milestone 1.  CAN and TCP are reserved for future
    transport implementations in trt-protocol.
    """

    USB = "usb"
    CAN = "can"       # Future: CAN bus transport
    TCP = "tcp"       # Future: Ethernet / TCP transport
    SIMULATOR = "simulator"  # Future: software simulator transport


class BoardStatus(str, Enum):
    """Lifecycle state of a board as seen by trt-cli.

    Future Implementation: states will be driven by TRT Protocol responses.
    """

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    OFFLINE = "offline"


class BoardType(str, Enum):
    """Board type identifiers used by TRT.

    Boards are typed by function/role, not by MCU family.  This allows the CLI
    to support TRT_CORE, Arduino, RP2040-based, and future boards uniformly.
    """

    TRT_CORE = "TRT_CORE"
    TRT_MODULE = "TRT_MODULE"
    ARDUINO = "Arduino"
    RP2040 = "RP2040"
    SIMULATOR = "Simulator"
    UNKNOWN = "Unknown"


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

@dataclass
class TransportConfig:
    """Describes the physical connection to a board.

    For milestone 1, only USB is used.  Future transports (CAN, TCP) will
    add their own fields here or in subclasses.

    Future:
        - CAN bus node ID and bitrate
        - TCP host/port and TLS options
        - Connection pooling hints
    """

    transport_type: TransportType = TransportType.USB
    port: Optional[str] = None          # e.g. "COM3" or "/dev/ttyACM0"
    baudrate: Optional[int] = None      # USB CDC: None (native), Serial: 115200
    timeout_ms: int = 1000
    retry_count: int = 3

    def __str__(self) -> str:
        if self.port:
            return f"{self.transport_type.value}:{self.port}"
        return self.transport_type.value


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------

@dataclass
class BoardCapabilities:
    """Feature set advertised by a board.

    In the future this will be populated via a TRT Protocol capabilities
    handshake.  For now it is set manually on mock board objects.

    The CLI uses this at runtime to decide which sub-commands are available
    for a given board, so all hardware-specific gating flows through here.
    """

    gpio: bool = False
    pwm: bool = False
    adc: bool = False
    dac: bool = False
    i2c: bool = False
    spi: bool = False
    uart: bool = False
    can: bool = False
    lcd: bool = False
    relay: bool = False
    debug_shell: bool = False
    # Extension point: modules can add capabilities via this dict
    custom: dict[str, bool] = field(default_factory=dict)

    def has(self, capability: str) -> bool:
        """Return True if the board supports *capability*.

        Checks first-class fields by name, then falls back to ``custom``.
        """
        if hasattr(self, capability):
            val = getattr(self, capability)
            if isinstance(val, bool):
                return val
        return self.custom.get(capability, False)

    def as_dict(self) -> dict[str, bool]:
        """Return all standard capabilities as a plain dict."""
        standard = {
            "gpio": self.gpio,
            "pwm": self.pwm,
            "adc": self.adc,
            "dac": self.dac,
            "i2c": self.i2c,
            "spi": self.spi,
            "uart": self.uart,
            "can": self.can,
            "lcd": self.lcd,
            "relay": self.relay,
            "debug_shell": self.debug_shell,
        }
        standard.update(self.custom)
        return standard


# ---------------------------------------------------------------------------
# Board identity
# ---------------------------------------------------------------------------

@dataclass
class BoardIdentity:
    """Identifies a board without referencing MCU family.

    Fields are populated from device firmware via TRT Protocol.
    For mock boards they are set statically.

    Note: board_id is a *logical* identifier assigned by trt-cli (e.g. "board0").
    It is NOT the serial number.  serial is what the firmware reports.
    """

    board_id: str                          # CLI-assigned handle, e.g. "board0"
    board_type: BoardType = BoardType.UNKNOWN
    revision: str = "A1"                   # Hardware revision from firmware
    firmware: str = "0.1.0"               # Firmware version string
    serial: Optional[str] = None           # Device serial number from firmware

    def __str__(self) -> str:
        return f"{self.board_id} ({self.board_type.value})"


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

@dataclass
class Board:
    """Represents a single connected or discoverable TRT board.

    This is the central domain object in trt-cli.  All per-board sub-commands
    (gpio, pwm, i2c, …) are gated on ``capabilities``.

    Current Status: mock objects only — no real USB traffic.
    Future: instantiated from TRT Protocol discovery responses.
    """

    identity: BoardIdentity
    status: BoardStatus = BoardStatus.DISCONNECTED
    transport: Optional[TransportConfig] = None
    capabilities: BoardCapabilities = field(default_factory=BoardCapabilities)
    metadata: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Board[{self.identity}] status={self.status.value}"

    def is_connected(self) -> bool:
        return self.status in (BoardStatus.CONNECTED, BoardStatus.READY)

    def is_ready(self) -> bool:
        return self.status == BoardStatus.READY


# ---------------------------------------------------------------------------
# Board registry
# ---------------------------------------------------------------------------

class BoardRegistry:
    """In-memory registry of all known boards for the current session.

    Acts as the single source of truth for board state within trt-cli.

    Future Implementation:
        - Populated via USB discovery scan (trt-protocol)
        - Persists last-known-good state to a local cache file
        - Emits events on connect / disconnect
    """

    def __init__(self) -> None:
        self._boards: dict[str, Board] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, board: Board) -> None:
        self._boards[board.identity.board_id] = board

    def remove(self, board_id: str) -> bool:
        if board_id in self._boards:
            del self._boards[board_id]
            return True
        return False

    def clear(self) -> None:
        self._boards.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, board_id: str) -> Optional[Board]:
        return self._boards.get(board_id)

    def all(self) -> list[Board]:
        return list(self._boards.values())

    def connected(self) -> list[Board]:
        return [b for b in self._boards.values() if b.is_connected()]

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._boards)

    def __iter__(self):  # type: ignore[override]
        return iter(self._boards.values())


# ---------------------------------------------------------------------------
# Mock data factory
# ---------------------------------------------------------------------------

def make_mock_registry() -> BoardRegistry:
    """Return a BoardRegistry pre-populated with two mock boards.

    Used by ``trt boards`` and ``trt discover`` until real USB discovery
    is implemented.
    """
    registry = BoardRegistry()

    board0 = Board(
        identity=BoardIdentity(
            board_id="board0",
            board_type=BoardType.TRT_CORE,
            revision="A1",
            firmware="0.1.0",
            serial="000001",
        ),
        status=BoardStatus.READY,
        transport=TransportConfig(transport_type=TransportType.USB, port="COM3"),
        capabilities=BoardCapabilities(
            gpio=True, pwm=True, adc=True, dac=True,
            i2c=True, spi=True, uart=True, debug_shell=True,
        ),
    )

    board1 = Board(
        identity=BoardIdentity(
            board_id="board1",
            board_type=BoardType.ARDUINO,
            revision="R3",
            firmware="0.1.0",
            serial="000002",
        ),
        status=BoardStatus.CONNECTED,
        transport=TransportConfig(transport_type=TransportType.USB, port="COM4"),
        capabilities=BoardCapabilities(gpio=True, pwm=True, adc=True, i2c=True),
    )

    registry.register(board0)
    registry.register(board1)
    return registry
