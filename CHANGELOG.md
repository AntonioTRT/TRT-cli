# Changelog

All notable changes to TRT-CLI. Dates are YYYY-MM-DD.

## 1.0.0 - release candidate (2026-11-26)

First public release. Validated end to end on an STM32 NUCLEO-L073RZ with TRT-Core: discovery, board
queries, HWID, MATCH / MISMATCH, the HWID-driven firmware update and heartbeat monitoring.
Requires Python 3.13+. Firmware-side reservations: TRT-core `docs/release-1.0-readiness.md`.

### Added

- `trt board update <address> [--check]`: compares the board's HWID with its installed mode and, if they
  differ, builds the matching STM32 mode, flashes it (verify + reset), waits for the reboot and verifies
  MATCH. `--check` only reports (exit 0 MATCH, 1 otherwise; 2 when the firmware has no HWID).
- `trt board hwid <address>` (HWID query `0x000B`) and `trt board mode <address>` (ACTIVE_MODE `0x000A`).
- One status view in `trt boards`, `trt discover` and `trt board info`: address, name, firmware #build,
  mode, HWID `read / expected` (e.g. `0010 / 0010`) and `MATCH` / `MISMATCH` / `NO HWID` / `NO MODE`,
  with the command to run when action is needed.
- Modes: STM32 firmware is `mode_<ID>_<name>`, mode ID = HWID family code (TRT_CHAINING_SPEC_v0.1
  D-09). `trt list-modes stm32`, `trt build stm32 <mode>`, `trt flash stm32 [mode]`.
- Help in three levels: `trt` (Quick Start), `trt --help` (commands grouped by purpose), `trt help`
  (concepts, MATCH / MISMATCH, workflow, heartbeat). The workflow
  `discover -> boards -> info -> hwid -> update -> MATCH -> listen` appears identically in all three.
- `trt listen` and `trt board listen <address>`: passive monitoring of HEARTBEAT (`0x9001`) and events.
- STM32CubeIDE's bundled toolchain is found automatically (Windows `C:\ST`, Linux `/opt/st` and `~/st`,
  macOS `/Applications`) when the tools are not on `PATH`.
- Automatic recovery from heartbeat collisions: a request lost while the board was sending a
  heartbeat is sent again (up to 2 retries, only when the board is evidently alive); late replies to
  earlier requests are ignored by sequence ID; each attempt is time-bounded.
- Test suite separation: `pytest` runs without hardware (no serial port is opened); `pytest -m hardware`
  runs against a real board (`TRT_TEST_BOARD` selects the address).
- Console-safety tests: no non-ASCII output strings, and the help and status screens run under cp1252
  and ASCII consoles.
- CI workflow (Windows, Linux, macOS): ruff, mypy, pytest, wheel build. Project URLs in the metadata.

### Changed

Breaking for scripts that parse output or use the earlier STM32 program names.

- Terminology: the number in board commands is the board **address** (`ADDRESS`, column `Addr`);
  **Board ID** is reserved for the future carrier-board identifier; "programs" are now **modes**.
  `trt list-programs` and `trt board active-program` remain as hidden aliases.
- `trt` without arguments prints the Quick Start instead of the usage screen.
- `trt discover` prints the `trt boards` table; `trt board info` prints the status block and details.
- Discovery also reads HWID and ACTIVE_MODE (older firmware answers "unsupported", which is handled).
- `trt stm32 test --board-id` help explains the current address 201 versus the legacy default `0x0002`.
- Packaging: dependency `typer` (the `typer[all]` extra no longer exists), SPDX license expression,
  setuptools >= 77, `types-pyserial` in the dev extras, development status Production/Stable.
- Documentation reorganised: current behaviour in `docs/`, future design in `docs/design/`, superseded
  notes in `docs/archive/` (index: `docs/README.md`).

### Fixed

- `trt update` and `trt protocol info` crashed with `UnicodeEncodeError` on Windows consoles without
  UTF-8; all output strings are ASCII.
- Piping output into a reader that stops early (`trt help | head`, `trt listen | grep -m1 HEARTBEAT`)
  printed a traceback; `trt` now exits quietly.
- A lost request waited through up to nine heartbeats (about 9 s) before failing, and a late reply to
  an earlier request failed the next command with "sequence mismatch".
- Tracebacks of unexpected errors no longer print local variables.

### Hidden

Still callable, not shown in help (simulated or outdated): `trt lcd`, `trt led`, `trt protocol`, and the
board peripheral commands `gpio`, `pwm`, `adc`, `dac`, `i2c`, `spi`, `debug`, `modules`, `reset`,
`reboot`, `status`.

### Known limitations

- `trt board update` supports STM32 over SWD only (one ST-LINK at a time).
- `trt update` (self-update) reports the installed version; checking GitHub releases is not implemented.
- Hardware validation was done on Windows; Linux and macOS are covered by CI tests only.

## History before 1.0.0

- **2026-11-26, Version 1.0.0 milestone** (tag `v1.0.0-milestone`, commit `746a961`): HWID and mode
  architecture, board update workflow and help redesign first validated with TRT-Core. Included in the
  1.0.0 release above.
- **2026-09-08, Arduino Uno milestone** (internal build reporting version `1.0.0`, never tagged or
  published): first real TRT protocol transaction. `trt board info 101` opened COM4, sent TRT frames to an
  Arduino Uno running TRT-Core and displayed its identity, firmware version 0.1.0 and build 000004.
