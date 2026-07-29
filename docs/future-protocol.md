# TRT Protocol — Design Notes

> **Status: Planned — not yet implemented.**
> Implementation will live in the `trt-protocol` repository.

---

## Overview

TRT Protocol is the binary communication layer between `trt-cli` (host) and TRT firmware (device).  It is transport-agnostic: the same message format is used over USB, CAN, or TCP.

---

## Design Goals

1. **Compact** — suitable for constrained microcontrollers with limited RAM.
2. **Versioned** — host and firmware can negotiate compatibility.
3. **Extensible** — new command types can be added without breaking existing implementations.
4. **Error-detecting** — CRC-16 on every packet.
5. **Transport-agnostic** — the framing layer is the same over USB CDC, CAN, and TCP.

---

## Packet Structure

```
┌──────────────────────────────────────────────────────────────┐
│ Offset │ Size    │ Field     │ Description                    │
├────────┼─────────┼───────────┼────────────────────────────────┤
│   0    │ 2 bytes │ MAGIC     │ 0x54 0x52  ("TR")              │
│   2    │ 1 byte  │ VERSION   │ Protocol version (0x01)        │
│   3    │ 1 byte  │ CMD       │ Command opcode                 │
│   4    │ 2 bytes │ LENGTH    │ Payload length (little-endian) │
│   6    │ N bytes │ PAYLOAD   │ Command-specific data          │
│  6+N   │ 2 bytes │ CRC       │ CRC-16/CCITT of bytes 0..5+N  │
└──────────────────────────────────────────────────────────────┘
```

**Minimum packet size:** 8 bytes (header + CRC, no payload).

**Maximum payload size:** 65535 bytes (limited by LENGTH field).

---

## Command Opcodes (Planned)

### System Commands

| Opcode | Name              | Description                          |
|--------|-------------------|--------------------------------------|
| 0x01   | PING              | Keepalive / latency probe            |
| 0x02   | PONG              | Response to PING                     |
| 0x03   | BOARD_INFO        | Request board identity               |
| 0x04   | BOARD_INFO_RESP   | Board identity response              |
| 0x05   | CAPABILITIES      | Request capability list              |
| 0x06   | CAPABILITIES_RESP | Capability list response             |
| 0x07   | BOARD_RESET       | Trigger board reset                  |
| 0x08   | BOARD_REBOOT      | Trigger board reboot                 |
| 0x09   | STATUS            | Request board status                 |
| 0x0A   | STATUS_RESP       | Board status response                |
| 0x0B   | MODULE_LIST       | Request loaded module list           |
| 0x0C   | MODULE_LIST_RESP  | Module list response                 |

### GPIO Commands

| Opcode | Name           | Description           |
|--------|----------------|-----------------------|
| 0x10   | GPIO_LIST      | List GPIO pins        |
| 0x11   | GPIO_LIST_RESP | GPIO list response    |
| 0x12   | GPIO_READ      | Read pin value        |
| 0x13   | GPIO_READ_RESP | Pin value response    |
| 0x14   | GPIO_WRITE     | Write pin value       |
| 0x15   | GPIO_WRITE_ACK | Write acknowledgement |

### PWM Commands

| Opcode | Name         | Description            |
|--------|--------------|------------------------|
| 0x20   | PWM_LIST     | List PWM channels      |
| 0x21   | PWM_SET      | Set frequency and duty |
| 0x22   | PWM_START    | Start PWM output       |
| 0x23   | PWM_STOP     | Stop PWM output        |
| 0x24   | PWM_ACK      | Acknowledgement        |

### ADC Commands

| Opcode | Name         | Description        |
|--------|--------------|--------------------|
| 0x30   | ADC_LIST     | List ADC channels  |
| 0x31   | ADC_READ     | Read ADC channel   |
| 0x32   | ADC_READ_RESP| ADC value response |

### DAC Commands

| Opcode | Name         | Description        |
|--------|--------------|--------------------|
| 0x40   | DAC_LIST     | List DAC channels  |
| 0x41   | DAC_READ     | Read DAC output    |
| 0x42   | DAC_SET      | Set DAC output     |
| 0x43   | DAC_ACK      | Acknowledgement    |

### I2C Commands

| Opcode | Name          | Description              |
|--------|---------------|--------------------------|
| 0x50   | I2C_SCAN      | Scan bus for addresses   |
| 0x51   | I2C_SCAN_RESP | Address list response    |
| 0x52   | I2C_READ      | Read from register       |
| 0x53   | I2C_READ_RESP | Read data response       |
| 0x54   | I2C_WRITE     | Write to register        |
| 0x55   | I2C_WRITE_ACK | Write acknowledgement    |

### SPI Commands

| Opcode | Name            | Description         |
|--------|-----------------|---------------------|
| 0x60   | SPI_CONFIG      | Configure SPI bus   |
| 0x61   | SPI_TRANSFER    | Full-duplex transfer|
| 0x62   | SPI_TRANSFER_RESP| Transfer response  |

### LCD Commands

| Opcode | Name         | Description            |
|--------|--------------|------------------------|
| 0x70   | LCD_RESET    | Reset display          |
| 0x71   | LCD_CLEAR    | Clear display          |
| 0x72   | LCD_WRITE    | Write text             |
| 0x73   | LCD_ACK      | Acknowledgement        |

### LED Commands

| Opcode | Name           | Description             |
|--------|----------------|-------------------------|
| 0x80   | LED_ON         | Turn LEDs on            |
| 0x81   | LED_OFF        | Turn LEDs off           |
| 0x82   | LED_BLINK      | Blink with parameters   |
| 0x83   | LED_BRIGHTNESS | Set brightness          |
| 0x84   | LED_COLOR      | Set RGB colour          |
| 0x85   | LED_ACK        | Acknowledgement         |

### Debug Commands

| Opcode | Name           | Description               |
|--------|----------------|---------------------------|
| 0x90   | LOG_STREAM     | Open log stream session   |
| 0x91   | LOG_DATA       | Log data packet           |
| 0x92   | LOG_CLOSE      | Close log stream          |
| 0x93   | MONITOR_DATA   | System monitor snapshot   |
| 0x94   | SHELL_DATA     | Debug shell I/O           |

### Error Response

| Opcode | Name  | Description                          |
|--------|-------|--------------------------------------|
| 0xFF   | ERROR | Error response with error code field |

---

## BOARD_INFO Response Payload

```
┌────────────────────────────────────────────────────────┐
│ Field          │ Size    │ Description                  │
├────────────────┼─────────┼──────────────────────────────┤
│ board_type_len │ 1 byte  │ Length of board_type string  │
│ board_type     │ N bytes │ Board type string (UTF-8)    │
│ revision_len   │ 1 byte  │ Length of revision string    │
│ revision       │ N bytes │ Revision string (UTF-8)      │
│ firmware_len   │ 1 byte  │ Length of firmware string    │
│ firmware       │ N bytes │ Firmware version (UTF-8)     │
│ serial_len     │ 1 byte  │ Length of serial string      │
│ serial         │ N bytes │ Serial number (UTF-8)        │
└────────────────────────────────────────────────────────┘
```

---

## CAPABILITIES_RESP Payload

```
┌────────────────────────────────────────────────────────┐
│ Field    │ Size    │ Description                        │
├──────────┼─────────┼────────────────────────────────────┤
│ flags    │ 2 bytes │ Capability bitmask (see below)     │
│ reserved │ 2 bytes │ Reserved for future use            │
└────────────────────────────────────────────────────────┘
```

**Capability bitmask:**

| Bit | Capability  |
|-----|-------------|
| 0   | gpio        |
| 1   | pwm         |
| 2   | adc         |
| 3   | dac         |
| 4   | i2c         |
| 5   | spi         |
| 6   | uart        |
| 7   | can         |
| 8   | lcd         |
| 9   | relay       |
| 10  | debug_shell |
| 11–15 | Reserved  |

---

## Error Codes

| Code | Name                | Description                    |
|------|---------------------|--------------------------------|
| 0x01 | UNKNOWN_CMD         | Unrecognised command opcode    |
| 0x02 | CAPABILITY_MISSING  | Board lacks required capability|
| 0x03 | INVALID_PARAM       | Parameter out of range         |
| 0x04 | TIMEOUT             | Operation timed out            |
| 0x05 | HARDWARE_ERROR      | Peripheral reported an error   |
| 0x06 | BUSY                | Resource is busy               |
| 0x07 | PROTOCOL_MISMATCH   | Incompatible protocol versions |

---

## CRC Calculation

CRC-16/CCITT (polynomial 0x1021, initial value 0xFFFF, no inversion).

The CRC covers all bytes from MAGIC through the end of PAYLOAD (bytes 0 through 5+N inclusive).

---

## Protocol Versioning

- The VERSION byte in every packet allows hosts and devices to negotiate compatibility.
- A device running protocol version 1 must still accept version 1 packets from a host running a newer CLI.
- Version negotiation happens during the BOARD_INFO exchange.

---

## Transport Notes

### USB CDC
- CDC-ACM class (no custom driver on Linux/macOS; WinUSB or usbser.sys on Windows).
- Maximum packet size: 64 bytes for Full-Speed USB (bulk transfer).
- Large payloads are segmented automatically by the transport layer.

### CAN Bus (Future)
- 11-bit standard identifiers.
- TRT Protocol messages fragmented across CAN frames (similar to ISO 15765-2 / UDS).
- Board ID embedded in CAN identifier.

### TCP (Future)
- Length-prefixed framing (2-byte big-endian length + TRT packet).
- TLS optional (configuration flag).

---

## Implementation Notes

The Python implementation will live in the `trt-protocol` repository and expose:

```python
# Future API sketch
from trt_protocol import TRTConnection

conn = TRTConnection.usb("COM3")
conn.open()

board_info = conn.board_info()
caps = conn.capabilities()

conn.gpio_write("PA5", 1)
value = conn.gpio_read("PA5")

conn.close()
```

`trt-cli` will depend on `trt-protocol` as a package once it exists.
