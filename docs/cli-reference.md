# TRT CLI Reference

Every `trt` command, its options, output and exit codes, for TRT-CLI 1.0.0 (Version 1.0.0 milestone,
2026-11-26). Installation and first steps: [README](../README.md).

## Contents

- [Workflow and help levels](#workflow-and-help-levels)
- [Concepts](#concepts)
- [Board discovery](#board-discovery): `discover`, `boards`
- [Board management](#board-management): `board info`, `board hwid`, `board mode`, `board update`, queries, `board capabilities`
- [Monitoring](#monitoring): `listen`, `board listen`
- [Development (STM32)](#development-stm32): `list-modes`, `build`, `flash`, `stm32 test`
- [Information](#information): `help`, `version`, `update`
- [Hidden commands](#hidden-commands)
- [Exit codes](#exit-codes)
- [Files and environment](#files-and-environment)
- [Shell completion](#shell-completion)

---

## Workflow and help levels

```text
trt discover            find the boards on the serial ports
trt boards              address, mode, HWID read / expected, status
trt board info 201      one board in detail
trt board hwid 201      which daughter board is connected
trt board mode 201      which mode is installed
trt board update 201    if MISMATCH: build, flash, reboot, verify
trt boards              confirm MATCH
trt listen              monitor the running board (Ctrl+C)
```

| Command | Shows |
|---|---|
| `trt` | Quick Start: the five workflow commands |
| `trt --help` | All visible commands grouped: Board Discovery, Board Management, Monitoring, Development, Information |
| `trt help` | Full reference: concepts, reading MATCH / MISMATCH, typical workflow, heartbeat, commands |
| `trt <command> --help` | Options of one command |

---

## Concepts

| Term | Identifies | Example |
|---|---|---|
| **Address** (board address) | The TRT node: how the CLI reaches a board, the number in every board command (`ADDRESS`). Not a hardware identifier. | `201` |
| **HWID** | The daughter board: 4-bit family code read from ID pins at boot, shown as the pin pattern (bit 3 ... bit 0). | `0010` (= 2) |
| **Board ID** | The carrier board, to select its profile. **Future**: not implemented (planned: ADC resistor divider). | - |
| **Mode ID** | The firmware: mode `mode_<ID>_<name>`, the ID is the HWID the mode is written for, common to all platforms. | `mode_0002_analog` |

HWID codes (TRT_CHAINING_SPEC_v0.1, decision D-09) and modes:

| HWID | Mode | | HWID | Meaning |
|---|---|---|---|---|
| `0000` | `mode_0000_base` (Base Mode) | | `0001` | Self-describing module (descriptor), no mode |
| `0010` | `mode_0002_analog` | | `1000`-`1011` | Reserved families |
| `0011` | `mode_0003_keypad` | | `1100` | `mode_0012_blink` (experimental, never production) |
| `0100` | `mode_0004_encoder` | | `1101` | Experimental / custom |
| `0101` | `mode_0005_display_i2c` | | `1110` | Factory test fixture |
| `0110` | `mode_0006_display_spi` | | `1111` | Fault / invalid |
| `0111` | `mode_0007_led` | | | |

**Base Mode (`0000`)** is the TRT recovery and maintenance runtime contained in every firmware image
(discovery, information, HWID, heartbeat, update). A carrier without daughter board reads HWID `0000`
and runs Base Mode alone.

**Status** compares *HWID read from the hardware* with *the mode ID of the installed mode*:

| Status | Meaning | Action |
|---|---|---|
| `MATCH` | `0010 / 0010`: the mode fits the hardware | None |
| `MISMATCH` | `0010 / 0000`: the mode is for other hardware | `trt board update <address>` |
| `NO MODE` | `0010 / ----`: the firmware reports no `mode_<ID>_*` name (older image, Arduino/ESP32 sketch) | `trt board update <address>` (STM32) |
| `NO HWID` | `---- / ...`: the firmware cannot read the HWID | One-time bootstrap, see [board update](#trt-board-update) |

---

## Board discovery

### trt discover

Scans every serial port (115200 baud, 8N1), identifies TRT boards and prints the `trt boards` table.
The connection of each board (address, port, baud rate) is saved for later board commands.

```text
  Discovery complete.  Found 1 board(s).

Connected Boards
Addr  Name           Firmware       Mode              HWID         Status
201   am-modulation  0.1.0 #000001  mode_0002_analog  0010 / 0010  MATCH
HWID: read from hardware / expected by the installed mode
```

With no board: `Found 0 board(s).` Discovery first sends PING + INFO; firmware without PING is found
by a second probe (BOARD_VERSION, FW_VERSION, CAPABILITIES, BUILD_ID).

### trt boards

Rescans and prints the board table. Columns: `Addr` (address), `Name`, `Firmware` (version
`#build`), `Mode`, `HWID` (read / expected), `Status`. Every board that needs action gets a line
below the table, e.g. `Board 201: update required. Run trt board update 201`.

---

## Board management

All board commands take the board `ADDRESS` (shown by `trt boards`, decimal `201` or hex `0xC9`) and,
except `capabilities` and `listen`, `--port / -p COMx` to skip the saved connection and discovery.

### trt board info

```powershell
trt board info 201 [--port COM9]
```

```text
+------------------------ Board 201 -------------------------+
|   Address        201                                       |
|   Name           am-modulation (STM32)                     |
|   Firmware       0.1.0  build 000001                       |
|   Mode           mode_0002_analog                          |
|   HWID           0010 / 0010  (read 2 / expected 2)        |
|   Status         MATCH  mode matches the hardware          |
+------------------------------------------------------------+
+------------- Details -------------+
|   Port            COM9            |
|   Revision        STM32L073RZ     |
|   Protocol        1               |
|   Serial          am-modulation   |
|   Capabilities    SYSTEM          |
+-----------------------------------+
```

The status block has the same values as the board's row in `trt boards`; the Details panel exists only
here.

### trt board hwid / trt board mode

```powershell
trt board hwid 201        #   201  hwid: 2
trt board mode 201        #   201  mode: mode_0002_analog
```

`hwid` sends HWID (`0x000B`); `mode` sends ACTIVE_MODE (`0x000A`). `trt board active-program` is a
hidden alias of `mode`.

### trt board update

```powershell
trt board update 201 [--check] [--port COM9] [--project-dir PATH]
```

1. Reads HWID, installed mode and board family over one serial connection.
2. Picks the mode `mode_<HWID>_*` from the TRT-core STM32 project.
3. `MATCH`: prints `No update required.`, exit 0.
4. Otherwise (or with `--check`, which stops here with exit 1): builds the mode, flashes it over
   ST-LINK with verify and reset, waits up to 20 s for the board to answer, re-reads and verifies.

```text
  Board             201 (STM32, COM9)
  HWID              0010 / 0000  MISMATCH  (read / expected)
  Installed mode    mode_0000_base
  Required mode     mode_0002_analog

  MISMATCH - update required: mode_0000_base -> mode_0002_analog.
  ... build and flash output ...
  Waiting for the board to reboot...
  Board             201 (STM32, COM9)
  HWID              0010 / 0010  MATCH  (read / expected)
  Installed mode    mode_0002_analog
  Required mode     mode_0002_analog
  Updated and verified: mode_0002_analog is active.
```

| Exit | Meaning |
|---|---|
| 0 | MATCH, or updated and verified |
| 1 | Not MATCH with `--check`; no mode for the HWID (`No mode for HWID n`); non-STM32 board; build, flash or verification failure |
| 2 | The firmware does not report a HWID; the bootstrap commands are printed |

Bootstrap of a board whose firmware predates HWID support:

```powershell
trt build stm32 mode_0000_base
trt flash stm32
trt discover
trt board update 201
```

Requires the TRT-core repository and the STM32 tools (see [Development](#development-stm32)).
Supports STM32 boards only.

### Single-value queries

```powershell
trt board <query> <address> [--port COMx]
```

| Query | Source | Example value |
|---|---|---|
| `id` | address in the reply frame | `201` |
| `name` | INFO field 0x01 | `am-modulation` |
| `type` | INFO field 0x06 (family) | `STM32` |
| `revision` | BOARD_VERSION | `STM32L073RZ` |
| `version` | FW_VERSION | `0.1.0` |
| `build-id` | BUILD_ID | `000001` |
| `runtime` | RUNTIME | `RUNNING` |
| `uptime` | UPTIME | `00:01:23.456 (83456 ms)` |
| `hwid` | HWID | `2` |
| `mode` | ACTIVE_MODE | `mode_0002_analog` |
| `transport` | the host's connection (no firmware query) | `serial (COM9, 115200 baud)` |

Output: `  201  version: 0.1.0`. A query the firmware does not support prints `unsupported` and exits
with 2; other failures exit with 1.

### trt board capabilities

```powershell
trt board capabilities 201
```

Lists the capabilities the board advertised at discovery (`SYSTEM`, `GPIO`, `DAC`, ...).

---

## Monitoring

### trt listen / trt board listen

```powershell
trt listen                 # all boards on all serial ports
trt board listen 201       # one board
```

Prints what boards send on their own, without sending anything:

```text
  Listening to all boards on COM9  (Ctrl+C to stop)

Board 201: HEARTBEAT
Board 201: HEARTBEAT
```

Every TRT-Core board sends HEARTBEAT (event `0x9001`, FLAGS `0x02`) about once per second. It confirms
that the firmware and TRT-Core are running and that the board -> PC link works; use it after flashing
or rewiring. It does **not** prove that the board receives commands: heartbeats with failing commands
mean the board is not receiving (reset it, or reflash with `trt board update`). A single
`No TRT response received ... (only event frames)` can happen when a request collides with a heartbeat;
repeat the command. Other events print as
`EVENT 0x<id> payload=<hex>`. Stop with Ctrl+C before running other commands: a serial port can be open
in one program only.

---

## Development (STM32)

These commands use the STM32CubeIDE project in the TRT-core repository
(`TRT-core/TRT-stm32/am modulation`). It is found when TRT-core is cloned next to TRT-CLI or when the
command runs inside TRT-core; otherwise pass `--project-dir PATH` (the TRT-stm32 folder or the project).

Tools: `cmake`, `arm-none-eabi-gcc` (and `ninja` if present) for building, `STM32_Programmer_CLI` for
flashing. When they are not on `PATH`, the CLI uses the copies bundled with STM32CubeIDE under
`C:\ST\STM32CubeIDE_*`.

### trt list-modes stm32

```powershell
trt list-modes stm32 [--project-dir PATH]
```

Prints the modes, one per line (`Sources/modes/mode_<ID>_<name>.c`): `mode_0000_base`,
`mode_0002_analog`, `mode_0003_keypad`, `mode_0004_encoder`, `mode_0005_display_i2c`,
`mode_0006_display_spi`, `mode_0007_led`, `mode_0012_blink`. Exit 1 if none is found.
`trt list-programs` is a hidden alias.

### trt build stm32

```powershell
trt build stm32 <mode> [--project-dir PATH]
```

Builds one mode with TRT-Core included in `build/<mode>/` (CubeIDE's `Debug/` is untouched) with
`-DACTIVE_MODE=MODE_<ID>_<NAME>`, stores `artifacts/<mode>/<mode>.elf` and records it in
`artifacts/latest.json`. Never flashes. An unknown name lists the available modes.

### trt flash stm32

```powershell
trt flash stm32 [<mode>] [--project-dir PATH]
trt flash stm32 --platformio [--port COMx] [--project-dir PATH]
```

Flashes a stored build and never builds: with no name the latest (`latest.json`), with a name that
mode's build. Runs `STM32_Programmer_CLI -c port=SWD -w <elf> -v -rst` (write, verify, reset). If
nothing is built it says `Run: trt build stm32 <mode>`.
`--platformio` builds and uploads the legacy PlatformIO project (`TRT-stm32/src`, address 2) with
`python -m platformio`; `--port` applies only there.

### trt stm32 test

```powershell
trt stm32 test [--port COMx] --board-id 201
```

Sends the six TRT V0.1 commands (PING, FW_VERSION, BOARD_VERSION, INFO, STATUS, CAPABILITIES) at
115200 baud, checks every reply and prints a table ending with
`All six protocol commands completed successfully.` Without `--port` it tries every serial port.
`--board-id` defaults to `0x0002` (legacy PlatformIO firmware); the current STM32 firmware answers as
201, so pass `--board-id 201` (otherwise: `Response board id is 0x00C9; expected 0x0002`).

---

## Information

### trt help, trt --help, trt

See [Workflow and help levels](#workflow-and-help-levels). Help text is plain ASCII and fits an
80-column terminal.

### trt version

```text
 TRT CLI
 Version:  1.0.0
```

### trt update

Updates **the TRT-CLI program itself**, not a board (board firmware: `trt board update`).

```powershell
trt update               # check (default)
trt update --check       # same
trt update --install     # check and install if an update exists
```

Today it reports the installed version and install method (pip, pipx, uv); checking GitHub releases
(`AntonioTRT/TRT-cli`) is not implemented yet, so it always ends with `No update available.`

---

## Hidden commands

Callable, but not shown by `trt`, `trt --help`, `trt help` or `trt board --help`:

| Command | Status |
|---|---|
| `trt list-programs ...`, `trt board active-program <address>` | Aliases of `trt list-modes`, `trt board mode` |
| `trt lcd info / reset / clear / write "<text>"` | Simulated: prints `(mock: no hardware connected)` |
| `trt led on / off / blink / brightness <n> / color <r> <g> <b>` | Simulated |
| `trt board gpio list / read / write <address> ...`, `pwm`, `adc`, `dac`, `i2c`, `spi`, `debug`, `modules`, `reset`, `reboot` | Simulated; syntax `trt board <group> <command> <address> [args]`, e.g. `trt board gpio read 201 PA5` |
| `trt board status <address>` | Reads the discovery cache (always `ready`); use `trt boards` / `trt board info` |
| `trt protocol info / version` | Outdated placeholder describing an earlier protocol design; the implemented protocol is TRT-core V0.1 |

---

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (for `board update`: MATCH or updated and verified) |
| 1 | Failure: transport error, board not found, build/flash error, `board update --check` not MATCH |
| 2 | The firmware does not support the requested query (`unsupported`), or `board update` on firmware without HWID; usage errors from the command parser |

---

## Files and environment

| Item | Purpose |
|---|---|
| `%USERPROFILE%\.trt\boards.json` (`~/.trt/boards.json`) | Saved connections (address -> port, baud rate) from `trt discover` |
| `TRT_CLI_BOARD_CACHE` | Use another file for the saved connections |
| `TRT-core/TRT-stm32/am modulation/build/`, `artifacts/` | Build output of `trt build stm32` (git-ignored) |

---

## Shell completion

```powershell
trt --install-completion     # install for the current shell
trt --show-completion        # print the script to install it manually
```
