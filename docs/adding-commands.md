# Adding a New `trt` Command

This guide shows where commands live, where they are listed, and the exact
steps to add your own function as a `trt` command.

TRT is built on [Typer](https://typer.tiangolo.com/). A command is a normal
Python function with an `@app.command()` decorator. Its parameters become the
command's arguments and options.

---

## 1. Where things are

| What | File | Notes |
|---|---|---|
| Entry point (`trt` executable) | [pyproject.toml](../pyproject.toml) → `[project.scripts] trt = "trt.cli:main"` | No changes needed |
| **Main app: registers every command** | [src/trt/cli.py](../src/trt/cli.py) | Top-level commands and `app.add_typer(...)` for groups |
| **Command implementations** | [src/trt/commands/](../src/trt/commands/) | One file per command or group (`led.py`, `lcd.py`, `board.py`, ...) |
| Business logic | [src/trt/services/](../src/trt/services/) | e.g. `LEDService`, `BoardService` |
| Request/response types | [src/trt/protocol/models.py](../src/trt/protocol/models.py) | `ProtocolOperation` enum + `*Request` / `*Response` dataclasses |
| Fake hardware replies | [src/trt/transport/mock_transport.py](../src/trt/transport/mock_transport.py) | Used when no board is connected |
| Real serial (Arduino) | [src/trt/transport/serial_transport.py](../src/trt/transport/serial_transport.py) | `_OPCODES` maps operations to firmware opcodes |
| Tests | [tests/test_cli.py](../tests/test_cli.py) | Uses `typer.testing.CliRunner` |

### Where commands are *listed*

Some command lists are written out by hand. **Update them when you add a command:**

1. **[src/trt/commands/help.py](../src/trt/commands/help.py)**: the tables shown
   by `trt help`. Add a `top.add_row(...)`, a tuple to `rows`, or an
   `extra.add_row(...)` line.
2. **[docs/cli-reference.md](cli-reference.md)**: the full user-facing reference.
3. The docstring at the top of [src/trt/cli.py](../src/trt/cli.py) (the command tree).
4. The docstring in [src/trt/commands/\_\_init\_\_.py](../src/trt/commands/__init__.py).

`trt --help` and `trt <group> --help` are **generated automatically** from the
`help=` text, so you don't edit them.

---

## 2. How a command flows

```text
trt led color 255 0 0
      │
      ▼
cli.py            app.add_typer(led_app, name="led")         ← registration
      │
      ▼
commands/led.py   @app.command() def color(red, green, blue)  ← parses args, prints output
      │
      ▼
services/led_service.py   LEDService().color(...)             ← logic
      │
      ▼
protocol/models.py        LedColorRequest(...)                ← typed request
      │
      ▼
transport/mock_transport.py or serial_transport.py            ← fake or real hardware
```

For a simple command that doesn't talk to a board, you only need the first two
layers (`cli.py` and a file in `commands/`).

---

## 3. Recipe A: add a simple top-level command (`trt ping`)

**Step 1.** Create `src/trt/commands/ping.py`:

```python
"""Ping command: simple connectivity check."""

from rich.console import Console

console = Console()


def run_ping() -> None:
    """Print a pong."""
    console.print("\n  [green]pong[/green]\n")
```

**Step 2.** Register it in [src/trt/cli.py](../src/trt/cli.py). Add the import
next to the others, then add the command in the *Top-level commands* section:

```python
from trt.commands.ping import run_ping

...

@app.command(help="Check that TRT is responding")
def ping() -> None:
    """Simple connectivity check."""
    run_ping()
```

**Step 3.** Run it:

```powershell
trt ping
trt --help        # "ping" now appears in the list
```

The function name becomes the command name. To use a different name, write
`@app.command("my-name", help=...)`.

---

## 4. Recipe B: add a command group with sub-commands (`trt hello say <name>`)

Use a group when you have several related commands, as `trt led on/off/blink`
does.

**Step 1.** Create `src/trt/commands/hello.py`:

```python
"""Hello command group: example group."""

import typer
from rich.console import Console

console = Console()
app = typer.Typer(
    help="Example greeting commands",
    no_args_is_help=True,
)


@app.command("say", help="Greet someone.  Example: trt hello say Ana --shout")
def say(
    name: str = typer.Argument(..., help="Name of the person"),
    shout: bool = typer.Option(False, "--shout", "-s", help="Print in uppercase"),
) -> None:
    message = f"Hello {name}"
    console.print(f"\n  {message.upper() if shout else message}\n")


@app.command("bye", help="Say goodbye")
def bye() -> None:
    console.print("\n  Bye!\n")
```

**Step 2.** Register the group in [src/trt/cli.py](../src/trt/cli.py):

```python
from trt.commands.hello import app as hello_app

...

app.add_typer(hello_app, name="hello", help="Example greeting commands")
```

**Step 3.** Run it:

```powershell
trt hello --help
trt hello say Ana
trt hello say Ana -s
```

---

## 5. Recipe C: add a sub-command to an existing group

Open the group's file and add one more decorated function. No registration is
needed, because the group is already registered in `cli.py`.

| Group | File | Typer object |
|---|---|---|
| `trt board ...` | [commands/board.py](../src/trt/commands/board.py) | `board_app` |
| `trt led ...` | [commands/led.py](../src/trt/commands/led.py) | `app` |
| `trt lcd ...` | [commands/lcd.py](../src/trt/commands/lcd.py) | `app` |
| `trt protocol ...` | [commands/protocol.py](../src/trt/commands/protocol.py) | `app` |

Example: add `trt board ping <id>` in `board.py`:

```python
@board_app.command("ping", help="Check that a board answers")
def board_ping(
    board_id: str = typer.Argument(..., help="Board identifier"),
) -> None:
    console.print(f"\n  [cyan]{board_id}[/cyan]  pong\n")
```

---

## 6. Recipe D: a command that talks to the board

Follow the same layers as the existing LED commands. Example: `trt led toggle`.

1. **Operation + request**: in [protocol/models.py](../src/trt/protocol/models.py),
   add a value to `ProtocolOperation` and a request dataclass:

   ```python
   class ProtocolOperation(str, Enum):
       ...
       LED_TOGGLE = "led_toggle"


   @dataclass(frozen=True, kw_only=True)
   class LedToggleRequest(ProtocolRequest):
       operation: ProtocolOperation = field(default=ProtocolOperation.LED_TOGGLE, init=False)
       board_id: str = "default"
       capability: str | None = field(default="led", init=False)
   ```

2. **Mock reply**: in [transport/mock_transport.py](../src/trt/transport/mock_transport.py),
   add an `if isinstance(request, LedToggleRequest): return ...` branch inside
   `send()`, modelled on the existing LED branches. This makes the command work
   without hardware.

3. **Service method**: in [services/led_service.py](../src/trt/services/led_service.py):

   ```python
   def toggle(self) -> ProtocolResponse:
       return self.execute(LedToggleRequest())
   ```

4. **CLI command**: in [commands/led.py](../src/trt/commands/led.py):

   ```python
   @app.command(help="Toggle LEDs on/off")
   def toggle() -> None:
       _render_action(LEDService().toggle())
   ```

5. **Real hardware (optional)**: to send it to the Arduino, add the firmware
   opcode to `SerialTransport._OPCODES` in
   [transport/serial_transport.py](../src/trt/transport/serial_transport.py)
   and handle the response in its decode logic. The firmware must implement the
   same opcode. See [trt-protocol.md](trt-protocol.md).

---

## 7. Arguments and options cheat sheet

```python
name: str = typer.Argument(..., help="Required positional")        # trt x Ana
count: int = typer.Argument(3, help="Optional positional")          # trt x  / trt x 5
level: int = typer.Argument(..., min=0, max=100)                    # validated range
verbose: bool = typer.Option(False, "--verbose", "-v")              # flag
port: str = typer.Option("COM4", "--port", "-p", help="Serial port") # trt x --port COM3
```

- Use `raise typer.Exit(1)` to end with an error code.
- Use the `rich` `Console` for coloured output (`[green]...[/green]`), like the
  other commands.

---

## 8. Add a test

In [tests/test_cli.py](../tests/test_cli.py), add a test next to the similar ones:

```python
class TestHelloCommands:
    def test_say(self) -> None:
        result = runner.invoke(app, ["hello", "say", "Ana"])
        assert result.exit_code == 0
        assert "Hello Ana" in result.stdout
```

Run the tests with `pytest` (install the dev tools first with `pip install -e ".[dev]"`).

---

## Checklist

- [ ] Function created in `src/trt/commands/<name>.py`
- [ ] Registered in `src/trt/cli.py` (for new top-level commands or groups)
- [ ] `help=` text written (shows up in `trt --help`)
- [ ] Added to `trt help` tables in `commands/help.py`
- [ ] Documented in `docs/cli-reference.md`
- [ ] Test added in `tests/test_cli.py`
- [ ] Tried it: `trt <your-command> --help`

Because TRT is installed with `pip install -e .`, you **don't need to reinstall**
after adding a command. Save the file and run `trt` again.
