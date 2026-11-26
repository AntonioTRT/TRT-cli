# TRT CLI Reference

Complete reference for all `trt` commands.

## Getting started

```text
trt discover                  Discover TRT boards
trt boards                    Show boards: application, HWID read / expected, MATCH
trt board info <address>      One board in detail
trt board hwid <address>      Which daughter board is connected
trt board active-program <address>   Which application is installed
trt board update <address>    If MISMATCH: build, flash, reboot, verify MATCH
trt listen                    Monitor heartbeat and events (Ctrl+C)
```

Three help levels, from short to complete:

| Command | Shows |
|---|---|
| `trt` | Quick Start: the five workflow commands |
| `trt --help` | All visible commands grouped: Board Discovery, Board Management, Monitoring, Development, Information |
| `trt help` | Full reference: concepts, reading MATCH / MISMATCH, typical workflow, heartbeat, commands |

## Concepts

| Term | Meaning | Example |
|---|---|---|
| Board Address | How TRT talks to a board: the number in every command (`<address>`). Not a hardware identifier. | `201` |
| Board ID | Identifies the carrier board, to select its board profile. **Not implemented yet** (planned: ADC resistor divider). Today: name, type, revision in `trt board info`. | `NUCLEO-L073RZ` |
| HWID | Identifies the daughter board, read from ID pins D6..D3 at boot. Decides the required application. | `0010` (= 2) |
| Application ID | The installed firmware application, `app_<HWID>_<name>`; the digits are the HWID it expects. | `app_0002_analog_family` |

Status: `HWID 0010 / 0010 MATCH` (read from hardware / expected by the installed application)
means nothing to do; `0010 / 0000 MISMATCH` means run `trt board update <address>`.
Details: TRT-core `docs/hwid-and-firmware-update.md`.

## Commands not shown in the help screens

Still callable, but hidden from `trt`, `trt --help`, `trt help` and `trt board --help`
because they do not talk to hardware or are outdated:

| Command | Reason |
|---|---|
| `trt lcd ...`, `trt led ...` | Simulated (mock): print "(mock: no hardware connected)" |
| `trt protocol info / version` | Outdated placeholder: describes a planned packet format, not the real TRT v0.1 protocol (see TRT-core `docs/protocol-v0.1-wire-format.md`) |
| `trt board gpio / pwm / adc / dac / i2c / spi / debug / modules / reset / reboot` | Simulated (mock), no firmware support |
| `trt board status` | Reads the discovery cache, which always says `ready`; use `trt boards` / `trt board info` |

---

## Global Options

```
trt --help                  Show help and exit
trt --install-completion    Install shell completion
trt --show-completion       Show completion script
```

## STM32 NUCLEO-L073RZ

```powershell
trt list-programs stm32 [--project-dir PATH]
trt board <id|name|type|revision|version|build-id|runtime|active-program|hwid|uptime|transport> <address> [--port COM5]
trt board update <address> [--check] [--port COM5] [--project-dir PATH]
trt build stm32 <app> [--project-dir PATH]
trt flash stm32 [app] [--project-dir PATH]
trt flash stm32 --platformio [--port COM5] [--project-dir PATH]
trt stm32 test [--port COM5] [--board-id 0x0002]
trt board info 2 [--port COM5]
```

`board <query> <address>` are read-only queries; each asks the board for one value it
already knows and prints it (`--port` overrides the saved/discovered port):

| Command | Source |
|---|---|
| `board id` | board address in the reply frame |
| `board name` | INFO field 0x01 |
| `board type` | INFO field 0x06 (board family: Arduino, STM32, ESP32, ...) |
| `board revision` | BOARD_VERSION |
| `board version` | FW_VERSION |
| `board build-id` | BUILD_ID |
| `board runtime` | RUNTIME (`RUNNING`) |
| `board active-program` | ACTIVE_PROGRAM |
| `board hwid` | HWID (0x000B): daughter-board hardware ID read from the ID pins |
| `board uptime` | UPTIME (`DD HH:MM:SS.mmm (N ms)`) |
| `board transport` | the host's connection (port and baud rate); no firmware query |

#### Which command to use

| Command | Purpose | Source | Notes |
|---|---|---|---|
| `board info` | Everything at once: ID, port, revision, firmware, build ID, INFO fields, capabilities | live, 6 requests | Aggregates `id`, `name`, `type`, `revision`, `version`, `build-id`, `capabilities`; use it for a human overview |
| `board version` | Firmware version only | live, FW_VERSION | For scripts |
| `board build-id` | Build identifier only | live, BUILD_ID | Not part of INFO; unique among the single-value queries except via `board info` |
| `board name` | Board name | live, INFO 0x01 | |
| `board type` | Board family (Arduino, STM32, ESP32, ...) | live, INFO 0x06 | Distinct from `name` |
| `board revision` | Hardware revision | live, BOARD_VERSION | |
| `board id` | Confirms which ID the board replies with | live, reply header | You already pass the ID in; `trt boards` lists IDs |
| `board runtime` | TRT-Core runtime state | live, RUNTIME | Currently only `RUNNING` |
| `board active-program` | Application on the board | live, ACTIVE_PROGRAM | Unique |
| `board hwid` | Daughter-board hardware ID | live, HWID | Compared with the application by `board update` |
| `board uptime` | Time since boot | live, UPTIME | Unique |
| `board transport` | How the host reaches the board | host, saved/discovered connection | No firmware query |
| `board capabilities` | Capability list | discovery scan, then render | Also shown in `board info` |
| `board status` | Board status | discovery cache | See below |

Overlaps that exist and are intentional or fixed by the protocol:

- `board info` repeats what the single-value commands return; the single-value commands exist for scripting and quick checks.
- On the wire, the firmware version is sent twice (FW_VERSION and INFO field 0x03), the revision twice (BOARD_VERSION and INFO field 0x02), and INFO fields 0x01 (name) and 0x05 (serial placeholder) carry the same string. The V0.1 identifiers are frozen, so these stay.
- The decoded INFO key `board_type` holds the board *name* (V0.1 naming), while `board type` shows the *family*. `board info` prints the former as `INFO.BOARD_TYPE` and the latter as `INFO.FAMILY`.

Findings that are not duplication but worth knowing:

- `board status` reads the discovery cache (discovery records every found board as `ready`); it does not send STATUS to the board, unlike every other query. The firmware's STATUS reply is only exercised by `trt stm32 test`.
- `board id` and `board runtime` carry little information: the first echoes the ID you supplied, the second can only say `RUNNING` because any reply proves the runtime is polling.

`board info`, `board status` and `board capabilities` are unchanged. If the firmware does not
provide a value (older firmware, or no clock / no active program declared), the command prints
`unsupported` and exits with code 2; other failures exit with code 1. Build date and build time
are not available in TRT-Core and have no command.

`board update <address>` checks that the installed application matches the board's
HWID and fixes it if not (STM32 only). It reads HWID, ACTIVE_PROGRAM and the INFO family,
picks the application `app_<HWID>_*` from the STM32CubeIDE project, and prints both. On a
match it exits 0. On a mismatch it builds the required application, flashes it with
verify and reset, waits up to 20 s for the board to answer again, and re-reads HWID
and ACTIVE_PROGRAM. It exits 0 when the board reports the required application, else 1.
`--check` only reports and exits 1 on mismatch. Firmware that does not report a HWID
exits 2 with the one-time bootstrap commands (`trt build stm32 app_0000_idle`,
`trt flash stm32`, `trt discover`). The model is documented in TRT-core
`docs/hwid-and-firmware-update.md`.

`list-programs stm32` prints one application name per line, discovered from the
files `Sources/programs/app_<HWID>_<name>.c` of the STM32CubeIDE project (sorted; files not
following that naming are ignored; read-only, it builds and flashes nothing). These are
exactly the names `build stm32` and `flash stm32` accept. It exits with code 1 if no
program is found.

`build stm32 <app>` builds one application of the STM32CubeIDE project
(`TRT-core/TRT-stm32/am modulation`) with TRT-Core included, in
`build/<app>/` (CubeIDE's `Debug/` is not touched), via
`cmake ... -DACTIVE_PROGRAM=APP_<HWID>_<NAME>` and `cmake --build`. It copies the
`.elf` to `artifacts/<app>/<app>.elf` and records it in
`artifacts/latest.json`. It never flashes. Needs `cmake` and `arm-none-eabi-gcc`
(and uses `ninja` if present): from `PATH`, or else the copies bundled with
STM32CubeIDE under `C:\ST\STM32CubeIDE_*`. Valid names are the files in
`Sources/programs/app_<HWID>_<name>.c`; an unknown name lists them.

`flash stm32` flashes an existing artifact and never builds: with no name the
most recent build (`latest.json`), with a name that application's stored build,
using `STM32_Programmer_CLI -c port=SWD -w <elf> -v -rst` (from `PATH` or STM32CubeIDE).
If nothing is built it tells you to run `trt build stm32 <app>`.
`flash stm32 --platformio` keeps the previous behaviour: it runs
`python -m platformio run -d <TRT-stm32> -t upload` (`--port` applies only here).
`stm32 test` scans serial ports unless one is specified and sends all six
TRT v0.1 requests at 115200 baud, 8N1. It checks PING for ACK `0x8001`,
the five data commands for response `0x8003`, and decodes INFO, STATUS, and
the capability identifier list. V0.1 CRC fields are emitted as `0x0000`,
matching the current TRT-core encoder.

Example test against the Nucleo's ST-LINK virtual COM port:

```powershell
trt stm32 test --port COM5
```

Discovery scans every serial COM port (without VID/PID filtering), tries the
TRT v0.1 PING/ACK handshake before STM32 identity queries, and caches board address,
port, and 115200 baudrate in `%USERPROFILE%\.trt\boards.json`.
`trt board info 2` resolves the cached port or performs a discovery scan;
`--port COM5` bypasses port resolution. The info command reads PING, BOARD_VERSION,
INFO, CAPABILITIES, FW_VERSION, and BUILD_ID. It exits non-zero if the device
does not return valid protocol responses.

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

The full reference: concepts (Board Address, Board ID, HWID, Application ID), how to read
MATCH / MISMATCH, the typical workflow, heartbeat, and every visible command grouped by
purpose. `trt` alone shows the Quick Start; `trt --help` the grouped command list.

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
> It is entirely independent from board firmware updates (`trt board update <address>`).

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

## trt listen

Passively print every asynchronous message sent by TRT boards. Nothing is sent to the boards.

```bash
trt listen              # all serial ports, all boards
trt board listen 101    # only board 101
```

Stop with Ctrl+C. `trt board listen <address>` needs a numeric board address and ignores frames from other boards.

```
Board 101: HEARTBEAT
Board 101: HEARTBEAT
Board 101: HEARTBEAT
```

### Relationship with TRT-Core heartbeat

Every TRT-Core board emits a HEARTBEAT event (FLAGS `0x02`, COMMAND `0x9001`) about once per second. `listen` receives and prints it. Other event frames are shown as `EVENT 0x<id> payload=<hex>`. Heartbeat only shows that the runtime is alive; it does not replace discovery (`trt discover`, `trt board info <address>`, `trt board capabilities <address>`). See the TRT-Core `docs/event-system.md`.

### When to use it

- Firmware validation: the firmware is running.
- Flash validation: the board boots after flashing.
- Runtime validation: the TRT runtime loop is alive.
- Communication validation: the transport path works.
- Development diagnostics.

### Typical workflow

1. Flash the board.
2. Run `trt listen`. A `HEARTBEAT` line about every second confirms the board is alive (the first one can take about a second, because opening the port resets Arduino-type boards).
3. Run `trt discover` or `trt board info <address>` to check identity and version.

### Notes

- Close other programs using the serial port first; only one program can hold a port.
- Exit code is 1 if no serial port exists or none can be opened.
- The simulator does not emit heartbeats.

---

## trt boards

List all boards currently known to TRT.

```bash
trt boards
```

**Output columns:** ID · Name · Firmware (version #build) · Application · HWID (read / expected) · Status

- **Application**: ACTIVE_PROGRAM, the application installed in the firmware.
- **HWID read / expected**: the hardware ID read from the board's ID pins (D6..D3, e.g. `0010` = 2)
  / the HWID the installed application is written for (the digits in `app_<HWID>_<name>`).
  `----` when the firmware does not report it.
- **Status**: `MATCH`, `MISMATCH` (update required), `NO HWID` (firmware cannot read the HWID) or
  `NO APP` (no `app_<HWID>_*` application declared). Below the table, every board that needs
  action gets one line with the command to run.

**Example (match):**
```
Connected Boards
Addr  Name           Firmware       Application             HWID         Status
201   am-modulation  0.1.0 #000001  app_0002_analog_family  0010 / 0010  MATCH
HWID: read from hardware / expected by the installed application
```

**Example (mismatch):**
```
Connected Boards
Addr  Name           Firmware       Application    HWID         Status
201   am-modulation  0.1.0 #000001  app_0000_idle  0010 / 0000  MISMATCH
HWID: read from hardware / expected by the installed application
  Board 201: update required. Run trt board update 201
```

`trt boards`, `trt discover` and `trt board info <address>` show the same status values;
`board info` adds port, revision, protocol, serial and capabilities. Board address, Board ID,
HWID and Application ID are explained in TRT-core `docs/hwid-and-firmware-update.md`.

---

## trt discover

Force a rescan for connected boards on all active transports.

```bash
trt discover
```

Enumerates available serial ports, probes each port with TRT protocol frames, and prints the
same table as `trt boards`.

---

## trt board

Inspect and update one board.  All sub-commands take the board address shown by `trt boards`.

```bash
trt board <sub-command> <address> [options]
```

### trt board \<id\> info

Display one board: first the same status block as its `trt boards` row, then details.

```bash
trt board info 201
```

```
+------------------------ Board 201 -------------------------+
|   Address        201                                       |
|   Name           am-modulation (STM32)                     |
|   Firmware       0.1.0  build 000001                       |
|   Application    app_0002_analog_family                    |
|   HWID           0010 / 0010  (read 2 / expected 2)        |
|   Status         MATCH  application matches the hardware   |
+------------------------------------------------------------+
+------------- Details -------------+
|   Port            COM9            |
|   Revision        STM32L073RZ     |
|   Protocol        1               |
|   Serial          am-modulation   |
|   Capabilities    SYSTEM          |
+-----------------------------------+
```

On a mismatch the HWID line reads `0010 / 0000  (read 2 / expected 0)`, the status
`MISMATCH  application is for other hardware`, and a final line says
`Board 201: update required. Run trt board update 201`.

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
