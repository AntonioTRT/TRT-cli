# TRT Architecture

## System overview

```text
Developer / User
      |
      | trt <command>
      v
┌────────────────────────────────────────────────────────────┐
│                       CLI Layer                             │
│  Typer app, command registration, Rich output, UX         │
│  src/trt/cli.py + src/trt/commands/*.py                  │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               v
┌────────────────────────────────────────────────────────────┐
│                Application Services Layer                   │
│  BoardService, BoardDiscoveryService, CapabilityService,   │
│  LCDService, LEDService                                    │
│  src/trt/services/*.py                                     │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               v
┌────────────────────────────────────────────────────────────┐
│                     Protocol Layer                          │
│  ProtocolOperation, typed requests/responses,              │
│  ProtocolClient, SerialProtocolClient, MockProtocolClient  │
│  src/trt/protocol/*.py                                     │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               v
┌────────────────────────────────────────────────────────────┐
│                    Transport Layer                          │
│  Transport interface, SerialTransport, MockTransport       │
│  src/trt/transport/*.py                                    │
└──────────────────────────────┬─────────────────────────────┘
                               │
                               v
┌────────────────────────────────────────────────────────────┐
│                      Device Layer                           │
│  Arduino Uno running TRT-Core firmware, plus explicit       │
│  mock transport support for tests                           │
└────────────────────────────────────────────────────────────┘
```

This architecture is now used for both real serial communication and explicit mock-backed tests.

---

## Layer responsibilities

### CLI Layer

Files:
- [src/trt/cli.py](../src/trt/cli.py)
- [src/trt/commands/board.py](../src/trt/commands/board.py)
- [src/trt/commands/boards.py](../src/trt/commands/boards.py)
- [src/trt/commands/discover.py](../src/trt/commands/discover.py)
- [src/trt/commands/lcd.py](../src/trt/commands/lcd.py)
- [src/trt/commands/led.py](../src/trt/commands/led.py)

Responsibilities:
- parse command-line arguments
- invoke services
- format console output
- preserve the existing user experience

This layer does not construct board registries, generate mock responses, create fake hardware values, or simulate board state. Command handlers parse arguments, call services, and render returned values.

### Application Services Layer

Files:
- [src/trt/services/board_service.py](../src/trt/services/board_service.py)
- [src/trt/services/board_discovery_service.py](../src/trt/services/board_discovery_service.py)
- [src/trt/services/capability_service.py](../src/trt/services/capability_service.py)
- [src/trt/services/lcd_service.py](../src/trt/services/lcd_service.py)
- [src/trt/services/led_service.py](../src/trt/services/led_service.py)
- [src/trt/services/update_service.py](../src/trt/services/update_service.py)

Responsibilities:
- board lookup and state coordination
- capability enforcement
- discovery orchestration
- LCD and LED operation orchestration
- update checking/install preparation

This is the place where business logic belongs in the current project structure.

### Protocol Layer

Files:
- [src/trt/protocol/models.py](../src/trt/protocol/models.py)
- [src/trt/protocol/protocol_client.py](../src/trt/protocol/protocol_client.py)
- [src/trt/protocol/serial_protocol_client.py](../src/trt/protocol/serial_protocol_client.py)

Responsibilities:
- define protocol request/response objects
- hide transport choices from the service layer
- provide serial and mock protocol clients

The current implementation is transport-independent and designed so serial, USB, CAN, TCP, and mock adapters can implement the same interface without changing service logic.

### Transport Layer

Files:
- [src/trt/transport/base.py](../src/trt/transport/base.py)
- [src/trt/transport/serial_transport.py](../src/trt/transport/serial_transport.py)
- [src/trt/transport/mock_transport.py](../src/trt/transport/mock_transport.py)

Responsibilities:
- send protocol requests over a concrete transport
- isolate the protocol layer from runtime transport concerns
- enumerate serial ports and exchange TRT frames over COM ports
- define extension points for USB/CAN/TCP transports

### Domain Layer

File:
- [src/trt/core/models.py](../src/trt/core/models.py)

Responsibilities:
- typed board and capability model definitions
- board registry state
- transport and capability metadata

The domain layer remains framework-independent and portable.

---

## Current state vs future state

### Implemented today

- Typer CLI with rich output
- thin command adapters for board, discovery, LCD, and LED commands
- board service layer
- LED and LCD service layers
- typed protocol operation, request, and response models
- protocol client abstraction
- real serial discovery over available COM ports
- real `trt board info 101` transaction over COM4
- mock transport retained as explicit test/support infrastructure
- capability service

### Planned for the future

- expanded `trt-protocol` repo implementation
- USB CDC transport implementation
- CAN transport
- TCP transport
- broader firmware capability coverage

TRT-CLI 1.0.0 is no longer mock-only: board discovery and numeric board info can use real TRT protocol frames against Arduino Uno firmware.

---

## Dependency flow

```text
CLI
      -> BoardService / DiscoveryService / CapabilityService / LCDService / LEDService
          -> ProtocolClient
              -> SerialTransport / MockTransport
                  -> TRT-Core firmware / explicit test double
```

Dependency direction rules now follow the intended architecture:

- CLI depends on services and renders returned data
- Services depend on protocol and repository abstractions
- Protocol depends on transport abstractions
- SerialTransport exchanges real TRT frames over COM ports
- MockTransport generates simulated device responses only when explicitly injected
- Transport does not depend on CLI or services
- Domain models remain independent

This is the key improvement that makes the project more maintainable and more migration-friendly.

---

## Capability-driven design

The domain and service layers enforce the capability-driven design principle.

Examples:

- `BoardCapabilities.has()` in [src/trt/core/models.py](../src/trt/core/models.py)
- `CapabilityService.supports()` in [src/trt/services/capability_service.py](../src/trt/services/capability_service.py)
- `BoardService.ensure_capability()` in [src/trt/services/board_service.py](../src/trt/services/board_service.py)

This keeps the CLI from hard-coding board family assumptions such as STM32, RP2040, or Arduino checks in the command layer.

---

## Protocol abstraction

The protocol layer intentionally describes the data contract independent of hardware transport.

Key abstractions:

- `ProtocolOperation`: enum-backed operation identifiers
- typed request dataclasses such as `DiscoverRequest`, `GpioReadRequest`, and `GpioWriteRequest`
- typed response dataclasses such as `DiscoverResponse`, `GpioReadResponse`, and `GetCapabilitiesResponse`
- `ProtocolClient`: abstract interface for sending protocol requests
- `SerialProtocolClient`: current real serial implementation for TRT-Core firmware
- `MockProtocolClient`: explicit mock implementation for tests and support paths

Services now construct typed request objects instead of raw operation strings and unstructured request payload dictionaries. Transports return typed response objects, and services project them into CLI-facing result DTOs for rendering.

This allows future real implementations to plug into the same service layer without changing CLI behavior.

---

## Transport abstraction

The transport layer now defines the future extension points.

Key abstractions:

- `Transport`: abstract interface
- `SerialTransport`: current real COM-port transport used for Arduino Uno TRT-Core communication
- `MockTransport`: explicit test/support transport

Planned future implementations:

- `USBTransport`
- `CANTransport`
- `TCPTransport`

The important architectural point is that the protocol layer depends on the transport interface, not on a specific transport backend. `SerialTransport` performs real frame exchange; `MockTransport` remains available only for explicit test/support use.

---

## Migration readiness

The new architecture improves maintainability and future migration for several reasons:

1. CLI concerns are separated from business logic.
2. Domain and service contracts are more explicit.
3. Protocol semantics are captured as models rather than hidden in command handlers.
4. Transport-specific code is isolated behind an interface.
5. The code is easier to reimplement in other languages such as Go without rewriting the command surface.

---

## Remaining future work

The following remain outside the current 1.0.0 hardware-validated slice:

- real CAN and TCP transport adapters
- full USB CDC implementation beyond current COM-port serial transport
- full command coverage beyond discovery, board info, firmware version, build ID, and capabilities

These do not change the 1.0.0 milestone: TRT-CLI has a validated end-to-end Arduino Uno protocol transaction.


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
