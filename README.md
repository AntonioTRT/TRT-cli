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
```

`trt discover` enumerates available serial ports, probes them with TRT protocol frames, and lists compatible boards.

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
