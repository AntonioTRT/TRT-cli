# Changelog

## 1.0.0rc1 - release candidate

Release notes: [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md).

- Version is now `1.0.0rc1`; development status classifier changed from Alpha to Beta.
- Removed the hidden `trt --dev` developer area (placeholder commands for individual developers).
- `trt stm32 test` discovers the board and uses its address when `--board-id` is omitted; with several
  boards it asks for `--board-id`, with none it keeps the previous default.
- `BoardDiscoveryService.discover_serial` accepts an optional list of ports.
- Update-version comparison understands release candidates (`1.0.0` is newer than `1.0.0rc1`).
- Tests: board cache isolated per test; tests needing a real board are marked `hardware` and skipped
  unless `TRT_HARDWARE_TESTS=1`.
- Docs: README, QUICKSTART, CLI reference and `trt help` corrected (STM32 workflow, clone URL).

Included in 1.0.0rc1 (previously "Unreleased"):

- Added `trt listen` and `trt board listen <id>` to passively print asynchronous board messages.
- Handles the TRT-Core HEARTBEAT event (FLAGS `0x02`, COMMAND `0x9001`), printed as `Board <id>: HEARTBEAT`.
- Request/response exchanges now skip event frames while waiting for a reply.

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

Terminology note (added later): the `Board ID` label in this historical output is the protocol `BOARD_ID` node address, not the hardware-platform Board ID. See `TRT-core/docs/identifiers.md`.
