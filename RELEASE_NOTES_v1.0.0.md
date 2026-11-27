# TRT-CLI 1.0.0 (release candidate 1: `1.0.0rc1`)

TRT-CLI is the host-side command line for the TRT ecosystem: it discovers TRT boards on serial
ports, talks the TRT v0.1 protocol to the TRT-Core firmware running on them, and drives the
STM32 build and flash workflow. This is a **Beta** release candidate: the CLI is feature-complete
for 1.0.0, but it has been exercised end to end on real hardware only with an Arduino Uno, and the
firmware side (TRT-Core) has open items listed under [Known limitations](#known-limitations).

## Major features

- **Discovery**: `trt discover` probes every serial port with TRT v0.1 frames and lists compatible
  boards; `trt boards` shows the result. Found boards are cached (port and baud rate) in
  `~/.trt/boards.json` so later commands need no `--port`.
- **Board queries**: `trt board info <id>` and read-only queries (`version`, `build-id`, `name`,
  `type`, `revision`, `id`, `runtime`, `active-program`, `uptime`, `transport`). A firmware that
  predates a query reports "unsupported" (exit code 2).
- **Heartbeat**: `trt listen` and `trt board listen <id>` print the `HEARTBEAT` event every TRT-Core
  board emits about once per second. Request/response commands skip event frames while waiting for
  their reply.
- **STM32 workflow**: `trt list-programs stm32`, `trt build stm32 [program]`, `trt flash stm32
  [program]`, and `trt stm32 test` (see below).
- **Protocol tools**: `trt protocol info|version`, plus mock-backed `lcd`, `led` and `board` hardware
  groups used for development and tests.

## HWID architecture

The 4-bit HWID is the module-family code read from the daughter board's strap lines. The CLI does
not read it; it controls how firmware uses it:

- `trt build stm32` (no application) builds the **common image**: at startup the firmware reads the
  HWID and runs the application registered for it.
- `trt build stm32 <application>` builds a development image that always runs that application and
  skips HWID selection.
- `trt build stm32 --hwid 0x2` makes a board with no HWID lines (the NUCLEO) report that HWID, to
  simulate a daughter board.

The firmware reports the selected application, and any selection error, through
`trt board active-program` (for example `app_0000_idle:hwid_fault`).

## Discovery workflow

1. `trt discover` scans ports and caches each board's address and port.
2. `trt boards` lists them; `trt board <query> <id>` resolves the cached port (or rescans).
3. `trt stm32 test` now **discovers the board automatically** and uses its address. With one board
   it just works; with several it lists them and asks for `--board-id` (and `--port`) instead of
   guessing; with none discovered it keeps the previous behaviour (scan ports, address `0x0002`).
   `--board-id` always skips discovery.

Terminology: the "board id" in the CLI is the protocol `BOARD_ID` node address (101, 201, ...). It is
not the hardware-platform Board ID, a HWID or an Application ID.

## Mode architecture

In this release a "mode" is a firmware **application** (`app_<id>_<name>`, 4-digit hexadecimal ID),
selected by HWID through each application's `hwid_family`. The CLI accepts an application by full
name or by ID (`0003`, `0x0003`). A unified numeric mode format (`0x02`, `0b0010`, `0002` all
meaning the same mode), a Base/Service boot split and HWID error handling in firmware are designed
but not implemented; see the v1.0.1 plan in the TRT documentation.

## Update workflow

- **Firmware**: build and flash are separate steps. `trt build stm32` produces
  `artifacts/<name>/<name>.elf` and never flashes; `trt flash stm32 [program]` flashes a stored
  build with `STM32_Programmer_CLI` over SWD and never builds. `trt flash stm32 --platformio` keeps
  the legacy PlatformIO path.
- **CLI**: `trt update` checks for a newer TRT-CLI. Release checking against GitHub and automatic
  installation are scaffolded and not active in this release; `trt update` reports "no update
  available". Release candidates (`1.0.0rc1`) compare correctly: `1.0.0` is newer than `1.0.0rc1`.
- A `trt board <id> update` command does not exist yet.

## Reliability improvements

- Event frames (heartbeat) are skipped while waiting for a command reply.
- The board cache is written atomically (temporary file, then replace).
- `trt stm32 test` no longer needs a hard-coded address and never guesses between boards.
- Update-version comparison accepts pre-release suffixes (`rc1`, `-beta.1`).

## Testing improvements

- 109 tests pass without any hardware (78% line coverage); 5 tests that need an Arduino Uno on COM4
  are marked `hardware` and skipped unless `TRT_HARDWARE_TESTS=1`.
- Tests no longer read or write the real `~/.trt/boards.json`; the cache is redirected to a
  temporary file for every test.
- New tests cover `trt stm32 test` discovery (one board, several boards, STM32 preference, explicit
  address) and release-candidate version comparison.

## Packaging improvements

- Version `1.0.0rc1` (PEP 440); trove classifier **Development Status :: 4 - Beta**.
- The undocumented developer-only `trt --dev` area (three placeholder commands) was removed, so
  nothing internal ships in the wheel.
- README, QUICKSTART, `docs/cli-reference.md` and `trt help` were checked against the actual
  commands; the clone URL, STM32 workflow and `build`/`flash` descriptions were corrected.

## Known limitations

- Hardware validation covers the Arduino Uno. STM32 and ESP32 firmware are covered by simulated
  transports only in this repository; the TRT documentation records no real-hardware run for them.
- TRT protocol v0.1 uses CRC `0x0000`; CRC16 integration is not done in the CLI or TRT-Core.
- `trt board status` reads the discovery cache; it does not query the board.
- `lcd`, `led` and most `board` hardware sub-commands (gpio, pwm, adc, dac, i2c, spi) run against the
  mock transport and are not available against real boards.
- No Base/Service mode, no hardware Reset-button service entry, no HWID timeout/fault policy beyond
  what the firmware does today.
- `trt update` does not yet contact GitHub; `trt board <id> update` does not exist.
- The STM32 build needs `cmake` and `arm-none-eabi-gcc`; flashing needs `STM32_Programmer_CLI`.
- No CI is configured in this repository.

## Roadmap

- **1.0.0**: final release after the release candidate is confirmed on hardware.
- **1.0.1**: unified mode identifiers (`0x02` = `0b0010` = `0002`), Base/Service boot paths,
  bounded HWID read with fault-to-Service fallback, reset-button preparation, cross-platform
  alignment of Arduino/ESP32 with STM32.
- **1.1.0**: modes become functional hardware controllers (input events, host agent, PC actions such
  as macro keys and media control), board firmware update from the CLI, CRC16.
