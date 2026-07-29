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

## trt-cli Layer (Current)

### Responsibilities
- Parse and route user commands
- Display formatted terminal output (Rich)
- Maintain an in-memory BoardRegistry
- Gate commands on board capabilities
- Provide mock implementations for all commands

### Key Components

#### `trt/cli.py`
Main Typer application.  Registers all top-level commands and sub-apps.

#### `trt/commands/`
One module per command domain:

| Module         | Commands                               |
|----------------|----------------------------------------|
| `help.py`      | `trt help`                             |
| `version.py`   | `trt version`                          |
| `boards.py`    | `trt boards`                           |
| `discover.py`  | `trt discover`                         |
| `board.py`     | `trt board <id> *` (full sub-tree)     |
| `lcd.py`       | `trt lcd *`                            |
| `led.py`       | `trt led *`                            |
| `protocol.py`  | `trt protocol *`                       |

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

See [docs/vision.md](vision.md) for the full roadmap.
