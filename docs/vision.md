# TRT Vision

## Mission

> *TRT is a modular hardware control ecosystem for embedded boards and expansion modules.*

TRT makes controlling embedded hardware as natural as using `git` or `docker`.  A single command — `trt` — should work uniformly regardless of:

- Which board is connected (TRT_CORE, Arduino, RP2040, future custom boards)
- Which operating system the developer is on (Windows, Linux, macOS)
- Which transport is in use (USB today; CAN and TCP in future releases)

---

## The Problem TRT Solves

Today, working with embedded hardware typically requires:

- Vendor-specific GUIs (STM32CubeIDE, Arduino IDE, Thonny)
- Custom Python scripts with direct serial access
- Board-specific one-off terminal tools
- Different workflows for different boards

None of these tools compose, none are scriptable, and none share a common model.

TRT is the unified alternative.

---

## Design Goals

### 1. Unified CLI
One command, one mental model.  `trt board board0 gpio write PA5 1` works the same whether `board0` is a TRT_CORE, an Arduino, or a simulator.

### 2. Capability-based, not MCU-based
Boards advertise what they can do.  The CLI adapts to capabilities.  There is no `--stm32` flag.

### 3. Extensible without restructuring
Adding a new board type, transport, or command never requires reorganising the codebase.  Every layer has clear extension points.

### 4. Scriptable and automatable
`trt` commands produce clean output suitable for shell scripting, CI pipelines, and test automation.

### 5. Cross-platform
Full feature parity on Windows, Linux, and macOS.

---

## Supported Boards (Current and Planned)

| Board Type    | Status  | Notes                                  |
|---------------|---------|----------------------------------------|
| TRT_CORE      | Planned | Reference TRT board                    |
| Arduino       | Planned | Arduino-compatible boards              |
| RP2040        | Planned | Raspberry Pi RP2040-based boards       |
| Simulator     | Planned | Software simulator, no hardware needed |
| Custom        | Planned | Any board implementing TRT Protocol    |

---

## Supported Transports (Current and Planned)

| Transport | Status  | Notes                     |
|-----------|---------|---------------------------|
| USB       | Planned | USB CDC (milestone 2)     |
| CAN       | Future  | CAN bus, multi-device     |
| TCP       | Future  | Ethernet / network boards |
| Simulator | Future  | In-process simulation     |

---

## Roadmap

### Milestone 1 — CLI Foundation (0.1.0) ✅
- Clean repository structure
- Full command tree scaffolded
- Rich terminal output
- Board models (capability-based)
- Mock board data
- Architecture and documentation

### Milestone 2 — USB Transport (0.2.0)
- TRT Protocol specification (trt-protocol)
- USB CDC transport implementation
- Real board discovery via USB
- Board capability handshake
- GPIO read/write over USB

### Milestone 3 — Full Hardware Abstraction (0.3.0)
- PWM, ADC, DAC over TRT Protocol
- I2C and SPI master operations
- LCD and LED peripheral support
- Debug shell over USB

### Milestone 4 — Extended Transports (0.4.0)
- CAN bus transport
- TCP/Ethernet transport
- Multi-board sessions

### Milestone 5 — Ecosystem (1.0.0)
- Stable TRT Protocol v1.0
- trt-core firmware library (C/C++)
- trt-modules driver collection
- Plugin / extension API

---

## Related Repositories (Future)

| Repository      | Purpose                                                    |
|-----------------|------------------------------------------------------------|
| `trt-cli`       | This repository — CLI frontend                             |
| `trt-protocol`  | Binary communication protocol specification + Python impl  |
| `trt-core`      | C/C++ firmware library for TRT-compatible boards           |
| `trt-modules`   | Firmware module drivers (GPIO, PWM, I2C, SPI, LCD, LED)    |
