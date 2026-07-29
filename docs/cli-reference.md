# TRT CLI Reference

Complete reference for all `trt` commands.

---

## Global Options

```
trt --help                  Show help and exit
trt --install-completion    Install shell completion
trt --show-completion       Show completion script
```

---

## trt help

Display the full command tree with descriptions.

```bash
trt help
```

---

## trt version

Display the TRT CLI version.

```bash
trt version
```

**Output:**
```
TRT CLI
Version: 0.1.0
```

---

## trt boards

List all boards currently known to TRT.

```bash
trt boards
```

**Output columns:** Board ID · Type · Revision · Firmware · Transport · Status

**Example:**
```
╭──────────────── Connected Boards ────────────────╮
│ Board ID │ Type     │ Rev │ Firmware │ Transport  │ Status    │
│ board0   │ TRT_CORE │ A1  │ 0.1.0    │ usb:COM3   │ ready     │
│ board1   │ Arduino  │ R3  │ 0.1.0    │ usb:COM4   │ connected │
╰──────────────────────────────────────────────────╯
```

---

## trt discover

Force a rescan for connected boards on all active transports.

```bash
trt discover
```

Currently a mock implementation.  Future: triggers USB enumeration via TRT Protocol.

---

## trt board

Operate on a specific board.  All sub-commands require a board ID.

```bash
trt board <board_id> <sub-command> [options]
```

### trt board \<id\> info

Display board identity and firmware details.

```bash
trt board board0 info
```

### trt board \<id\> status

Show current board operational status.

```bash
trt board board0 status
```

### trt board \<id\> reset

Send a reset command to the board.

```bash
trt board board0 reset
```

### trt board \<id\> reboot

Reboot the board into normal firmware.

```bash
trt board board0 reboot
```

### trt board \<id\> capabilities

List all capabilities the board advertises.

```bash
trt board board0 capabilities
```

**Output:**
```
Capabilities — board0
  gpio         ✓ yes
  pwm          ✓ yes
  adc          ✓ yes
  dac          ✓ yes
  i2c          ✓ yes
  spi          ✓ yes
  lcd          ✗ no
  relay        ✗ no
```

### trt board \<id\> modules

List firmware modules loaded on the board.

```bash
trt board board0 modules
```

---

## trt board \<id\> gpio

GPIO pin control.

### gpio list

```bash
trt board board0 gpio list
```

### gpio read

```bash
trt board board0 gpio read <pin>
```

| Argument | Type   | Description            |
|----------|--------|------------------------|
| `pin`    | string | Pin name e.g. `PA5`   |

**Example:**
```bash
trt board board0 gpio read PA5
# board0  gpio read  PA5  →  0
```

### gpio write

```bash
trt board board0 gpio write <pin> <value>
```

| Argument | Type    | Description              |
|----------|---------|--------------------------|
| `pin`    | string  | Pin name e.g. `PA5`     |
| `value`  | int 0–1 | Value to write: 0 or 1  |

**Example:**
```bash
trt board board0 gpio write PA5 1
```

---

## trt board \<id\> pwm

PWM channel control.

### pwm list

```bash
trt board board0 pwm list
```

### pwm start

```bash
trt board board0 pwm start <channel>
```

### pwm stop

```bash
trt board board0 pwm stop <channel>
```

### pwm set

Set frequency and duty cycle.

```bash
trt board board0 pwm set <channel> <frequency> <duty>
```

| Argument     | Type  | Description                   |
|--------------|-------|-------------------------------|
| `channel`    | int   | PWM channel number            |
| `frequency`  | float | Frequency in Hz               |
| `duty`       | float | Duty cycle 0.0 – 100.0 %     |

**Example:**
```bash
trt board board0 pwm set 1 1000 50
```

---

## trt board \<id\> adc

Analog-to-Digital Converter.

### adc list

```bash
trt board board0 adc list
```

### adc read

```bash
trt board board0 adc read <channel>
```

**Example:**
```bash
trt board board0 adc read 3
# board0  adc read  ch=3  →  0 (0.00 mV)
```

---

## trt board \<id\> dac

Digital-to-Analog Converter.

### dac list

```bash
trt board board0 dac list
```

### dac read

```bash
trt board board0 dac read <channel>
```

### dac set

```bash
trt board board0 dac set <channel> <value>
```

| Argument   | Type | Description                         |
|------------|------|-------------------------------------|
| `channel`  | int  | DAC channel number                  |
| `value`    | int  | Raw output value (0–4095 for 12-bit)|

**Example:**
```bash
trt board board0 dac set 1 2048
```

---

## trt board \<id\> i2c

I2C master operations.

### i2c scan

Scan the I2C bus for device addresses.

```bash
trt board board0 i2c scan
```

### i2c read

```bash
trt board board0 i2c read [--addr 0x48] [--reg 0x00] [--len 1]
```

| Option   | Default | Description               |
|----------|---------|---------------------------|
| `--addr` | `0x48`  | I2C device address (hex)  |
| `--reg`  | `0x00`  | Register address (hex)    |
| `--len`  | `1`     | Number of bytes to read   |

**Example:**
```bash
trt board board0 i2c read --addr 0x48 --reg 0x00 --len 2
```

### i2c write

```bash
trt board board0 i2c write [--addr 0x48] [--reg 0x00] [--data 0xAB]
```

---

## trt board \<id\> spi

SPI master operations.

### spi transfer

Full-duplex byte transfer.

```bash
trt board board0 spi transfer [--data 0x00]
```

### spi config

Configure SPI bus parameters.

```bash
trt board board0 spi config [--baud 1000000] [--mode 0] [--msb/--lsb]
```

---

## trt board \<id\> debug

Diagnostic and debug operations.

### debug logs

```bash
trt board board0 debug logs [--follow]
```

### debug monitor

```bash
trt board board0 debug monitor
```

### debug shell

```bash
trt board board0 debug shell
```

---

## trt lcd

LCD display control (HD44780-style over I2C).

```bash
trt lcd info
trt lcd reset
trt lcd clear
trt lcd write "Hello TRT"
trt lcd write "Hello" --line 0 --col 0
```

| Option   | Default | Description               |
|----------|---------|---------------------------|
| `--line` | `0`     | Target line (0-indexed)   |
| `--col`  | `0`     | Start column (0-indexed)  |

---

## trt led

LED control (WS2812 / NeoPixel style).

```bash
trt led on
trt led off
trt led blink [--count 3] [--interval 500]
trt led brightness <level>       # 0–100
trt led color <red> <green> <blue>  # 0–255 each
```

**Examples:**
```bash
trt led color 255 0 0      # Red
trt led color 0 255 0      # Green
trt led color 0 0 255      # Blue
trt led brightness 50
trt led blink --count 5 --interval 250
```

---

## trt protocol

TRT Protocol information.

```bash
trt protocol info       # Show protocol specification summary
trt protocol version    # Show protocol version
```

---

## Shell Completion

```bash
# Bash
trt --install-completion bash

# Zsh
trt --install-completion zsh

# Fish
trt --install-completion fish

# PowerShell
trt --install-completion powershell
```
