# Changelog

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
