# TRT Protocol V1 — Specification

> **Status: Architecture Definition — No implementation yet.**
> This document is the single source of truth for all future TRT Protocol development.
> Commands, transport drivers, and firmware libraries will be built against this specification.

---

## Table of Contents

1. [Mission](#1-mission)
2. [Design Goals](#2-design-goals)
3. [Capability-Driven Architecture](#3-capability-driven-architecture)
4. [Frame Structure](#4-frame-structure)
5. [Field Definitions](#5-field-definitions)
6. [Example Frame](#6-example-frame)
7. [Response Types](#7-response-types)
8. [Error Model](#8-error-model)
9. [Command Categories](#9-command-categories)
10. [Debug Verbosity Levels](#10-debug-verbosity-levels)
11. [Long Payload Support](#11-long-payload-support)
12. [Chunked Transfers](#12-chunked-transfers)
13. [Board Identity](#13-board-identity)
14. [Modules](#14-modules)
15. [Transport Strategy](#15-transport-strategy)
16. [Versioning and Compatibility](#16-versioning-and-compatibility)
17. [Security Considerations](#17-security-considerations)
18. [Open Questions](#18-open-questions)
19. [Design Decisions Log](#19-design-decisions-log)

---

## 1. Mission

**TRT Protocol** is a transport-independent binary communication protocol for the TRT ecosystem.

Its primary purpose is to allow `trt-cli` (running on a developer's machine) to communicate reliably with TRT-compatible embedded boards regardless of the physical connection medium.

```
trt-cli
  │
  │  TRT Protocol frames (binary)
  │
  ├── USB CDC      (V1)
  ├── CAN FD       (V2)
  └── TCP/IP       (V3)
```

**The protocol frame format is fixed and transport-agnostic.**
Only the transport layer changes between physical media.
A frame transmitted over USB is byte-for-byte identical to one sent over TCP.

---

## 2. Design Goals

| Goal | Description |
|---|---|
| **Binary** | All frames are binary. No text encoding overhead. |
| **Compact** | Minimal header overhead relative to payload size. |
| **MCU-friendly** | Easy to implement on STM32 and similar microcontrollers with limited RAM. |
| **Debuggable** | Frames can be visualised in human-readable hex format via debug flags. |
| **Multi-board** | A single host connection can address multiple boards simultaneously. |
| **Sequenced** | Every request carries a sequence ID for response matching and retransmission. |
| **Long payload** | Supports payloads of any size via chunked transfer. |
| **Firmware-update capable** | Chunked transfer design accommodates firmware image delivery. |
| **Forward compatible** | VERSION field and FLAGS field allow future protocol extensions without breaking V1 clients. |
| **Event-ready** | FLAGS field reserves space for future asynchronous event packets. |
| **Capability-driven** | Boards decide what they support; the CLI never hardcodes board-specific restrictions. |

---

## 3. Capability-Driven Architecture

### 3.1 Core Principle

> **The CLI defines the command syntax. The board decides whether it can execute it.**

TRT is intentionally generic. The CLI presents the same command surface regardless of what type of board is connected. Capability decisions — whether a board can execute `dac read`, `spi transfer`, or any other command — are made by the board's firmware at runtime, not by `trt-cli` at the source-code level.

This principle enables TRT to support fundamentally different hardware without changing the CLI:

| Board | Capabilities |
|---|---|
| TRT Core (STM32) | GPIO, PWM, ADC, DAC, I2C, SPI, Debug shell |
| Arduino-compatible | GPIO, PWM, ADC |
| RP2040-based | GPIO, PWM, ADC, I2C, SPI |
| Simulator | SYSTEM only |
| Future custom board | Any declared subset |

### 3.2 Command Execution Flow

```
User executes:
    trt board board1 dac read 1

                        │
        trt-cli builds TRT Protocol frame
        COMMAND = CMD_DAC_READ, BOARD_ID = 0x0002
                        │
                        ▼
        Frame transmitted to board1
                        │
             ┌──────────┴──────────┐
             │                     │
       Board supports DAC     Board does NOT support DAC
             │                     │
             ▼                     ▼
          DATA response         NACK response
          payload: raw value    error: ERROR_UNSUPPORTED_COMMAND
             │                     │
             ▼                     ▼
    trt-cli displays:       trt-cli displays:
    "Channel 1: 1.65V"      "board1: command not supported"
```

### 3.3 Supported Command (Example)

```
$ trt board board1 dac read 1

  board1  dac read  ch=1  →  1.65V  (raw: 2048)
```

### 3.4 Unsupported Command (Example)

```
$ trt board board1 dac read 1

  board1: NACK — ERROR_UNSUPPORTED_COMMAND
  Board does not advertise DAC capability.
  Run 'trt board capabilities board1' to see what this board supports.
```

### 3.5 Capability Advertisement

Every TRT board exposes a capabilities response via `CMD_CAPABILITIES`.  `trt-cli` can optionally pre-check capabilities before issuing a command, but this is a convenience — the authoritative enforcement happens on the board.

```json
{
  "gpio":        true,
  "pwm":         true,
  "adc":         true,
  "dac":         false,
  "i2c":         true,
  "spi":         false,
  "uart":        false,
  "can":         false,
  "lcd":         false,
  "relay":       false,
  "debug_shell": false
}
```

### 3.6 CLI Design Rule

`trt board board1 dac read 1` is **always valid CLI syntax**.

The CLI never refuses to send a command based on locally cached capability data.  If a user wants to try a command on a board, `trt-cli` will send it and display whatever the board responds with.  This eliminates the need to keep CLI behaviour synchronised with board firmware capabilities.

---

## 4. Frame Structure

```
 Offset   Size    Field
 ──────   ────    ──────────────────────────────────────────────
  0       2       SYNC        Frame start marker
  2       1       VERSION     Protocol version
  3       1       FLAGS       Packet options
  4       2       BOARD_ID    Target board logical address
  6       2       SEQ_ID      Sequence identifier
  8       2       COMMAND     Operation code
 10       2       LENGTH      Payload length in bytes
 12       N       PAYLOAD     Variable-length payload
 12+N     2       CRC16       Frame integrity checksum
 ──────   ────    ──────────────────────────────────────────────
```

**Minimum frame size (no payload):** 14 bytes  
**Maximum payload size:** 65 535 bytes (LENGTH is 2 bytes, unsigned)

### Visual Representation

```
┌────────┬─────────┬───────┬──────────┬────────┬─────────┬────────┬─────────────┬───────┐
│ SYNC   │ VERSION │ FLAGS │ BOARD_ID │ SEQ_ID │ COMMAND │ LENGTH │   PAYLOAD   │ CRC16 │
│ 2 B    │ 1 B     │ 1 B   │ 2 B      │ 2 B    │ 2 B     │ 2 B    │   N bytes   │ 2 B   │
└────────┴─────────┴───────┴──────────┴────────┴─────────┴────────┴─────────────┴───────┘
```

**Byte order:** Little-endian throughout (consistent with STM32 native byte order).

---

## 5. Field Definitions

### 4.1 SYNC — `0xAA55`

| Attribute | Value |
|---|---|
| Size | 2 bytes |
| Value | `0xAA` `0x55` |
| Purpose | Frame synchronisation |

The SYNC marker allows the receiver to scan an incoming byte stream and locate frame boundaries.  This is important on byte-oriented transports (UART, RS485) where framing is not guaranteed.

On packet-oriented transports (USB CDC bulk, TCP), SYNC still provides an additional layer of sanity checking.

**Byte order:**  `0xAA` transmitted first, `0x55` second.

---

### 4.2 VERSION — `0x01`

| Attribute | Value |
|---|---|
| Size | 1 byte |
| Initial value | `0x01` |
| Purpose | Protocol version for compatibility negotiation |

A device running protocol V1 must:
- Accept and process frames with VERSION `0x01`
- Respond to version-mismatch frames with a NACK containing error code `PROTOCOL_VERSION_MISMATCH`

Future versions increment this field.  Minor non-breaking additions do not require a version bump.  Breaking structural changes do.

---

### 4.3 FLAGS — `0x00`

| Attribute | Value |
|---|---|
| Size | 1 byte |
| V1 initial value | `0x00` |
| Purpose | Per-packet options bitmask |

FLAGS is reserved for future packet-type modifiers.  In V1 all flags are zero.

**Planned flag bits (not implemented in V1):**

| Bit | Name | Description |
|---|---|---|
| 0 | `RESPONSE` | This frame is a response to a request |
| 1 | `EVENT` | Unsolicited asynchronous event from device |
| 2 | `BROADCAST` | Frame addressed to all boards |
| 3 | `DEBUG` | Frame carries debug/diagnostic payload |
| 4 | `CHUNKED` | This frame is part of a chunked transfer |
| 5 | `CHUNK_FIRST` | First chunk of a multi-packet transfer |
| 6 | `CHUNK_LAST` | Last chunk of a multi-packet transfer |
| 7 | *Reserved* | Reserved for future use |

---

### 4.4 BOARD_ID

| Attribute | Value |
|---|---|
| Size | 2 bytes |
| Range | `0x0001` – `0xFFFF` |
| Purpose | Logical target board address |

BOARD_ID allows a single host connection to address multiple boards.

The user interacts with logical names:

```
board0  →  BOARD_ID 0x0001
board1  →  BOARD_ID 0x0002
board2  →  BOARD_ID 0x0003
```

The mapping between logical names and BOARD_IDs is maintained by `trt-cli`'s `BoardRegistry`.

**Special values:**

| Value | Meaning |
|---|---|
| `0x0000` | Broadcast — all boards (FLAGS `BROADCAST` must also be set) |
| `0x0001` | First connected board (default when only one is present) |
| `0xFFFF` | Reserved |

---

### 4.5 SEQ_ID

| Attribute | Value |
|---|---|
| Size | 2 bytes |
| Range | `0x0000` – `0xFFFF` (wraps around) |
| Purpose | Request / response matching, retransmission, chunked transfer coordination |

Every request from `trt-cli` carries a unique SEQ_ID.  The responding device echoes the same SEQ_ID in its response frame.  This allows:

- **Matching** — correlate responses to the correct request
- **Retransmission** — detect lost responses and resend
- **Chunked transfers** — identify which chunk a response acknowledges
- **Firmware updates** — track progress across many packets

SEQ_ID wraps from `0xFFFF` back to `0x0000`.

---

### 4.6 COMMAND

| Attribute | Value |
|---|---|
| Size | 2 bytes |
| Purpose | Identifies the operation being requested |

COMMAND is a 2-byte opcode identifying what action the frame requests or what data it carries.

> **Command values are not defined in this document.**
> The command table will be specified in a separate companion document: `docs/trt-commands.md`.

The 2-byte width provides 65 536 possible opcodes, partitioned into groups:

| Range | Reserved for |
|---|---|
| `0x0000` – `0x00FF` | System / session management |
| `0x0100` – `0x01FF` | GPIO |
| `0x0200` – `0x02FF` | PWM |
| `0x0300` – `0x03FF` | ADC |
| `0x0400` – `0x04FF` | DAC |
| `0x0500` – `0x05FF` | I2C |
| `0x0600` – `0x06FF` | SPI |
| `0x0700` – `0x07FF` | UART |
| `0x0800` – `0x08FF` | CAN |
| `0x0900` – `0x09FF` | LCD |
| `0x0A00` – `0x0AFF` | LED |
| `0x0B00` – `0x0BFF` | Relay |
| `0x0C00` – `0x0CFF` | Debug / diagnostics |
| `0x0D00` – `0x0DFF` | Firmware update |
| `0x0E00` – `0x0FFF` | Reserved |
| `0x1000` – `0xEFFF` | Module expansion |
| `0xF000` – `0xFFFE` | Vendor / custom |
| `0xFFFF` | Error / NACK |

---

### 4.7 LENGTH

| Attribute | Value |
|---|---|
| Size | 2 bytes |
| Range | `0x0000` – `0xFFFF` |
| Purpose | Number of bytes in PAYLOAD |

LENGTH = 0 is valid (no payload).  The CRC16 still covers the header.

The receiver must allocate or stream exactly LENGTH bytes before reading CRC16.

---

### 4.8 PAYLOAD

| Attribute | Value |
|---|---|
| Size | 0 – 65 535 bytes |
| Encoding | Command-specific binary format |

Payload encoding is defined per command in the command table.  Examples of payload content:

- Pin number (1 byte) + value (1 byte)
- ADC channel (1 byte) → response: raw count (2 bytes) + millivolt value (2 bytes)
- Board info response: type string, revision, firmware version, serial (length-prefixed strings)
- Firmware chunk: chunk index (2 bytes) + data (up to 4 KB per chunk)
- LCD write: line (1 byte) + column (1 byte) + UTF-8 string (N bytes)

---

### 4.9 CRC16

| Attribute | Value |
|---|---|
| Size | 2 bytes |
| Coverage | Bytes 0 through (12 + LENGTH − 1), i.e. the entire frame except CRC itself |
| Purpose | Frame integrity verification |

> **The specific CRC16 polynomial is an open question.** See [Section 15](#15-open-questions).
> Candidates: CRC-16/CCITT (polynomial `0x1021`), CRC-16/MODBUS (polynomial `0x8005`).

The receiver computes CRC16 over the received bytes and compares it to the trailing CRC16 field.  A mismatch causes the frame to be discarded and a NACK to be sent (if the header was readable).

---

## 6. Example Frame

### Scenario

User executes:

```bash
trt board board1 version
```

`trt-cli` translates this into a TRT Protocol frame:

- `board1` maps to `BOARD_ID = 0x0002`
- `version` maps to `COMMAND = 0x0001` *(example value — not yet finalised)*
- No payload
- SEQ_ID = `0x0001` (first request in session)

### Frame Bytes

```
Offset  Bytes       Field       Value / Meaning
──────  ──────────  ──────────  ────────────────────────────────────────
 0      AA 55       SYNC        Frame start marker
 2      01          VERSION     Protocol version 1
 3      00          FLAGS       No flags (standard request)
 4      02 00       BOARD_ID    0x0002 = board1  (little-endian)
 6      01 00       SEQ_ID      0x0001 (little-endian)
 8      01 00       COMMAND     0x0001 = CMD_VERSION  (little-endian, example)
10      00 00       LENGTH      0 bytes payload
                   ─ PAYLOAD ─  (none)
12      XX XX       CRC16       Computed over bytes 0–11
```

### Hex Dump

```
AA 55 01 00 02 00 01 00 01 00 00 00 [CRC_LO] [CRC_HI]
```

### Response Frame (example)

The board responds with a DATA frame containing its version string:

```
AA 55 01 01 02 00 01 00 01 00 07 00 30 2E 31 2E 30 [CRC_LO] [CRC_HI]
                  ^                ^
                  FLAGS=0x01       COMMAND=CMD_VERSION_RESP
                  (RESPONSE bit)
                                              ─ PAYLOAD ─
                                              "0.1.0" = 30 2E 31 2E 30
                                              LENGTH = 7 (including null if used)
```

---

## 7. Response Types

Every frame sent by a board in response to a request falls into one of four types.  The type is signalled via the FLAGS field and, for NACK, via the COMMAND field.

### 7.1 ACK — Operation Successful

| Attribute | Value |
|---|---|
| FLAGS | `RESPONSE` bit set |
| COMMAND | Mirrors the request command |
| PAYLOAD | Empty (LENGTH = 0) or short confirmation |

The operation completed without error. No data is returned.

```
SYNC VERSION FLAGS(RESPONSE) BOARD_ID SEQ_ID COMMAND LENGTH(0) CRC16
```

**CLI display:**
```
$ trt board board1 reset

  board1: OK
```

---

### 7.2 NACK — Operation Failed

| Attribute | Value |
|---|---|
| FLAGS | `RESPONSE` bit set |
| COMMAND | `0xFFFF` (error sentinel) |
| PAYLOAD | 1-byte error code + optional UTF-8 message |

The operation could not be completed.  The error code identifies the reason (see [Section 8](#8-error-model)).

**CLI display — unsupported command:**
```
$ trt board board1 dac read 1

  board1: NACK — ERROR_UNSUPPORTED_COMMAND
  Board does not advertise DAC capability.
  Run 'trt board capabilities board1' to see what this board supports.
```

**CLI display — invalid argument:**
```
$ trt board board1 gpio read PX99

  board1: NACK — ERROR_INVALID_ARGUMENT
  Pin 'PX99' does not exist on this board.
```

---

### 7.3 DATA — Response Contains Data

| Attribute | Value |
|---|---|
| FLAGS | `RESPONSE` bit set |
| COMMAND | Mirrors the request command |
| PAYLOAD | Command-specific binary data |

The operation completed and the board is returning a result.

**Example — `CMD_ADC_READ` payload:**
```
Byte 0:    ADC channel number
Bytes 1-2: Raw ADC count (little-endian uint16)
Bytes 3-4: Millivolt value (little-endian uint16)
```

**CLI display:**
```
$ trt board board1 adc read 3

  board1  adc read  ch=3  →  1.65V  (raw: 2048)
```

---

### 7.4 EVENT — Asynchronous Notification *(Future — V2+)*

| Attribute | Value |
|---|---|
| FLAGS | `EVENT` bit set, `RESPONSE` bit clear |
| COMMAND | Event type opcode |
| PAYLOAD | Event-specific data |

An unsolicited frame sent by the board without a prior request.  The board assigns its own SEQ_ID (not echoed from any request).

> **Events are not part of V1.**  This section documents the reserved design space only.

**Planned event sources:**
- GPIO edge trigger (button press, limit switch)
- Alarm or fault condition
- Temperature threshold crossed
- Watchdog recovery notification
- Module connected / disconnected

**CLI display (future):**
```
[EVENT] board1: GPIO PA0 → RISING EDGE  (ts=0x0000A3F2)
```

---

## 8. Error Model

Error codes are carried in NACK response payloads.  They identify why a command failed without requiring the CLI to predict board behaviour.

> **Numeric values are not yet assigned.** This section defines the error taxonomy only.

### 8.1 Error Codes

| Name | When Used |
|---|---|
| `ERROR_UNKNOWN_COMMAND` | Command opcode is not recognised by firmware |
| `ERROR_UNSUPPORTED_COMMAND` | Opcode is known but the board does not support it (capability missing) |
| `ERROR_INVALID_ARGUMENT` | A payload field is out of range, malformed, or references a non-existent resource |
| `ERROR_INVALID_BOARD` | BOARD_ID does not match any connected board |
| `ERROR_INVALID_MODULE` | Command references a module that is not present |
| `ERROR_BUSY` | The requested peripheral or resource is currently in use |
| `ERROR_CRC_FAILURE` | The received frame failed CRC verification |
| `ERROR_TIMEOUT` | The operation did not complete within the expected time window |
| `ERROR_PERMISSION_DENIED` | The command requires elevated access (future secure mode) |
| `ERROR_INTERNAL` | Firmware encountered an unexpected internal error |
| `ERROR_NOT_IMPLEMENTED` | The command is defined in the protocol but not yet implemented in this firmware version |

### 8.2 Error vs. Unsupported

The distinction between `ERROR_UNKNOWN_COMMAND` and `ERROR_UNSUPPORTED_COMMAND` is intentional:

| Error | Meaning | Typical cause |
|---|---|---|
| `ERROR_UNKNOWN_COMMAND` | Firmware does not recognise the opcode at all | Old firmware, wrong command range |
| `ERROR_UNSUPPORTED_COMMAND` | Opcode is understood but the feature is absent | Board has no DAC hardware |

This separation helps the developer understand whether the issue is a firmware version mismatch or a hardware limitation.

### 8.3 NACK Payload Format

```
Byte 0:   Error code (1 byte, value TBD)
Bytes 1+: Optional UTF-8 human-readable message (NULL terminated or LENGTH delimited)
```

---

## 9. Command Categories

Commands are organised into functional categories.  Boards are free to implement any subset.

> **No numeric opcode values are assigned in this document.**
> Values will be defined in the companion document: `docs/trt-commands.md`.

### 9.1 Category Overview

| Category | Commands | Board types that typically support this |
|---|---|---|
| `SYSTEM` | version, info, reset, reboot, capabilities, modules | All boards |
| `GPIO` | list, read, write, config | MCU boards with digital I/O |
| `PWM` | list, start, stop, set | MCU boards with timer/PWM |
| `ADC` | list, read | MCU boards with ADC peripheral |
| `DAC` | list, read, set | MCU boards with DAC peripheral |
| `I2C` | scan, read, write | Boards with I2C master |
| `SPI` | transfer, config | Boards with SPI master |
| `UART` | config, send, recv | Boards with UART |
| `CAN` | config, send, recv | Boards with CAN transceiver |
| `MODULE` | discover, info, read, write | Boards with expansion modules |
| `FIRMWARE` | begin, chunk, end, verify | All boards (bootloader) |
| `DEBUG` | logs, monitor, shell | Boards with debug infrastructure |

### 9.2 Category Implementation by Board Type

```
Category   │ TRT Core  │ Arduino  │ RP2040  │ Simulator
───────────┼───────────┼──────────┼─────────┼──────────
SYSTEM     │ ✓         │ ✓        │ ✓       │ ✓
GPIO       │ ✓         │ ✓        │ ✓       │ ✗
PWM        │ ✓         │ ✓        │ ✓       │ ✗
ADC        │ ✓         │ ✓        │ ✓       │ ✗
DAC        │ ✓         │ ✗        │ ✗       │ ✗
I2C        │ ✓         │ ✓        │ ✓       │ ✗
SPI        │ ✓         │ ✗        │ ✓       │ ✗
MODULE     │ ✓         │ ✗        │ ✗       │ ✗
FIRMWARE   │ ✓         │ ✓        │ ✓       │ ✗
DEBUG      │ ✓         │ ✗        │ ✗       │ ✗
```

### 9.3 Sending an Unsupported Command

When `trt-cli` sends a `CMD_DAC_READ` to an Arduino-compatible board, the board responds:

```
NACK  ERROR_UNSUPPORTED_COMMAND
```

`trt-cli` displays:

```
  board1: NACK — ERROR_UNSUPPORTED_COMMAND
  Board does not advertise DAC capability.
  Run 'trt board capabilities board1' to see what this board supports.
```

No special-casing in `trt-cli` is required.  The CLI does not need to know in advance which boards support which commands.

---

## 10. Debug Verbosity Levels

TRT CLI supports four debug verbosity levels via repeated `-d` flags.  All levels are purely a `trt-cli` feature — the protocol frames are identical at all levels; only what the CLI prints changes.

> **Debug flags are not yet implemented.**  This section defines the intended behaviour for implementation.

### Level 0 — Normal (no flag)

```bash
trt board board1 version
```

Output:
```
TRT Core 0.1.0
```

Clean, user-facing output only.  No protocol visibility.

---

### Level 1 — Command trace (`-d`)

```bash
trt -d board board1 version
```

Output:
```
[D1] Executing VERSION on board1  (BOARD_ID=0x0002, SEQ=0x0001)
TRT Core 0.1.0
```

Shows:
- Which command is being executed
- Target board logical name and BOARD_ID
- Sequence ID assigned to this request

---

### Level 2 — TX packet (`-dd`)

```bash
trt -dd board board1 version
```

Output:
```
[D2] TX ───────────────────────────────────────────
  AA 55 01 00 02 00 01 00 01 00 00 00 XX XX

TRT Core 0.1.0
```

Shows:
- Complete transmitted frame in hex
- (Received data still displayed as normal output)

---

### Level 3 — TX + field decode (`-ddd`)

```bash
trt -ddd board board1 version
```

Output:
```
[D3] TX ───────────────────────────────────────────
  AA 55 01 00 02 00 01 00 01 00 00 00 XX XX

[D3] Frame decode:
  SYNC     = AA 55
  VERSION  = 01
  FLAGS    = 00  (standard request)
  BOARD_ID = 02 00  → board1 (0x0002)
  SEQ_ID   = 01 00  → 0x0001
  COMMAND  = 01 00  → CMD_VERSION
  LENGTH   = 00 00  → 0 bytes payload
  CRC16    = XX XX

[D3] Command mapping:
  CLI input : trt board board1 version
  Category  : SYSTEM
  Command   : CMD_VERSION

TRT Core 0.1.0
```

Shows:
- Transmitted frame
- Field-by-field decode of the frame
- CLI-to-command mapping (how the CLI verb became a protocol opcode)

---

### Level 4 — Full duplex (`-dddd`)

```bash
trt -dddd board board1 version
```

Output:
```
[D4] TX ───────────────────────────────────────────
  AA 55 01 00 02 00 01 00 01 00 00 00 XX XX

[D4] RX ───────────────────────────────────────────
  AA 55 01 01 02 00 01 00 01 00 07 00 30 2E 31 2E 30 XX XX

[D4] RX decode:
  SYNC     = AA 55
  VERSION  = 01
  FLAGS    = 01  (RESPONSE bit set)
  BOARD_ID = 02 00  → board1 (0x0002)
  SEQ_ID   = 01 00  → 0x0001  (matches TX)
  COMMAND  = 01 00  → CMD_VERSION (response)
  LENGTH   = 07 00  → 7 bytes
  PAYLOAD  = 30 2E 31 2E 30  → "0.1.0"
  CRC16    = XX XX  ✓

[D4] Decoded response:
  Type    : DATA
  Command : CMD_VERSION
  Value   : "0.1.0"

TRT Core 0.1.0
```

Shows:
- Transmitted frame
- Received frame
- Field-by-field decode of both
- Human-readable interpretation of the response

### 10.5 Debug Flag Design Notes

- All four levels are CLI-side only.  Firmware is unaware of the debug level.
- Debug output is written to `stderr`; normal command output goes to `stdout`.  This allows `trt -dddd board board1 adc read 3 2>/dev/null` to suppress debug and keep only the result.
- The `-d` flag applies globally to the entire command invocation, including all sub-commands in a future scripting mode.
- Future: `--log-file <path>` to capture debug output persistently.

---

## 11. Long Payload Support

TRT V1 imposes **no artificial small-payload limit**.

The LENGTH field supports up to 65 535 bytes per frame.  This is sufficient for:

| Use Case | Typical Size |
|---|---|
| GPIO / ADC / DAC read | 1 – 4 bytes |
| Board identity string | 20 – 64 bytes |
| LCD write message | Up to 256 bytes |
| Log dump | Up to 4 KB |
| Single firmware chunk | Up to 4 KB |
| Full firmware image | → use chunked transfer (Section 12) |

For payloads that exceed a single frame or a transport's maximum transfer unit (MTU), use the chunked transfer protocol described in Section 12.

---

## 12. Chunked Transfers

Large data — such as firmware images, data logs, or file transfers — is split into multiple sequential frames called **chunks**.

### 12.1 Concept

```
Host                             Device
  │                                │
  │─── CMD_TRANSFER_BEGIN ────────>│  Announce total size, chunk count
  │<── ACK ────────────────────────│
  │                                │
  │─── CMD_DATA_CHUNK (index=0) ──>│  First data chunk
  │<── ACK ────────────────────────│
  │                                │
  │─── CMD_DATA_CHUNK (index=1) ──>│  Next chunk
  │<── ACK ────────────────────────│
  │                                │
  │         … repeat …             │
  │                                │
  │─── CMD_TRANSFER_END ──────────>│  Signal transfer complete
  │<── ACK ────────────────────────│  (or DATA with result)
```

### 12.2 Firmware Update Sequence

```
HOST                                    DEVICE
 │                                         │
 │─── CMD_FW_UPDATE_BEGIN ───────────────>│  total_size, chunk_count, target_region
 │<── ACK ─────────────────────────────────│
 │                                         │
 │─── CMD_FW_DATA_CHUNK (seq=0, idx=0) ──>│  4096 bytes of firmware binary
 │<── ACK (seq=0) ─────────────────────────│  echoed SEQ_ID confirms receipt
 │                                         │
 │─── CMD_FW_DATA_CHUNK (seq=1, idx=1) ──>│
 │<── ACK (seq=1) ─────────────────────────│
 │                                         │
 │         … continue for all chunks …     │
 │                                         │
 │─── CMD_FW_UPDATE_END ─────────────────>│
 │<── DATA (verification result) ──────────│  CRC of received image
```

### 12.3 Retry Logic

If the host does not receive ACK within a timeout window it resends the same chunk with the same SEQ_ID.  The device detects duplicate SEQ_IDs and responds with ACK without reprocessing.

### 12.4 FLAGS Usage in Chunked Transfers

| FLAG bits | Meaning |
|---|---|
| `CHUNKED` | This frame is part of a chunked transfer |
| `CHUNK_FIRST` | First chunk |
| `CHUNK_LAST` | Last chunk |

---

## 13. Board Identity

Every TRT-compatible board should expose the following identity information via the `CMD_BOARD_INFO` command:

### 10.1 Identity Fields

| Field | Type | Description |
|---|---|---|
| `board_type` | UTF-8 string | Board type name (e.g. `TRT_CORE`) |
| `revision` | UTF-8 string | Hardware revision (e.g. `A1`, `B2`) |
| `firmware` | UTF-8 string | Firmware version (semver, e.g. `0.1.0`) |
| `serial` | UTF-8 string | Board serial number |
| `capabilities` | uint16 bitmask | Supported feature flags |

### 10.2 Serial Number Strategies

Three options are under consideration. The final choice is an open question.

**Option A — TRT Serial in Flash**

A unique serial number is programmed into a dedicated region of the MCU's internal flash during manufacturing or first provisioning.

- ✅ Board-independent (works on any MCU)
- ✅ Fully controlled by TRT ecosystem
- ⚠️ Requires a provisioning step
- ⚠️ Lost if flash is fully erased

**Option B — MCU Unique Identifier**

Most modern MCUs (STM32, RP2040) expose a factory-programmed unique 96-bit or 128-bit ID register.

- ✅ No provisioning required
- ✅ Guaranteed unique per silicon
- ⚠️ MCU-dependent implementation
- ⚠️ Exposes silicon identity (privacy consideration)

**Option C — TRT-Assigned Serial**

`trt-cli` assigns a logical serial number the first time a board is connected, stored in `trt-cli`'s local board registry.

- ✅ Works without firmware changes
- ✅ Human-readable assignment possible
- ⚠️ Serial is tied to the host machine's registry, not the board itself
- ⚠️ Connecting to a different machine shows no serial

**Recommendation (provisional):** Implement Option B as the default for V1 (leverages existing hardware capability with no provisioning overhead), with an override field in flash for Option A when a persistent TRT serial is required.

### 10.3 Capabilities Bitmask

The `capabilities` field in the identity response is a uint16 bitmask matching the `BoardCapabilities` model in `trt-cli`:

| Bit | Capability |
|---|---|
| 0 | GPIO |
| 1 | PWM |
| 2 | ADC |
| 3 | DAC |
| 4 | I2C |
| 5 | SPI |
| 6 | UART |
| 7 | CAN |
| 8 | LCD |
| 9 | Relay |
| 10 | Debug shell |
| 11–15 | Reserved |

---

## 14. Modules

TRT V1 does not define module commands.  This section documents the design intent for future expansion.

### 11.1 Module Concept

A **module** is a peripheral add-on that connects to a TRT board — either via direct integration on the PCB or via an expansion connector.  Examples:

| Module | Function |
|---|---|
| Relay board | Isolated electrical switching |
| DAC board | Precision analog output |
| LCD module | HD44780-compatible display |
| LED strip | WS2812 / NeoPixel addressable LEDs |
| Sensor module | Temperature, humidity, pressure |
| Custom FPGA | Vendor-specific logic |

### 11.2 Module Addressing Strategy (Future)

The COMMAND space `0x1000` – `0xEFFF` is reserved for module expansion.  A module's commands are identified by a **module class ID** embedded in the upper bits of COMMAND.

Module addressing is an open question (see Section 15).

### 11.3 Module Discovery (Future)

A future `CMD_MODULE_LIST` command will allow `trt-cli` to enumerate all modules attached to a board and retrieve their identifiers and capability advertisements, enabling the CLI to dynamically gate available commands.

---

## 15. Transport Strategy

### 12.1 Roadmap

| Version | Transports |
|---|---|
| V1 | USB CDC (USB Full-Speed, CDC-ACM class) |
| V2 | USB CDC + CAN FD |
| V3 | USB CDC + CAN FD + TCP/IP |

### 12.2 Core Principle

> **The protocol frame is transport-agnostic.**
> A frame is identical byte-for-byte whether transmitted over USB, CAN, or TCP.
> Only the framing/segmentation adapter changes per transport.

### 12.3 USB CDC (V1)

- Class: USB CDC-ACM
- No custom driver on Linux or macOS
- On Windows: WinUSB or usbser.sys (built-in from Windows 10)
- Bulk transfer, no packet-size constraint from protocol perspective
- Natural byte-stream framing — SYNC `0xAA55` used for resynchronisation

### 12.4 CAN FD (V2)

- CAN FD frames carry up to 64 bytes of data
- TRT frames larger than 64 bytes must be segmented within the transport layer (similar to ISO 15765-2)
- BOARD_ID maps to CAN node identifier
- One CAN bus can carry traffic for multiple boards simultaneously

### 12.5 TCP/IP (V3)

- Length-prefixed stream framing: 2-byte big-endian length header followed by TRT frame
- TLS optional (enabled via transport configuration flag in `trt-cli`)
- Enables remote board access over a network

### 12.6 Transport Abstraction Layer (Future — `trt-protocol` repo)

```
trt-cli
  └── TransportAdapter (abstract)
        ├── USBCDCTransport
        ├── CANFDTransport   (V2)
        └── TCPTransport     (V3)
```

Each adapter implements `send(frame: bytes)` and `receive() -> bytes` with transport-specific framing.

---

## 16. Versioning and Compatibility

### 13.1 Protocol Version Field

The VERSION field allows host and device to detect incompatible protocol versions before transmitting any commands.

**Compatibility rules:**

| Host VERSION | Device VERSION | Outcome |
|---|---|---|
| 1 | 1 | ✅ Compatible |
| 1 | 2 | ⚠️ Device is newer — host should warn but may continue if device is backward-compatible |
| 2 | 1 | ❌ Host is newer — NACK `PROTOCOL_VERSION_MISMATCH` |

### 13.2 Non-Breaking Changes (No Version Bump Required)

- Adding new COMMAND opcodes in reserved ranges
- Extending PAYLOAD format with optional trailing fields (existing decoders ignore them)
- Adding new capabilities bits (existing firmware ignores unknown bits)

### 13.3 Breaking Changes (Version Bump Required)

- Changing field positions or sizes in the frame header
- Changing the SYNC value
- Changing byte order
- Redefining existing COMMAND opcodes

---

## 17. Security Considerations

> **V1 has no security layer.** This is appropriate for a development tool connected to a local USB device.

Future security requirements (for networked V3 deployments):

- **Authentication:** Challenge-response or pre-shared key to prevent unauthorised access to boards over TCP.
- **Encryption:** TLS transport wrapper (does not change the protocol frame format).
- **Command authorisation:** Some destructive commands (firmware erase, reset) may require an explicit confirmation flag in FLAGS.
- **Replay protection:** SEQ_ID combined with a session token can prevent replayed packets.

None of these are planned for V1 or V2.

---

## 18. Open Questions

These items require a decision before or during V2 implementation.

```
[ ] CRC16 polynomial selection
      Candidates: CRC-16/CCITT (0x1021) or CRC-16/MODBUS (0x8005)
      Criteria: STM32 hardware CRC unit compatibility

[ ] CRC16 or CRC32?
      CRC32 provides stronger integrity for firmware updates.
      CRC16 is lighter on small MCUs.
      Possible: CRC16 for normal frames, CRC32 for firmware chunks.

[ ] Standard error code table
      Define a complete NACK error code registry.
      Avoid overlapping codes across command groups.

[ ] Broadcast packet behaviour
      When FLAGS BROADCAST is set:
        - Does every board respond?
        - How are responses differentiated?
        - Is there a collision risk on CAN?

[ ] Event packet infrastructure
      How does the host enable/disable events?
      What is the event subscription model?
      How are events delivered on USB (interrupt endpoint vs. bulk)?

[ ] Firmware recovery mechanism
      What happens if a firmware update is interrupted mid-transfer?
      Is there a dual-bank bootloader requirement?
      How does the host detect a device stuck in recovery mode?

[ ] Maximum practical payload size
      While LENGTH allows 65 535 bytes, what is the recommended
      single-frame payload limit for reliability?
      Suggestion: cap at 4096 bytes; use chunked for larger.

[ ] Binary-only vs. dual binary/debug endpoint
      Option A: Single endpoint, --debug is pure host-side formatting.
      Option B: Separate USB endpoint for debug text output from firmware.
      Recommendation: Option A (simpler firmware).

[ ] Module addressing strategy
      How are modules identified within the COMMAND space?
      Option A: Upper byte of COMMAND = module class ID.
      Option B: Dedicated CMD_MODULE_WRITE with module ID in payload.
      Option C: Modules are addressed via a sub-protocol.

[ ] Multi-host support
      Should the protocol support multiple host machines connecting
      to the same CAN bus simultaneously?
      V1: out of scope. Document for V3.
```

---

## 19. Design Decisions Log

This section records decisions that were made and the rationale behind them.

| # | Decision | Rationale | Date |
|---|---|---|---|
| 1 | SYNC = `0xAA55` | Alternating bit pattern, easy to spot in hex dumps, not valid UTF-8 | 2026-07-30 |
| 2 | Little-endian byte order | Matches STM32 native byte order, avoids `__builtin_bswap` overhead on firmware | 2026-07-30 |
| 3 | 2-byte COMMAND field | 65 536 opcodes sufficient for foreseeable expansion; 1 byte (256) would be too limiting | 2026-07-30 |
| 4 | 2-byte LENGTH field | Supports payloads up to 64 KB; sufficient for firmware chunks; avoids 4-byte overhead | 2026-07-30 |
| 5 | 2-byte BOARD_ID field | Supports 65 534 boards; overkill for bench use but trivially cheap overhead | 2026-07-30 |
| 6 | FLAGS reserved as 0x00 in V1 | Ensures clean forward compatibility without committing to bit meanings prematurely | 2026-07-30 |
| 7 | CRC covers entire frame including header | Detects corrupted BOARD_ID and COMMAND fields, not just payload corruption | 2026-07-30 |
| 8 | Board type string not MCU name | Decouples CLI from silicon family; allows same CLI to work with STM32, RP2040, Arduino | 2026-07-30 |
| 9 | Boards decide capability, not CLI | CLI remains stable across board types; no board-specific forks of trt-cli | 2026-07-30 |
| 10 | `ERROR_UNKNOWN_COMMAND` ≠ `ERROR_UNSUPPORTED_COMMAND` | Distinguishes firmware version mismatch from hardware limitation — actionable debugging | 2026-07-30 |
| 11 | Debug verbosity via `-d/-dd/-ddd/-dddd` | Graduated visibility without a single opaque `--debug` flag; stderr separation keeps scripts clean | 2026-07-30 |

---

## Related Documents

| Document | Contents |
|---|---|
| [architecture.md](architecture.md) | Overall trt-cli system architecture |
| [cli-reference.md](cli-reference.md) | Full CLI command reference |
| [future-protocol.md](future-protocol.md) | Earlier protocol sketch (superseded by this document for design decisions) |
| `docs/trt-commands.md` *(planned)* | Complete command opcode table and payload formats |

---

*TRT Protocol V1 specification — last updated 2026-07-30*
