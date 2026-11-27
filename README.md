# TRT - Tool Runtime Terminal

> A Python CLI for board-agnostic embedded hardware control over the TRT protocol. **Release candidate 1.0.0rc1 (Beta).**

TRT provides a unified command-line interface for controlling embedded boards across Windows, Linux, and macOS. Version 1.0.0 (currently release candidate `1.0.0rc1`) marks the first successful end-to-end hardware milestone: TRT-CLI opened COM4, sent TRT protocol frames to an Arduino Uno running TRT-Core firmware, decoded real responses, and displayed board identity data.

```text
TRT-CLI -> COM4 -> Arduino Uno -> TRT-Core -> real protocol response
```

Validated command:

```bash
trt board info 101
```

Validated firmware response:

```text
Board ID      101
BOARD_INFO    UNSPECIFIED
FW_VERSION    0.1.0
BUILD_ID      000004
```

> Terminology: the `Board ID` label above is the protocol `BOARD_ID` field (a node address, here 101). It is not the Board ID of the hardware platform, a HWID or an Application ID. See `TRT-core/docs/identifiers.md`.

---

## Why 1.0.0

TRT-CLI is now versioned as `1.0.0` because the project is no longer mock-only:

- first real hardware communication implemented
- first real TRT protocol transaction validated
- Arduino Uno end-to-end communication working over COM4
- serial discovery now enumerates ports and probes for TRT-compatible firmware
- mock-only status no longer applies to the core board discovery and board info path

---

## Technology

- Python 3.13+
- Typer for command routing
- Rich for terminal output
- pyserial for serial transport
- pytest for regression coverage
- typed protocol request/response models

---

## Current Status

| Area | Status |
|---|---|
| CLI executable `trt` | Implemented |
| Thin command adapters | Implemented |
| Application services | Implemented |
| Typed protocol contract | Implemented |
| Real serial transport | Implemented for discovery and board info |
| Arduino Uno TRT-Core communication | Validated |
| Mock operation support | Retained only as explicit test/support infrastructure |
| Heartbeat listening (`trt listen`, `trt board <id> listen`) | Implemented |
| STM32 application build (`trt build stm32 <program>`) | Implemented; needs `cmake` and `arm-none-eabi-gcc` |
| STM32 flash of a stored build (`trt flash stm32 [program]`) | Implemented; needs `STM32_Programmer_CLI` |
| STM32 application discovery (`trt list-programs stm32`) | Implemented |

Cross-platform status (Arduino, ESP32, STM32) is documented in the TRT-core repository: `docs/platform-status.md`.

---

## Installation

```bash
git clone https://github.com/AntonioTRT/TRT-cli.git
cd TRT-cli
pip install -e .
```

---

## Quick Start

```bash
trt help
trt version
trt discover
trt boards
trt board info 101
trt board capabilities 101
trt listen
trt board listen 101
```

`trt discover` enumerates available serial ports, probes them with TRT protocol frames, and lists compatible boards.

`trt listen` passively prints the messages boards send on their own. Every TRT-Core board emits a `HEARTBEAT` event about once per second, so after flashing, `Board 101: HEARTBEAT` lines confirm the firmware, transport and runtime are alive. It does not replace discovery. `trt board listen 101` shows only board 101. See [docs/cli-reference.md](docs/cli-reference.md#trt-listen).

### STM32 NUCLEO-L073RZ

From the workspace root containing `TRT-core/TRT-stm32` (needs `cmake`, `arm-none-eabi-gcc` and
`STM32_Programmer_CLI` on `PATH`):

```powershell
trt list-programs stm32          # applications available in the CubeIDE project
trt build stm32                  # common image: the daughter-board HWID selects the application
trt build stm32 0001             # development image that always runs app_0001 (skips HWID)
trt flash stm32                  # flash the latest build over the ST-LINK probe (SWD)
trt flash stm32 --platformio     # legacy PlatformIO project: build and upload
trt discover
trt stm32 test                   # discovers the board, then runs the protocol test
trt stm32 test --port COM5 --board-id 201
trt board info 201
```

`trt stm32 test` finds the board with the same probe as `trt discover` and uses its address. If
several boards answer it does not guess: it lists them and asks for `--board-id` (and `--port`).
If nothing is discovered it falls back to scanning ports with address `0x0002`. The test verifies
PING, FW_VERSION, BOARD_VERSION, INFO, STATUS, and CAPABILITIES at 115200 baud, 8N1.
`trt discover` saves each detected serial board's protocol `BOARD_ID`, COM port, and baudrate in
`%USERPROFILE%\.trt\boards.json`; `trt board info <id>` uses that saved port or
performs a discovery scan if there is no cached connection.

---

## Architecture

The hardware path follows this dependency direction:

```text
CLI -> Services -> ProtocolClient -> Transport -> Device
```

Key directories:

```text
src/trt/commands/       Typer handlers and Rich output
src/trt/services/       Board, discovery, LCD, LED, capability, and update orchestration
src/trt/protocol/       ProtocolOperation, typed requests/responses, protocol clients
src/trt/transport/      Transport interface, SerialTransport, MockTransport
src/trt/repositories/   Board state storage abstraction
src/trt/core/           Hardware-agnostic domain models
```

Commands parse arguments and render results. Services coordinate board operations. Protocol clients send typed request objects. Transports exchange frames with devices or provide explicit test doubles.

---

## Development

```bash
pip install -e ".[dev]"
pytest                       # hardware-independent; tests marked "hardware" are skipped
TRT_HARDWARE_TESTS=1 pytest  # also runs the tests that need an Arduino Uno on COM4
```

Optional checks:

```bash
ruff check src tests
mypy src
```

---

## Documentation

| Document | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Layered architecture and dependency flow |
| [docs/vision.md](docs/vision.md) | Mission, goals, roadmap |
| [docs/trt-protocol.md](docs/trt-protocol.md) | TRT Protocol V1 specification |
| [docs/cli-reference.md](docs/cli-reference.md) | Command reference |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |

---

## License

MIT - see [LICENSE](LICENSE).
