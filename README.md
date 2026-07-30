# TRT — Tool Runtime Terminal

> **A modular hardware control ecosystem for embedded boards and expansion modules.**

TRT provides a unified, git-style command-line interface for controlling embedded hardware devices — across Windows, Linux, and macOS — through a clean, extensible CLI.

---

## Mission

*TRT makes embedded hardware control feel as natural as running `git status` or `docker ps`.*

Engineers working with embedded boards should not need vendor-specific tools, fragile scripts, or custom one-off terminals.  TRT provides a single entry point — `trt` — that works uniformly across board types, transports, and platforms.

---

## Ecosystem

```
trt-cli        ← you are here
trt-protocol   ← future: binary communication layer
trt-core       ← future: hardware abstraction layer
trt-modules    ← future: firmware module drivers
```

---

## Current Status — Milestone 1 (0.1.0)

| Goal                                 | Status         |
|--------------------------------------|---------------|
| CLI executable (`trt`)               | ✅ Complete    |
| Full command tree scaffolded         | ✅ Complete    |
| Rich help output                     | ✅ Complete    |
| Board models (capability-based)      | ✅ Complete    |
| Mock boards (`boards`, `discover`)   | ✅ Complete    |
| `trt update` command (Phase 1)       | ✅ Complete    |
| Architecture documentation           | ✅ Complete    |
| TRT Protocol V1 specification        | ✅ Complete    |
| Hardware communication               | 🔜 Future      |
| TRT Protocol V1 implementation       | 🔜 Future      |
| `trt update` GitHub check (Phase 2)  | 🔜 Future      |

---

## Installation

```bash
git clone https://github.com/trt-project/trt-cli.git
cd trt-cli
pip install -e .
```

Requires Python 3.13 or later.

---

## Quick Start

```bash
trt help
trt version
trt update
trt boards
trt discover

trt board board0 info
trt board board0 capabilities
trt board board0 gpio list
trt board board0 gpio write PA5 1
trt board board0 pwm set 1 1000 50
trt board board0 adc read 3
trt board board0 i2c scan

trt lcd write "Hello"
trt led color 255 0 0
trt protocol info
```

---

## Command Tree

```
trt
├── help
├── version
├── update
├── boards
├── discover
│
├── board <id>
│   ├── info
│   ├── status
│   ├── reset
│   ├── reboot
│   ├── capabilities
│   ├── modules
│   ├── gpio list | read <pin> | write <pin> <value>
│   ├── pwm  list | start <ch> | stop <ch> | set <ch> <freq> <duty>
│   ├── adc  list | read <ch>
│   ├── dac  list | read <ch> | set <ch> <value>
│   ├── i2c  scan | read | write
│   ├── spi  transfer | config
│   └── debug logs | monitor | shell
│
├── lcd  info | reset | clear | write <text>
├── led  on | off | blink | brightness <n> | color <r> <g> <b>
└── protocol  info | version
```

---

## Board Philosophy

TRT never identifies boards by MCU.  There is no `--stm32` or `--rp2040` flag.

Instead, every board advertises its **capabilities** via firmware:

```json
{
  "board_type": "TRT_CORE",
  "revision":   "A1",
  "firmware":   "0.1.0",
  "serial":     "000001",
  "capabilities": {
    "gpio":  true,
    "pwm":   true,
    "adc":   true,
    "dac":   true,
    "i2c":   true,
    "spi":   true,
    "lcd":   false,
    "relay": false
  }
}
```

This means:
- A TRT_CORE, an Arduino, an RP2040-based board, and a simulator can all be supported by the same CLI without changes.
- Adding a new board type never requires restructuring the command tree.

---

## Project Structure

```
trt-cli/
├── src/trt/
│   ├── cli.py                  — Typer app, command registration
│   ├── version.py              — Version constant
│   ├── commands/
│   │   ├── help.py             — Rich help output
│   │   ├── version.py          — Version command
│   │   ├── boards.py           — boards command
│   │   ├── discover.py         — discover command
│   │   ├── board.py            — board <id> sub-command tree
│   │   ├── lcd.py              — lcd sub-commands
│   │   ├── led.py              — led sub-commands
│   │   └── protocol.py         — protocol sub-commands
│   └── core/
│       └── models.py           — Board, BoardCapabilities, BoardRegistry, …
├── docs/
│   ├── vision.md
│   ├── architecture.md
│   ├── cli-reference.md
│   └── future-protocol.md
└── tests/
    └── test_cli.py
```

---

## Development

```bash
# Run tests
pytest

# Type check
mypy src/

# Lint
ruff check src/
```

---

## Documentation

| Document | Contents |
|-------------------------------------------------|-------------------------------------|
| [docs/vision.md](docs/vision.md) | Mission, goals, roadmap |
| [docs/architecture.md](docs/architecture.md) | System design, layers, extension |
| [docs/trt-protocol.md](docs/trt-protocol.md) | **TRT Protocol V1 specification** (frame structure, fields, transport, open questions) |
| [docs/cli-reference.md](docs/cli-reference.md) | Full command reference with examples |
| [docs/future-protocol.md](docs/future-protocol.md) | Earlier protocol sketch (superseded by trt-protocol.md) |

---

## License

MIT — see [LICENSE](LICENSE).


## Vision

TRT provides a unified, extensible command-line interface for controlling embedded hardware devices across Windows, Linux, and macOS. It enables developers and embedded systems engineers to communicate with microcontrollers, IoT devices, and expansion boards through a clean, modern CLI.

## Project Goals

### Current Milestone (MVP - 0.1.0)
- ✅ Clean, professional repository structure
- ✅ Working CLI executable (`trt`)
- ✅ Core commands: `trt help`, `trt version`, `trt boards`
- ✅ Foundation for future expansion
- ✅ Architecture documentation

### Future Milestones
- **0.2.0**: TRT Protocol implementation
- **0.3.0**: USB communication support
- **0.4.0**: CAN bus support
- **1.0.0**: Full hardware abstraction layer

## Architecture

```
User
  ↓
TRT CLI (trt-cli)
  ↓
TRT Protocol (trt-protocol) - Future
  ↓
Transport Layer (USB / CAN / TCP) - Future
  ↓
TRT Core (trt-core) - Future
  ↓
TRT Modules (trt-modules) - Future
  ↓
Embedded Hardware
```

## Installation

### Prerequisites
- Python 3.13 or higher
- pip

### Development Installation

```bash
git clone https://github.com/trt-project/trt-cli.git
cd trt-cli
pip install -e .
```

### Production Installation

```bash
pip install trt-cli
```

## Quick Start

### View Help
```bash
trt help
```

Output:
```
TRT - Tool Runtime Terminal

Available commands:
  help
  version
  boards

Future commands:
  info
  status
  gpio
  pwm
  i2c
  spi
  relay
  lcd
  modules
```

### Check Version
```bash
trt version
```

Output:
```
TRT CLI
Version: 0.1.0
```

### List Connected Boards
```bash
trt boards
```

Output:
```
No boards detected.
(Mock implementation)
```

## Project Structure

```
trt-cli/
├── src/trt/                    # Main package
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # Module execution entry point
│   ├── cli.py                  # CLI application setup (Typer)
│   ├── version.py              # Version information
│   ├── commands/               # Command implementations
│   │   ├── __init__.py
│   │   ├── help.py             # Help command
│   │   ├── version.py          # Version command
│   │   └── boards.py           # Boards command (mock)
│   └── core/                   # Core models and utilities
│       ├── __init__.py
│       └── models.py           # Data models for future expansion
├── docs/                       # Documentation
│   └── architecture.md         # Detailed architecture guide
├── tests/                      # Test suite
│   └── test_cli.py
├── pyproject.toml              # Modern Python packaging
├── README.md                   # This file
├── LICENSE                     # MIT License
└── .gitignore                  # Git configuration
```

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
ruff check src/
black --check src/
mypy src/
```

### Auto-Format Code
```bash
black src/
isort src/
```

## Future Features

### Planned Commands
- `trt info` - Display system and board information
- `trt status` - Show status of connected boards
- `trt gpio` - GPIO control (read/write)
- `trt pwm` - PWM configuration
- `trt i2c` - I2C protocol interface
- `trt spi` - SPI protocol interface
- `trt relay` - Relay control
- `trt lcd` - LCD display control
- `trt modules` - Module management

### Extension System (Future)
- Plugin architecture for custom commands
- Custom protocol implementations
- Board profile system
- Configuration management

## Design Philosophy

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Plugins and custom commands are first-class citizens
3. **Clarity**: Code is self-documenting and easy to understand
4. **Typing**: Full type hints for IDE support and safety
5. **Testing**: Comprehensive test coverage
6. **Documentation**: Every module has clear documentation

## Contributing

We welcome contributions! See CONTRIBUTING.md for guidelines (coming soon).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

See [docs/architecture.md](docs/architecture.md) for detailed roadmap and implementation notes.

## Related Projects

Future repositories in the TRT ecosystem:
- **trt-protocol**: Communication protocol specification and implementation
- **trt-core**: Core hardware abstraction layer
- **trt-modules**: Official hardware modules and drivers

## Contact

For questions, suggestions, or bug reports, please open an issue on GitHub.

---

**TRT** - Making hardware control accessible to everyone.
