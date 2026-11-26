# Changelog

## Unreleased

- Help reorganised around the board workflow (discover -> boards -> info -> hwid -> update -> MATCH -> listen): `trt` alone prints a Quick Start; `trt --help` groups commands into Board Discovery, Board Management, Monitoring, Development and Information; `trt help` is the full reference with concepts (Board Address, Board ID, HWID, Application ID), MATCH / MISMATCH examples, typical workflow and heartbeat. Help text is plain ASCII.
- Hidden from the help screens (still callable): `lcd`, `led` (simulated), `protocol` (outdated placeholder), and the simulated `board gpio/pwm/adc/dac/i2c/spi/debug/modules/reset/reboot/status`.
- User-facing text calls the number in board commands the board *address* (`ADDRESS` / `<address>`; `Addr` column, `Address` row); Board ID now means the carrier-board identifier (not implemented yet).
- Added `trt listen` and `trt board listen <address>` to passively print asynchronous board messages.
- Handles the TRT-Core HEARTBEAT event (FLAGS `0x02`, COMMAND `0x9001`), printed as `Board <address>: HEARTBEAT`.
- Request/response exchanges now skip event frames while waiting for a reply.
- Added `trt board hwid <address>` (HWID query `0x000B`) and `trt board update <address> [--check]`: compares the board's HWID with its installed application and, on mismatch, builds, flashes, waits for the reboot and verifies the matching STM32 application.
- `trt boards`, `trt discover` and `trt board info <address>` show the same status per board: name, firmware + build, installed application, HWID `read / expected` (e.g. `0010 / 0010`) and `MATCH` / `MISMATCH` / `NO HWID` / `NO APP`, plus the `trt board update <address>` hint when action is needed. `trt discover` now prints the `trt boards` table; `trt board info` prints the status block followed by port, revision, protocol, serial and capabilities. Discovery and `board info` also query HWID and ACTIVE_PROGRAM (NACKed by older firmware).
- STM32 applications are named `app_<HWID>_<name>` (was `program_<name>`); `build`, `flash` and `list-programs` follow the new naming.
- `build stm32` / `flash stm32` find `cmake`, `ninja`, `arm-none-eabi-gcc` and `STM32_Programmer_CLI` in an STM32CubeIDE install under `C:\ST` when they are not on `PATH`.

## 1.0.0 - 2026-09-08

TRT-CLI 1.0.0 is the first hardware-validated release.

Why this release is 1.0.0:

- First real hardware communication implemented.
- First real TRT protocol transaction validated.
- Arduino Uno end-to-end communication works over COM4.
- `trt board info 101` opens COM4, sends TRT frames, receives firmware responses, decodes them, and displays board information.
- Mock-only status no longer applies to board discovery and board info.

Validated response:

```text
Board ID      101
BOARD_INFO    UNSPECIFIED
FW_VERSION    0.1.0
BUILD_ID      000004
```
