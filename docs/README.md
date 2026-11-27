# TRT-CLI documentation

Each document belongs to one of three kinds. Read **Current** to use or change the CLI.

## Current - what exists today

| Document | Contents |
|---|---|
| [cli-reference.md](cli-reference.md) | Every command, option, output and exit code |
| [architecture.md](architecture.md) | Layers, dependency direction, where each feature lives |
| [adding-commands.md](adding-commands.md) | How to add a `trt` command |
| [../README.md](../README.md), [../QUICKSTART.md](../QUICKSTART.md) | Installation, first steps, troubleshooting |
| [../CHANGELOG.md](../CHANGELOG.md) | Release notes |

The implemented TRT protocol (V0.1) and the firmware side (modes, HWID, update workflow) are
documented in the TRT-core repository: `docs/protocol-v0.1-wire-format.md`,
`docs/command-identifiers.md`, `docs/modes.md`, `docs/hwid-and-firmware-update.md`.

## Design - future architecture, not implemented

| Document | Contents |
|---|---|
| [design/vision.md](design/vision.md) | Mission, goals and long-term roadmap |
| [design/trt-protocol-v1.md](design/trt-protocol-v1.md) | Broader protocol design (V1): shares the V0.1 frame layout; its command set, debug flags and CLI examples are not implemented |

## Archive - historical, superseded

| Document | Contents |
|---|---|
| [archive/future-protocol.md](archive/future-protocol.md) | Early protocol sketch (magic `TR` frame), never implemented |
