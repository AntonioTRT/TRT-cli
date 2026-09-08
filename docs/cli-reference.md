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

## Debug Flags

TRT CLI supports four debug verbosity levels applied via repeated `-d` flags.
These are global options that can precede any command.

> **Not yet implemented.** Defined here as the official behaviour specification.
> See [trt-protocol.md § 10. Debug Verbosity Levels](trt-protocol.md#10-debug-verbosity-levels) for full examples.

| Flag | Level | What is shown |
|---|---|---|
| *(none)* | 0 | Normal user-facing output only |
| `-d` | 1 | Command execution trace (board, SEQ_ID) |
| `-dd` | 2 | TX frame hex dump |
| `-ddd` | 3 | TX frame + field decode + CLI→command mapping |
| `-dddd` | 4 | TX frame + RX frame + full decode + interpreted response |

**Level 0 (normal):**
```bash
trt board board1 version
```
```
TRT Core 0.1.0
```

**Level 1 (`-d`):**
```bash
trt -d board board1 version
```
```
[D1] Executing VERSION on board1  (BOARD_ID=0x0002, SEQ=0x0001)
TRT Core 0.1.0
```

**Level 2 (`-dd`):**
```bash
trt -dd board board1 version
```
```
[D2] TX ───────────────────────────────────────────
  AA 55 01 00 02 00 01 00 01 00 00 00 XX XX

TRT Core 0.1.0
```

**Level 3 (`-ddd`):**
```bash
trt -ddd board board1 version
```
```
[D3] TX ───────────────────────────────────────────
  AA 55 01 00 02 00 01 00 01 00 00 00 XX XX

[D3] Frame decode:
  SYNC=AA55  VERSION=01  FLAGS=00  BOARD_ID=0x0002(board1)
  SEQ_ID=0x0001  COMMAND=CMD_VERSION  LENGTH=0

[D3] Command mapping:
  CLI input : trt board board1 version
  Category  : SYSTEM
  Command   : CMD_VERSION

TRT Core 0.1.0
```

**Level 4 (`-dddd`):**
```bash
trt -dddd board board1 version
```
```
[D4] TX ───────────────────────────────────────────
  AA 55 01 00 02 00 01 00 01 00 00 00 XX XX

[D4] RX ───────────────────────────────────────────
  AA 55 01 01 02 00 01 00 01 00 07 00 30 2E 31 2E 30 XX XX

[D4] RX decode:
  FLAGS=01(RESPONSE)  SEQ_ID=0x0001(match)  LENGTH=7
  PAYLOAD="0.1.0"

[D4] Decoded response: TYPE=DATA  VALUE="0.1.0"

TRT Core 0.1.0
```

**Design notes:**
- Debug output goes to `stderr`; command output goes to `stdout`
- Scripts can suppress debug with `2>/dev/null` (Linux/macOS) or `2>$null` (PowerShell)

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
Version: 1.0.0
```

---

## trt update

Check for a newer version of the TRT CLI application.

> **Scope:** This command updates the `trt-cli` Python package on your machine.
> It is entirely independent from board firmware updates (`trt board <id> update`, future).

```bash
trt update                  # Check for updates
trt update --install        # Check and install if available
trt update --check          # Explicit check-only (same as no flags)
```

| Option | Description |
|---|---|
| `--install` / `-i` | Download and install the latest version |
| `--check` / `-c` | Check only, never prompt for install |

**Phase 1 output (current):**
```
  Checking for updates…
  Current version : 1.0.0
  Install method  : pip
  Checking         : GitHub releases (AntonioTRT/TRT-cli)

  ✓ No update available.
  GitHub release checking will be available in a future release.
```

**Phase 2 output (when update is available):**
```
  ╭─ Update available! ───────────────────────────────╮
  │  Current version : 1.0.0                          │
  │  Latest version  : 0.2.0                          │
  │  https://github.com/AntonioTRT/TRT-cli/releases   │
  ╰───────────────────────────────────────────────────╯

  Run trt update --install to install it.
```

**GitHub API endpoint (Phase 2):**
```
GET https://api.github.com/repos/AntonioTRT/TRT-cli/releases/latest
```

**Supported install methods:**
- `pip install --upgrade trt-cli` (standard pip)
- `pipx upgrade trt-cli` (pipx managed)
- `uv pip install --upgrade trt-cli` (uv managed)

The install method is auto-detected at runtime.

---

## trt boards

List all boards currently known to TRT.

```bash
trt boards
```

**Output columns:** Board ID · Type · Revision · Firmware · Build ID · Transport · Status

**Example:**
```
╭──────────────── Connected Boards ────────────────╮
│ Board ID │ Type     │ Rev │ Firmware │ Transport  │ Status    │
│ 101      │ UNSPECIFIED │ - │ 0.1.0 │ 000004 │ usb:COM4 │ ready │
╰──────────────────────────────────────────────────╯
```

---

## trt discover

Force a rescan for connected boards on all active transports.

```bash
trt discover
```

Enumerates available serial ports, probes each port with TRT protocol frames, and lists TRT-compatible boards.

---

## trt board

Operate on a specific board.  All sub-commands require a board ID.

```bash
trt board <board_id> <sub-command> [options]
```

### trt board \<id\> info

Display board identity and firmware details.

```bash
trt board 101 info
```

### trt board \<id\> status

Show current board operational status.

```bash
trt board 101 status
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
trt board 101 capabilities
```

**Output:**
```
Capabilities — 101
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
