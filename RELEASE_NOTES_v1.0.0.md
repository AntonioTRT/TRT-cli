# TRT-CLI 1.0.0 (release candidate)

TRT-CLI is the host-side command line for the TRT ecosystem. It discovers TRT boards on serial
ports, reads their identity, HWID and active mode, updates STM32 firmware to match the HWID, and
monitors heartbeats. The complete change list is in [CHANGELOG.md](CHANGELOG.md); this page is the
summary.

## Major features

- **Discovery and status view**: `trt discover`, `trt boards` and `trt board info <address>` show one
  status view per board: address, name, firmware build, mode, HWID `read / expected` and
  `MATCH` / `MISMATCH` / `NO HWID` / `NO MODE`, with the command to run when action is needed.
- **Board queries**: `trt board hwid <address>`, `trt board mode <address>` and the read-only queries
  (`version`, `build-id`, `name`, `type`, `revision`, `id`, `runtime`, `uptime`, `transport`). Older
  firmware answers "unsupported", which the CLI handles.
- **Heartbeat monitoring**: `trt listen` and `trt board listen <address>`, with automatic recovery
  when a request collides with a heartbeat.
- **Help in three levels**: `trt` (Quick Start), `trt --help` (commands by purpose) and `trt help`
  (concepts and workflow).

## HWID architecture

The 4-bit HWID is the module-family code read by the board from its daughter-board lines. The CLI
reads it (`trt board hwid`) and compares it with the mode installed on the board. The result is the
`MATCH` / `MISMATCH` state shown everywhere.

## Mode architecture

STM32 firmware is built as `mode_<ID>_<name>`; the mode ID equals the HWID family code
(TRT_CHAINING_SPEC_v0.1, D-09). `trt list-modes stm32`, `trt build stm32 <mode>` and
`trt flash stm32 [mode]` work with modes. `trt list-programs` and `trt board active-program` remain
as hidden aliases of the earlier terminology.

## Discovery workflow

`discover -> boards -> info -> hwid -> update -> MATCH -> listen`. The same workflow appears in all
three help levels. `trt stm32 test` discovers the board by itself and uses its address; with
several boards it lists them and asks for `--board-id` (and `--port`) instead of guessing, and when
nothing is discovered it keeps the previous default (`0x0002`, the legacy PlatformIO image). An
explicit `--board-id` always skips discovery.

## Update workflow

`trt board update <address> [--check]` compares the board's HWID with its installed mode. If they
differ it builds the matching STM32 mode, flashes it (verify + reset), waits for the reboot and
verifies `MATCH`. `--check` only reports (exit 0 for MATCH, 1 otherwise, 2 when the firmware has no
HWID). STM32 over SWD only, one ST-LINK at a time. `trt update` is the separate self-update check
for the CLI itself.

## Reliability improvements

- A request lost to a heartbeat collision is sent again (up to 2 retries, only when the board is
  evidently alive); late replies to earlier requests are ignored by sequence ID.
- Console safety: all output is ASCII, so Windows consoles without UTF-8 no longer crash.
- Piping into a reader that stops early (`trt help | head`) exits quietly.
- Tracebacks of unexpected errors no longer print local variables.

## Testing improvements

- `pytest` runs without hardware; `pytest -m hardware` runs against a real board
  (`TRT_TEST_BOARD` selects the address).
- Console-safety tests (cp1252 and ASCII consoles) and `trt stm32 test` discovery tests.
- CI on Windows, Linux and macOS: ruff, mypy, pytest and a wheel build.

## Packaging improvements

- Dependency `typer` (the `typer[all]` extra no longer exists), SPDX license expression,
  setuptools >= 77, project URLs, development status Production/Stable.
- Documentation reorganised into current behaviour (`docs/`), future design (`docs/design/`) and
  archive (`docs/archive/`).

## Known limitations

- `trt board update` supports STM32 over SWD only.
- `trt update` (self-update) reports the installed version; it does not check GitHub releases yet.
- Hardware validation was done on Windows with an STM32 NUCLEO-L073RZ; Linux and macOS are covered
  by CI tests only. Arduino and ESP32 are not validated with this release.
- Firmware-side reservations are listed in TRT-core `docs/release-1.0-readiness.md`.
- Simulated or outdated commands are hidden from help: `lcd`, `led`, `protocol`, and the board
  peripheral commands (`gpio`, `pwm`, `adc`, `dac`, `i2c`, `spi`, ...).

## Roadmap

- **1.0.1**: unified mode identifiers (`0x02`, `0b0010` and `0002` mean the same mode), Base/Service
  boot paths, bounded HWID read with fallback to Service, reset-button preparation, alignment of
  Arduino and ESP32 with STM32.
- **1.1.0**: modes become functional hardware controllers (input events, host agent, PC actions),
  CRC16, board update for more platforms.
