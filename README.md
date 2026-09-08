# TRT - Tool Runtime Terminal

> A Python CLI for board-agnostic embedded hardware control, built around thin command adapters, application services, protocol abstractions, and a mock transport boundary.

TRT provides a unified, git-style command-line interface for controlling embedded boards across Windows, Linux, and macOS. The current implementation is intentionally mock-backed, but every hardware-shaped operation now follows the same architecture that future real hardware support will use.

```text
CLI -> Service -> ProtocolClient -> Transport -> Mock Device
```

The command names and user experience remain stable while the lower layers evolve.

---

## Technology

- Python 3.13+
- Typer for command routing
- Rich for terminal output
- pytest for regression coverage
- Dataclasses and typed service/protocol/transport boundaries

---

## Current Status

| Area | Status |
|---|---|
| CLI executable `trt` | Implemented |
| Thin command adapters | Implemented |
| Application services | Implemented |
| Typed protocol request/response models | Implemented |
| Protocol client abstraction | Implemented |
| Mock transport device responses | Implemented |
| Real USB/CAN/TCP communication | Future |
| Real TRT protocol framing | Future |
| Firmware-backed discovery | Future |

`MockTransport` is the only component that generates simulated hardware responses. CLI commands parse arguments, call services, and render returned data.

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
trt update
trt boards
trt discover

trt board info board0
trt board capabilities board0
trt board gpio list board0
trt board gpio write board0 PA5 1
trt board pwm set board0 1 1000 50
trt board adc read board0 3
trt board i2c scan board0

trt lcd write "Hello"
trt led color 255 0 0
trt protocol info
```

---

## Architecture

The project is organized around clear dependency direction:

```text
src/trt/commands/       Typer handlers and Rich output only
src/trt/services/       Board, discovery, LCD, LED, capability, and update orchestration
src/trt/protocol/       ProtocolOperation, typed requests/responses, ProtocolClient
src/trt/transport/      Transport interface and MockTransport
src/trt/repositories/   Board state storage abstraction
src/trt/core/           Hardware-agnostic domain models
```

Hardware-related commands flow through services into protocol and transport abstractions. The mock implementation lives behind `MockTransport`, so future real transports can replace it without changing the command surface.

Protocol operations are represented by `ProtocolOperation` enum values and operation-specific dataclasses such as `GpioReadRequest`, `GpioWriteRequest`, `DiscoverRequest`, and `GpioReadResponse`. Services no longer construct raw operation strings or request payload dictionaries.

---

## Capability-Driven Design

TRT avoids board-family-specific command logic. Boards advertise capabilities such as GPIO, PWM, ADC, DAC, I2C, SPI, LCD, and debug shell support. Services enforce those capabilities before sending protocol requests.

This keeps the CLI from hard-coding assumptions about STM32, RP2040, Arduino, or future board families.

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
| [docs/trt-protocol.md](docs/trt-protocol.md) | Future TRT Protocol V1 specification |
| [docs/cli-reference.md](docs/cli-reference.md) | Command reference |
| [docs/future-protocol.md](docs/future-protocol.md) | Earlier protocol sketch |

---

## License

MIT - see [LICENSE](LICENSE).
