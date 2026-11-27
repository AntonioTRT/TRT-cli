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
- [src/trt/commands/listen.py](../src/trt/commands/listen.py)

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
- [src/trt/services/listen_service.py](../src/trt/services/listen_service.py)

Responsibilities:
- passive monitoring of asynchronous board messages (`ListenService`)
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
- [src/trt/transport/frame_reader.py](../src/trt/transport/frame_reader.py)

Responsibilities:
- `FrameReader` is a resynchronising TRT frame parser used to read unsolicited frames from a byte stream
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

### Implemented today (Version 1.0.0 milestone, 2026-11-26)

- Typer CLI with Rich output; three help levels (`trt`, `trt --help`, `trt help`)
- real serial discovery over all COM ports (TRT V0.1 frames), validated on STM32 and Arduino Uno
- board queries (`board_query_service.py`), including HWID (`0x000B`) and ACTIVE_MODE (`0x000A`)
- one board status summary shared by `boards`, `discover`, `board info` and `board update`
  (`board_summary.py`, rendered by `commands/board_view.py`; mode and HWID rules in `core/modes.py`)
- HWID-driven firmware update (`board_update_service.py`) on top of the STM32 build and flash
  commands (`commands/build.py`, `commands/flash.py`)
- passive monitoring: `trt listen` and `trt board listen <address>` (heartbeat events)
- mock transport and the simulated LCD / LED / peripheral commands, kept as test and support
  infrastructure and hidden from the help screens

### Planned for the future

- expanded `trt-protocol` repo implementation
- USB CDC transport implementation
- CAN transport
- TCP transport
- broader firmware capability coverage

Discovery, queries, the status view and the update workflow use real TRT protocol frames; they were validated end to end on an STM32 NUCLEO-L073RZ.

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

## Asynchronous events and heartbeat

TRT-Core boards emit a HEARTBEAT event (FLAGS `0x02`, COMMAND `0x9001`) about once per second. It is a runtime presence indicator and does not replace discovery.

Handling is passive and sits beside the request/response path:

```text
trt listen / trt board listen <address>
    -> commands/listen.py            (arguments, output: "Board <address>: HEARTBEAT")
        -> ListenService             (opens serial ports, one reader thread per port, board filter)
            -> FrameReader           (resynchronising frame parser)
                -> serial port
```

- `listen` never sends frames. It does not use `ProtocolClient`.
- `SerialTransport.exchange_command` skips event frames while waiting for a reply, so heartbeats do not corrupt discovery, `board info` or `board capabilities`.
- Event frames other than heartbeat are printed as `EVENT 0x<id> payload=<hex>`.

See [cli-reference.md](cli-reference.md#trt-listen) for usage.

Request/response synchronisation (`SerialTransport.exchange_command`): each attempt waits up to the
serial timeout for the reply whose sequence ID matches the request, skipping event frames and stale
replies. If the board sent frames but not the reply (request lost to a heartbeat collision), the
request is sent again, up to `retries` (default 2) more times; a silent port fails after one attempt so
discovery stays fast. Only read-only queries use this path, so repeating a request is safe.

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
- real peripheral commands (GPIO, PWM, ADC, DAC, I2C, SPI, LCD, LED) once the firmware supports them
- `trt board update` for Arduino and ESP32 (today STM32 over SWD only)
- GitHub release checking in `trt update`


---

## Repository Map

```
TRT-cli/           This repository (host CLI)
TRT-core/          Firmware runtime, board runtimes, STM32 mode project, protocol V0.1 docs
trt_docs/          Onboarding documentation (Spanish) and system deliverables
```

## Protocol Specification

The implemented protocol is **TRT V0.1**, specified in TRT-core (`docs/protocol-v0.1-wire-format.md`,
`docs/command-identifiers.md`). [design/trt-protocol-v1.md](design/trt-protocol-v1.md) is an earlier, broader design
document (V1); it shares the frame layout but its command set and CLI examples are not the implemented ones.

Key facts:
- Frame: `SYNC | VERSION | FLAGS | BOARD_ID | SEQ_ID | COMMAND | LENGTH | PAYLOAD | CRC16`
- Transport-agnostic: same frame over USB CDC, CAN FD, TCP/IP
- Implemented transport: serial (USB CDC / ST-LINK virtual COM port), 115200 baud
- CRC16 field present but sent as 0x0000 and not validated (V0.1)
- `archive/future-protocol.md` is a superseded sketch of an earlier frame format

See [design/vision.md](design/vision.md) for the long-term direction.
