# TRT Vision

## Mission

TRT provides a unified command surface for embedded hardware control. The project exists to make hardware interaction feel as ordinary as using developer tools such as `git`, `docker`, or `kubectl`.

The repository is intentionally designed around a layered architecture:

CLI Layer
    ↓
Application Services
    ↓
Protocol Layer
    ↓
Transport Layer
    ↓
Device Layer

This architecture helps TRT remain board-agnostic, capability-driven, and ready for future protocol and transport implementations.

---

## The problem TRT solves

Embedded engineers usually face a fragmented toolchain:

- vendor-specific IDEs and GUIs
- board-specific scripts
- direct serial handling in custom tools
- mixed hardware interfaces across different devices

TRT aims to replace that with a single consistent interface that continues to work across board types and communication methods.

---

## Design goals

### 1. Unified CLI
One command surface, one mental model, and consistent behavior across hardware.

### 2. Capability-driven design
Boards will advertise support for GPIO, PWM, ADC, DAC, I2C, SPI, and similar capabilities. The command layer should not hard-code board families or silicon assumptions.

### 3. Protocol abstraction
The service layer should not know whether a device is reached over USB, CAN, or TCP. The protocol client should provide a consistent request/response abstraction.

### 4. Transport abstraction
The transport layer is intentionally designed to be replaceable. Future USB, CAN, and TCP adapters should be compatible with the same protocol client interface.

### 5. Testability and portability
The architecture separates CLI rendering, service orchestration, and mock transport behavior so the project remains easier to test, reason about, and port to another language in the future.

---

## Current implementation status

The repo currently delivers the foundation of that vision:

- command layer exists
- board and capability domain models exist
- service layer exists
- protocol request/response abstractions exist
- mock transport implementation exists

The remaining parts are intentionally deferred and remain future work:

- real board discovery
- real protocol framing
- real hardware communication
- real USB/CAN/TCP layers

---

## Supported boards and transports

### Boards

| Board Type | Status | Notes |
|---|---|---|
| TRT_CORE | Planned | Reference TRT board |
| Arduino | Planned | Arduino-compatible boards |
| RP2040 | Planned | Common embedded target |
| Simulator | Planned | Mock in-process device |
| Custom | Planned | Any board implementing the TRT protocol |

### Transports

| Transport | Status | Notes |
|---|---|---|
| USB | Planned | Future USB CDC transport |
| CAN | Planned | Future CAN bus support |
| TCP | Planned | Future Ethernet transport |
| Mock | Implemented | Current CLI behavior |

---

## Long-term roadmap

### Milestone 1 — CLI foundation ✅
- CLI scaffold and command structure
- Rich help and output
- typed domain model
- mock board registry
- service layer and protocol abstractions

### Milestone 2 — Real protocol client
- implement real protocol request/response flow
- expand protocol model definitions
- begin board capability negotiation

### Milestone 3 — Real transport adapters
- USB transport implementation
- CAN transport implementation
- TCP transport implementation

### Milestone 4 — Hardware ecosystem integration
- actual device discovery
- capability-driven command execution
- board firmware integration

### Milestone 5 — System maturity
- stable protocol version
- shared firmware ecosystem
- reusable module and driver libraries

---

## Why the architecture matters

The project is intentionally designed so that the user-facing command syntax stays stable even as the lower layers evolve. That allows the repository to preserve a consistent CLI while implementing the real protocol and transport layers later.

The architecture also improves maintainability by separating concerns in a way that supports future migration to Go or another language without rewriting the command semantics from scratch.

---

## Related repositories (future)

| Repository | Purpose |
|---|---|
| trt-cli | CLI frontend and service orchestration |
| trt-protocol | binary protocol specification and real protocol implementation |
| trt-core | firmware library for TRT-compatible boards |
| trt-modules | firmware module drivers and board capabilities |
