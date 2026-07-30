# TRT Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Developer / User                      │
└────────────────────────┬────────────────────────────────┘
                         │  trt <command>
┌────────────────────────▼────────────────────────────────┐
│                   trt-cli  (this repo)                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Typer App  ·  Command Router  ·  Rich Output   │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌───────────────────────▼─────────────────────────┐    │
│  │  BoardRegistry  ·  BoardCapabilities  ·  Models  │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │  TRT Protocol messages
┌────────────────────────▼────────────────────────────────┐
│              trt-protocol  (future repo)                 │
│  Message serialisation  ·  CRC  ·  Versioning           │
└────────────────────────┬────────────────────────────────┘
                         │  USB CDC / CAN / TCP
┌────────────────────────▼────────────────────────────────┐
│               Transport Layer  (future)                  │
│  USB (milestone 2)  ·  CAN (future)  ·  TCP (future)    │
└────────────────────────┬────────────────────────────────┘
                         │  physical connection
┌────────────────────────▼────────────────────────────────┐
│               Embedded Firmware  (future)                │
│  trt-core  ·  trt-modules  ·  Board HAL                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Embedded Hardware                           │
│  GPIO  ·  PWM  ·  ADC  ·  DAC  ·  I2C  ·  SPI  ·  ...  │
└─────────────────────────────────────────────────────────┘
```

---

## Capability-Driven Design

> The CLI defines syntax. The board decides execution.

TRT's core design principle is that **command support is determined at runtime by the board, not at compile time by trt-cli**.

```
User:  trt board board1 dac read 1
         │
         │  trt-cli always sends the command — no pre-filtering
         ▼
       TRT Protocol frame  →  board1
         │
         ├── board1 HAS DAC?  →  DATA response  →  "1.65V"
         └── board1 NO DAC?   →  NACK response  →  "ERROR_UNSUPPORTED_COMMAND"
```

This means:
- `trt-cli` never needs board-specific logic
- New board types work without changing the CLI
- The same CLI supports STM32, Arduino, RP2040, simulators, and future boards
- `trt board board1 dac read 1` is always valid CLI syntax regardless of board type

See [trt-protocol.md § 3. Capability-Driven Architecture](trt-protocol.md#3-capability-driven-architecture) for the full design rationale.

---

## trt-cli Layer (Current)

### Responsibilities
- Parse and route user commands
- Display formatted terminal output (Rich)
- Maintain an in-memory BoardRegistry
- Forward all commands to the board; display whatever the board returns
- Provide mock implementations for all commands (milestone 1)

### Key Components

#### `trt/cli.py`
Main Typer application.  Registers all top-level commands and sub-apps.

#### `trt/commands/`
One module per command domain:

| Module         | Commands                               |
|----------------|----------------------------------------|
| `help.py`      | `trt help`                             |
| `version.py`   | `trt version`                          |
| `update.py`    | `trt update`                           |
| `boards.py`    | `trt boards`                           |
| `discover.py`  | `trt discover`                         |
| `board.py`     | `trt board <id> *` (full sub-tree)     |
| `lcd.py`       | `trt lcd *`                            |
| `led.py`       | `trt led *`                            |
| `protocol.py`  | `trt protocol *`                       |

#### `trt/services/`
Business-logic service layer, independent of the CLI presentation layer.
Services are called by command handlers and can be tested in isolation.

| Module               | Responsibility                                   |
|----------------------|--------------------------------------------------|
| `update_service.py`  | GitHub release check · version comparison · install |

**`update_service.py` architecture:**

```
check_for_update()          → UpdateCheckResult
    status: UP_TO_DATE | UPDATE_AVAILABLE | CHECK_FAILED
    current_version: str    (from trt.version — never hardcoded)
    latest_version:  str    (from GitHub API tag_name)
    release_url:     str
    upgrade_command: str    (auto-detected: pip / pipx / uv)

install_update()            → UpdateInstallResult
    success:     bool
    message:     str
    new_version: str | None

detect_install_method()     → InstallMethod (PIP | PIPX | UV | UNKNOWN)
```

**Update scope — two independent commands:**

| Command | Scope |
|---|---|
| `trt update` | Updates the `trt-cli` Python package on the developer's machine |
| `trt board <id> update` *(future)* | Updates firmware on a connected embedded board |

These two update paths are completely independent and must never be conflated.

**Phase 1 (current):**  Command exists, displays current version, GitHub check is a documented placeholder.

**Phase 2:**  Real HTTP GET to `https://api.github.com/repos/AntonioTRT/TRT-cli/releases/latest`, semantic version comparison, install via detected package manager.

#### `trt/core/models.py`
All domain data structures — typed dataclasses with no external dependencies.

### Data Model

```
Board
├── BoardIdentity       board_id, board_type, revision, firmware, serial
├── BoardStatus         DISCONNECTED | CONNECTED | INITIALIZING | READY | ERROR | OFFLINE
├── TransportConfig     transport_type, port, baudrate, timeout_ms
└── BoardCapabilities   gpio, pwm, adc, dac, i2c, spi, uart, can, lcd, relay, debug_shell
```

`BoardRegistry` is the session-level store.  `make_mock_registry()` populates two mock boards for milestone 1.

---

## Capability-Based Design

A board **advertises** its capabilities at connection time (future: via TRT Protocol handshake).  The CLI reads these and gates commands accordingly.

```python
if not board.capabilities.has("gpio"):
    raise CommandError("Board does not support GPIO")
```

This means:
- The CLI never hard-codes board types.
- An Arduino and a TRT_CORE board can coexist in the same session.
- A future simulator board works without any CLI changes.

**Adding a new peripheral** requires only:
1. Adding a field to `BoardCapabilities`.
2. Creating a new command module.
3. Registering it in `cli.py`.

---

## Command Architecture

### Naming Convention

TRT follows the `<tool> <noun> <verb> [args]` pattern from `kubectl` and `docker`:

```
trt  board  board0  gpio  write  PA5  1
 │     │      │      │      │    │    │
tool  noun   id    domain  verb  arg  arg
```

Top-level convenience commands (`lcd`, `led`) drop the board qualifier for brevity.

### Sub-App Pattern (Typer)

Each command group is a separate `typer.Typer()` instance added to the main app:

```python
app.add_typer(board_app, name="board")
app.add_typer(lcd_app,   name="lcd")
```

Within `board_app`, each hardware domain is also a sub-app:

```python
board_app.add_typer(gpio_app, name="gpio")
board_app.add_typer(pwm_app,  name="pwm")
```

---

## Extension Points

### Adding a New Top-Level Command
1. Create `src/trt/commands/mycommand.py` with a `typer.Typer()` instance or a plain function.
2. Register in `src/trt/cli.py`.

### Adding a New Board Sub-Command
1. Create a sub-app in `src/trt/commands/board.py` (or a new file).
2. Add it to `board_app` via `board_app.add_typer(...)`.

### Adding a New Capability
1. Add a field to `BoardCapabilities` in `src/trt/core/models.py`.
2. Use `board.capabilities.has("my_cap")` to gate the new command.

### Adding a New Transport
1. Add a value to `TransportType` enum.
2. Extend `TransportConfig` with transport-specific fields.
3. Implement the transport in `trt-protocol` (future repo).

### Adding a New Board Type
1. Add a value to `BoardType` enum.
2. No other changes needed — capabilities handle the rest.

---

## Testing Strategy

| Layer              | Test Type    | Location                   |
|--------------------|--------------|----------------------------|
| CLI commands       | Integration  | `tests/test_cli.py`        |
| Data models        | Unit         | `tests/test_cli.py`        |
| Board registry     | Unit         | `tests/test_cli.py`        |
| Transport (future) | Integration  | `tests/test_transport.py`  |
| Protocol (future)  | Unit         | `tests/test_protocol.py`   |

---

## Repository Map

```
trt-cli/           This repository
trt-protocol/      Binary message protocol (future)
trt-core/          C/C++ firmware library (future)
trt-modules/       Firmware peripheral drivers (future)
```

## Protocol Specification

The TRT Protocol V1 frame structure, field definitions, transport strategy, open questions, and design rationale are fully documented in:

**[docs/trt-protocol.md](trt-protocol.md)**

Key facts:
- Frame: `SYNC | VERSION | FLAGS | BOARD_ID | SEQ_ID | COMMAND | LENGTH | PAYLOAD | CRC16`
- Transport-agnostic: same frame over USB CDC, CAN FD, TCP/IP
- V1 transport: USB CDC only
- Supports chunked transfers for firmware updates and large payloads
- `future-protocol.md` is superseded by `trt-protocol.md` for design decisions

See [docs/vision.md](vision.md) for the full roadmap.
