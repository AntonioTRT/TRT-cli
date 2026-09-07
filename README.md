# TRT — Tool Runtime Terminal

> A board-agnostic embedded hardware control ecosystem built around a Python CLI, an application service layer, protocol abstractions, and a future transport abstraction.

TRT provides a unified, git-style command-line interface for controlling embedded boards across Windows, Linux, and macOS. The project is intentionally designed around capability-driven operation rather than board-family-specific logic.

---

## Mission

TRT is a command surface for embedded hardware that behaves like normal developer tooling: one interface, one model, and board-agnostic operation.

The repository now separates concerns into a layered architecture:

CLI Layer
    ↓
Application Services
    ↓
Protocol Layer
    ↓
Transport Layer
    ↓
Mock Device Layer

This keeps the user-facing interface stable while separating hardware concerns from presentation concerns.

---

## Current status

The repository currently sits in a staged architecture state:

| Area | Status |
|---|---|
| Typer CLI and Rich UI | ✅ Implemented |
| Domain models | ✅ Implemented |
| Services layer | ✅ Implemented |
| Protocol abstractions | ✅ Implemented as mock abstractions |
| Transport abstractions | ✅ Implemented as mock transport interface |
| Real USB/CAN/TCP communication | 🔜 Future |
| Real TRT Protocol implementation | 🔜 Future |
| Firmware ecosystem integration | 🔜 Future |

---

## Installation

```bash
git clone https://github.com/trt-project/trt-cli.git
cd trt-cli
pip install -e .
```

Requires Python 3.13 or later.

---

## Quick start

```bash
trt help
trt version
trt update
trt boards
trt discover

trt board board0 info
trt board board0 capabilities
trt board board0 gpio list
trt board board0 gpio write PA5 1
trt board board0 pwm set 1 1000 50
trt board board0 adc read 3
trt board board0 i2c scan

trt lcd write "Hello"
trt led color 255 0 0
trt protocol info
```

The CLI behavior remains unchanged for users, even though the implementation has been reorganized behind application services and protocol abstractions.

---

## Architectural direction

### Current implementation

The current codebase includes a real layered intent while preserving mock behavior:

- CLI layer: command parsing and Rich rendering
- Service layer: board lookup, capability checks, mock device orchestration
- Protocol layer: `ProtocolRequest`, `ProtocolResponse`, `ProtocolClient`, `MockProtocolClient`
- Transport layer: `Transport` interface and `MockTransport`
- Domain model: `Board`, `BoardCapabilities`, `BoardRegistry`, `TransportConfig`

### Future vision

The long-term plan remains consistent with the original TRT ecosystem design:

```text
trt-cli                -> CLI + application services
trt-protocol           -> protocol specification and real client implementation
trt-core               -> firmware library for TRT-compatible boards
trt-modules            -> hardware module drivers
```

---

## Project structure

```text
trt-cli/
├── src/trt/
│   ├── cli.py                     # Typer command registration
│   ├── __main__.py                # python -m trt entry point
│   ├── version.py                 # version metadata
│   ├── commands/
│   │   ├── board.py               # board command tree
│   │   ├── boards.py              # list known boards
│   │   ├── discover.py            # discovery orchestration
│   │   ├── help.py                # help rendering
│   │   ├── lcd.py                 # LCD command group
│   │   ├── led.py                 # LED command group
│   │   ├── protocol.py            # protocol info commands
│   │   ├── update.py              # CLI update orchestration
│   │   └── version.py             # version command
│   ├── core/
│   │   └── models.py              # domain model
│   ├── protocol/
│   │   ├── __init__.py            # protocol abstractions package
│   │   ├── models.py              # ProtocolRequest / ProtocolResponse
│   │   └── protocol_client.py     # ProtocolClient / MockProtocolClient
│   ├── repositories/
│   │   ├── __init__.py            # repository package
│   │   └── board_repository.py    # BoardRepository
│   ├── services/
│   │   ├── __init__.py            # service exports
│   │   ├── board_service.py       # board business logic
│   │   ├── board_discovery_service.py
│   │   ├── capability_service.py  # capability enforcement
│   │   └── update_service.py      # update check/install logic
│   ├── transport/
│   │   ├── __init__.py            # transport package
│   │   ├── base.py                # Transport interface
│   │   └── mock_transport.py      # mock transport implementation
│   └── version.py
├── docs/
│   ├── architecture.md
│   ├── vision.md
│   ├── cli-reference.md
│   ├── future-protocol.md
│   └── trt-protocol.md
├── tests/
│   └── test_cli.py
├── pyproject.toml
├── LICENSE
├── QUICKSTART.md
├── README.md
└── docs/architecture.md
```

---

## Capability-driven design

TRT intentionally avoids board-family-specific logic. The design principle is:

- the CLI exposes a consistent command surface
- the board advertises capabilities
- runtime behavior is gated by those capabilities

This is implemented in the domain model and service layer through `BoardCapabilities.has()` and `CapabilityService.supports()`.

The project avoids using board-type checks such as `if board.family == "STM32"` in command logic. That remains the intended design direction.

---

## Protocol and transport architecture

The repository now includes real protocol and transport abstraction boundaries, even though both are backed by mock implementations for the current phase.

Layer responsibilities:

- CLI: parse arguments and render output
- Services: coordinate board operations and enforce business rules
- Protocol: encode request/response semantics
- Transport: send requests across a concrete transport implementation
- Mock Device: simulate hardware without real device communication

This structure allows future real USB, CAN, and TCP implementations to plug into the same interface without changing the CLI contract.

---

## Migration readiness

The new architecture improves maintainability and future migration in several ways:

1. Business logic is no longer stuck inside Typer handlers.
2. Domain operations are exposed through reusable services.
3. Protocol serialization and command semantics are separated from the interface layer.
4. Transport behavior is abstracted behind an interface.
5. The architecture is more portable to Go, because the core domain and service contracts can be reimplemented cleanly in another language.

---

## License

MIT — see [LICENSE](LICENSE).
