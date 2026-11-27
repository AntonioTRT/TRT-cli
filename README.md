# TRT-CLI - Tool Runtime Terminal

`trt` is the command-line tool of **TRT**: it discovers TRT boards on the serial ports, checks that
the firmware mode installed on each board matches the daughter board connected to it (HWID), installs
the right mode when it does not, and monitors the boards.

```text
trt discover -> trt boards -> trt board info -> trt board hwid -> trt board update -> MATCH -> trt listen
```

**Status: Version 1.0.0 milestone (2026-11-26).** The full workflow above is validated on an STM32
NUCLEO-L073RZ. Open limitations are listed under [Status](#status).

---

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [First steps](#first-steps)
- [Concepts](#concepts)
- [Commands](#commands)
- [STM32 firmware (build, flash, update)](#stm32-firmware-build-flash-update)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Status](#status)
- [Documentation](#documentation)

---

## Requirements

| What | Needed for | Notes |
|---|---|---|
| Python **3.13** or newer | Everything | `python --version` |
| `typer`, `rich`, `pyserial` | Everything | Installed automatically by `pip install -e .` |
| A TRT board on USB/serial | Talking to hardware | Any board running TRT-Core (STM32 NUCLEO-L073RZ, Arduino Uno, ESP32) |
| [TRT-core](https://github.com/AntonioTRT/TRT-core) repository | `trt list-modes`, `trt build`, `trt flash`, `trt board update` | Clone it **next to** TRT-CLI (see below) |
| STM32CubeIDE (provides `cmake`, `ninja`, `arm-none-eabi-gcc`, `STM32_Programmer_CLI`) | Building and flashing STM32 modes | Found automatically in its default install folder (`C:\ST`, `/opt/st`, `~/st`, `/Applications`), or put the tools on `PATH` |
| ST-LINK probe (on-board on NUCLEO boards) | Flashing STM32 | Same USB cable as the serial port on a NUCLEO |
| PlatformIO Core | Only `trt flash stm32 --platformio` (legacy project) | `python -m pip install platformio` |

Board discovery, queries and `trt listen` need only Python and the three packages.

---

## Installation

```powershell
# 1. Get the code. TRT-core next to TRT-cli lets the CLI find the firmware project automatically.
mkdir trt && cd trt
git clone https://github.com/AntonioTRT/TRT-cli.git
git clone https://github.com/AntonioTRT/TRT-core.git      # optional: firmware build / flash / update

# 2. Create and activate a virtual environment (recommended)
cd TRT-cli
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Linux / macOS

# 3. Install trt (editable: a later "git pull" takes effect immediately)
python -m pip install -e .

# 4. Check
trt version
trt
```

`trt version` prints `TRT CLI  Version: 1.0.0`; `trt` alone prints the Quick Start. If `trt` is not
found, see [Troubleshooting](#troubleshooting). For development tools (tests, coverage, linters)
install `python -m pip install -e ".[dev]"`.

---

## First steps

Connect a board, then:

```powershell
trt discover               # scan serial ports, list TRT boards
trt boards                 # the same table, from a fresh scan
trt board info 201         # one board in detail (201 = the address shown by trt boards)
trt board update 201       # only if the status is MISMATCH: install the matching mode
trt listen                 # heartbeat from every board, Ctrl+C to stop
```

`trt boards` on an STM32 carrier with an analog daughter board:

```text
Connected Boards
Addr  Name           Firmware       Mode              HWID         Status
201   am-modulation  0.1.0 #000001  mode_0002_analog  0010 / 0010  MATCH
HWID: read from hardware / expected by the installed mode
```

The same board with the wrong mode installed:

```text
Connected Boards
Addr  Name           Firmware       Mode            HWID         Status
201   am-modulation  0.1.0 #000001  mode_0000_base  0010 / 0000  MISMATCH
HWID: read from hardware / expected by the installed mode
  Board 201: update required. Run trt board update 201
```

`trt board update 201` then builds `mode_0002_analog`, flashes it, waits for the reboot and verifies
`0010 / 0010  MATCH` (about 16 s). `trt listen` prints `Board 201: HEARTBEAT` once per second.

Help comes in three levels: `trt` (Quick Start), `trt --help` (all commands grouped by purpose) and
`trt help` (concepts, MATCH / MISMATCH, workflow, heartbeat). Every command also has
`trt <command> --help`.

---

## Concepts

Four identifiers that must not be mixed:

| Term | What it identifies | Example | Where you see it |
|---|---|---|---|
| **Address** (board address) | The TRT node: how the CLI reaches a board. The number in every board command. Not a hardware identifier. | `201` | `trt boards` column `Addr`; `trt board info 201` |
| **HWID** | The **daughter board** connected to the carrier: a 4-bit family code read at boot. | `0010` (= 2) | `trt board hwid 201` |
| **Board ID** | The **carrier board**, to select its profile. **Future**: not implemented (planned: ADC resistor divider). | - | Today the carrier shows as name / type / revision in `trt board info` |
| **Mode ID** | The **firmware** installed: mode `mode_<ID>_<name>`, where the ID is the HWID the mode is written for. | `mode_0002_analog` | `trt board mode 201` |

A board is correct when **HWID read = mode ID of the installed mode**.

| HWID | Mode | | HWID | Meaning |
|---|---|---|---|---|
| `0000` | `mode_0000_base` (Base Mode) | | `0001` | Self-describing module (descriptor), no mode |
| `0010` | `mode_0002_analog` | | `1000`-`1011` | Reserved |
| `0011` | `mode_0003_keypad` | | `1100` | `mode_0012_blink` (test, never in production) |
| `0100` | `mode_0004_encoder` | | `1101` | Experimental |
| `0101` | `mode_0005_display_i2c` | | `1110` | Factory test fixture |
| `0110` | `mode_0006_display_spi` | | `1111` | Fault / invalid |
| `0111` | `mode_0007_led` | | | |

**Base Mode (`0000`)** is not a normal mode: it is the TRT recovery and maintenance runtime that every
firmware image contains (discovery, board information, HWID, heartbeat, update). A carrier with no
daughter board reads HWID `0000` and runs Base Mode alone: `0000 / 0000  MATCH`.

**Status values:** `MATCH` (nothing to do), `MISMATCH` (run `trt board update`), `NO MODE` (the
firmware reports no `mode_<ID>_*` name, e.g. an older image: run `trt board update`), `NO HWID` (the
firmware cannot read the HWID: see the bootstrap below).

---

## Commands

| Group | Command | What it does |
|---|---|---|
| Discovery | `trt discover` | Scan serial ports, print the board table |
| | `trt boards` | Board table: address, name, firmware #build, mode, HWID read / expected, status |
| Board management | `trt board info <address>` | Status block (same values as `trt boards`) plus port, revision, protocol, capabilities |
| | `trt board hwid <address>` | HWID of the connected daughter board |
| | `trt board mode <address>` | Mode installed in the firmware |
| | `trt board update <address> [--check]` | Install the mode that matches the HWID and verify it; `--check` only reports (exit 0 = MATCH, 1 = not MATCH) |
| | `trt board <query> <address>` | One value: `name`, `type`, `revision`, `version`, `build-id`, `runtime`, `uptime`, `id`, `transport`, `capabilities` |
| Monitoring | `trt listen` | Heartbeat and events from all boards (Ctrl+C) |
| | `trt board listen <address>` | The same for one board |
| Development | `trt list-modes stm32` | Modes in the TRT-core STM32 project |
| | `trt build stm32 <mode>` | Build one mode (no flashing) |
| | `trt flash stm32 [mode]` | Flash the latest (or the named) build over ST-LINK |
| | `trt stm32 test --board-id <address>` | Protocol self-test of an STM32 board (six V0.1 commands) |
| Information | `trt`, `trt --help`, `trt help` | Quick Start, grouped command list, full reference |
| | `trt version` | CLI version |
| | `trt update` | Check for a newer TRT-CLI (the CLI itself, not a board) |

Board commands take `--port COMx` to skip discovery. Details for every command, options and exit codes:
[docs/cli-reference.md](docs/cli-reference.md). Older names `trt list-programs` and
`trt board active-program` still work as hidden aliases.

---

## STM32 firmware (build, flash, update)

`trt list-modes`, `trt build`, `trt flash` and `trt board update` work on the STM32CubeIDE project in
the TRT-core repository (`TRT-core/TRT-stm32/am modulation`). The CLI finds it when TRT-core is cloned
next to TRT-CLI or when you run the command from inside TRT-core; otherwise pass `--project-dir PATH`.

```powershell
trt list-modes stm32                  # mode_0000_base, mode_0002_analog, ..., mode_0012_blink
trt build stm32 mode_0002_analog      # build only
trt flash stm32                       # flash the latest build (verify + reset)
trt board update 201                  # or let the CLI pick, build, flash and verify the mode
trt stm32 test --port COM9 --board-id 201
```

**First time on a board without HWID support** (`NO HWID`, e.g. a NUCLEO with older firmware):

```powershell
trt build stm32 mode_0000_base
trt flash stm32
trt discover                          # the board now answers as 201
trt board update 201
```

`trt flash stm32 --platformio` builds and uploads the legacy PlatformIO project (`TRT-stm32/src`,
address 2) and needs PlatformIO. `trt board update` supports STM32 boards only for now.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `'trt' is not recognized` | The Python `Scripts` folder is not on `PATH`. Activate the virtual environment, or use `python -m trt`. |
| `Found 0 board(s)` | Board not connected, or its port is open in another program (serial monitor, `trt listen` in another window). Close it and run `trt discover` again. Check the COM port in Device Manager. |
| `could not open port 'COMx'` / port busy | Only one program can use a serial port. Stop `trt listen` (Ctrl+C) and close serial monitors. |
| `No TRT response received ... after 3 attempts (only event frames)` | The board sends heartbeats but does not answer. (A request lost to a heartbeat collision is resent automatically; this message means all attempts failed.) The board is not receiving: reset it, and if it persists reflash it (`trt board update`). |
| `NO HWID` / `update` exits with code 2 | The firmware predates HWID support: do the bootstrap above once. |
| `NO MODE` | The firmware reports no `mode_<ID>_*` name (older image, Arduino/ESP32 sketch). On STM32, `trt board update` installs the right mode. |
| `No mode for HWID n` | No mode exists for that daughter-board code (e.g. `0001`, reserved codes, `1111` = fault). Check the wiring / daughter board. |
| `Missing build tools` / `STM32_Programmer_CLI not found` | Install STM32CubeIDE (default `C:\ST`) or put the tools on `PATH`. |
| `Could not locate the STM32CubeIDE project` | Clone TRT-core next to TRT-CLI, run from inside TRT-core, or pass `--project-dir`. |
| `trt stm32 test`: `Response board id is 0x00C9; expected 0x0002` | The default address is the legacy `0x0002`; current firmware answers as 201: add `--board-id 201`. |
| `unrecognized arguments: --cov=...` when running `pytest` | Install the dev extras: `python -m pip install -e ".[dev]"`. |
| Linux: `Permission denied: '/dev/ttyACM0'` | Add your user to the serial group and log in again: `sudo usermod -aG dialout $USER` (`uucp` on Arch). |
| `trt help \| more` stops early | Expected: `trt` exits quietly when the reader closes the pipe. |
| PlatformIO certificate errors on a corporate network | `python -m pip install truststore` (used by the TRT-core upload tooling). |

Discovered boards are cached in `%USERPROFILE%\.trt\boards.json` (address, port, baud rate); the
`TRT_CLI_BOARD_CACHE` environment variable selects another file. Delete it to force a fresh scan for
board commands.

---

## Development

```powershell
python -m pip install -e ".[dev]"     # pytest, pytest-cov, mypy (+ types-pyserial), ruff, black, isort
pytest                                 # all tests that need no hardware, with coverage
pytest -m hardware                     # tests against a real board (address 101 by default)
$env:TRT_TEST_BOARD = "201"; pytest -m hardware    # another board address (PowerShell)
ruff check src tests                   # lint: must pass
mypy src                               # type check: must pass
```

A plain `pytest` never opens a serial port: tests marked `hardware` are deselected, and every other
test runs with no serial ports and a temporary board cache (`tests/conftest.py`). CI
(`.github/workflows/ci.yml`) runs lint, type check, tests and a wheel build on Windows, Linux and
macOS. To add a command, see [docs/adding-commands.md](docs/adding-commands.md).

Code layout (dependencies point downwards):

```text
src/trt/cli.py, commands/   Typer commands and Rich output (no business logic)
src/trt/services/           Discovery, queries, board status summary, update workflow, listen, build
src/trt/protocol/           TRT V0.1 frames: typed requests/responses, INFO decoding
src/trt/transport/          SerialTransport (real boards), MockTransport (tests), frame reader
src/trt/repositories/       Board registry and the serial connection cache
src/trt/core/               Domain models, modes and HWID rules
```

---

## Status

Validated on hardware (2026-11-26, STM32 NUCLEO-L073RZ with TRT-core): discovery, all board queries,
HWID, MATCH / MISMATCH display, `trt board update` (build, flash, reboot, verify), heartbeat,
`trt stm32 test`. Earlier milestone (2026-09-08): Arduino Uno discovery and `trt board info 101`.

Known limitations:

- `trt board update` supports STM32 over SWD (ST-LINK) only; Arduino and ESP32 firmware has no
  modes or HWID yet, so those boards show `NO MODE`.
- A board with the wrong mode keeps running it until updated (firmware fallback to Base Mode is planned).
- `trt lcd`, `trt led`, `trt protocol` and the board peripheral commands (`gpio`, `pwm`, `adc`, `dac`,
  `i2c`, `spi`, `debug`, ...) are simulated and hidden from the help screens.
- `trt update` (self-update) only reports the installed version for now.
- Hardware runs are on Windows; Linux and macOS are covered by the CI test suite but not yet by a
  run against a real board.
- Milestone reservations: TRT-core `docs/release-1.0-readiness.md`.

---

## Documentation

| Document | Contents |
|---|---|
| [docs/cli-reference.md](docs/cli-reference.md) | Every command, options, outputs, exit codes |
| [QUICKSTART.md](QUICKSTART.md) | Step-by-step first run on Windows (Spanish) |
| [docs/adding-commands.md](docs/adding-commands.md) | How to add a `trt` command |
| [docs/architecture.md](docs/architecture.md) | Layered architecture and dependency flow |
| [docs/README.md](docs/README.md) | Documentation index: current behaviour, future design, historical notes |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| TRT-core `docs/modes.md`, `docs/hwid-and-firmware-update.md` | Modes, HWID and the update workflow (firmware side) |
| TRT-core `docs/protocol-v0.1-wire-format.md`, `docs/command-identifiers.md` | The implemented TRT protocol |
| [docs/design/](docs/design/) | **Future** architecture: vision and the V1 protocol design (not implemented) |
| [docs/archive/](docs/archive/) | **Historical** design notes, superseded |

## License

MIT - see [LICENSE](LICENSE).
