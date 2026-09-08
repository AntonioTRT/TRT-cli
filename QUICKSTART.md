# TRT CLI - Quick Reference

## Installation

```bash
pip install -e .
```

Installation status:

```text
Package: trt-cli 1.0.0
Python: 3.13+
Dependencies: Typer, Rich, pyserial
Entry point: trt
Validated hardware: Arduino Uno on COM4 running TRT-Core firmware
```

## Core Commands

```bash
trt help
trt version
trt discover
trt boards
trt board info 101
trt board capabilities 101
```

## Validated Hardware Path

```text
TRT-CLI -> COM4 -> Arduino Uno -> TRT-Core -> real protocol response
```

`trt board info 101` returns real firmware data:

```text
Board ID      101
BOARD_INFO    UNSPECIFIED
FW_VERSION    0.1.0
BUILD_ID      000004
```

## Development

```bash
pytest
```
