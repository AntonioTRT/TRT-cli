# Changelog

## Unreleased

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
