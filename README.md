# TRT - Tool Runtime Terminal

> A Python CLI for board-agnostic embedded hardware control with validated Arduino Uno communication over the TRT protocol.

TRT provides a unified command-line interface for controlling embedded boards across Windows, Linux, and macOS. Version 1.0.0 marks the first successful end-to-end hardware milestone: TRT-CLI opened COM4, sent TRT protocol frames to an Arduino Uno running TRT-Core firmware, decoded real responses, and displayed board identity data.

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

---

## Getting started

```text
trt discover                  Discover TRT boards
trt boards                    Show boards: application, HWID read / expected, MATCH
trt board info <address>      One board in detail
trt board update <address>    If MISMATCH: install the firmware that matches the HWID
trt listen                    Monitor heartbeat and events (Ctrl+C)
```

`<address>` is the board address shown by `trt boards` (e.g. 201). A board shows
`HWID 0010 / 0010  MATCH` (read from hardware / expected by the installed application) when its
firmware fits the connected daughter board, and `0010 / 0000  MISMATCH` when `trt board update`
is needed.

Help: `trt` (Quick Start), `trt --help` (commands grouped by purpose), `trt help` (concepts:
Board Address, Board ID, HWID, Application ID; workflow; heartbeat). Full reference:
[docs/cli-reference.md](docs/cli-reference.md).

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
| Heartbeat listening (`trt listen`, `trt board listen <address>`) | Implemented |
| STM32 application build (`trt build stm32 <app>`) | Validated on NUCLEO-L073RZ; uses `cmake` and `arm-none-eabi-gcc` from `PATH` or STM32CubeIDE |
| STM32 flash of a stored build (`trt flash stm32 [app]`) | Validated; uses `STM32_Programmer_CLI` from `PATH` or STM32CubeIDE |
| STM32 application discovery (`trt list-programs stm32`) | Implemented (`app_<HWID>_<name>`) |
| HWID query (`trt board hwid <address>`) | Validated on STM32 |
| HWID-driven update (`trt board update <address> [--check]`) | Validated on STM32: detect mismatch, build, flash, reboot, verify |
| HWID / application status in `trt boards`, `trt discover`, `trt board info` (`0010 / 0010 MATCH`) | Validated on STM32 |

Cross-platform status (Arduino, ESP32, STM32) is documented in the TRT-core repository: `docs/platform-status.md`.

---

## Installation

```bash
git clone https://github.com/trt-project/trt-cli.git
cd trt-cli
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

From the workspace root containing `TRT-core/TRT-stm32`. Build and flash use the
STM32CubeIDE toolchain (found automatically under `C:\ST`) and the ST-LINK probe;
only `--platformio` needs PlatformIO Core:

```powershell
trt board update 201 --check   # does the installed application match the board's HWID?
trt board update 201           # if not: build, flash, reboot and verify the matching one
trt flash stm32 --platformio
trt stm32 test
trt stm32 test --port COM5
trt board info 2
trt board info 2 --port COM5
```

The protocol test scans serial ports if `--port` is omitted and verifies PING,
FW_VERSION, BOARD_VERSION, INFO, STATUS, and CAPABILITIES at 115200 baud, 8N1.
`trt discover` saves each detected board address, COM port, and baudrate in
`%USERPROFILE%\.trt\boards.json`; `trt board info 2` uses that saved port or
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
pytest
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
