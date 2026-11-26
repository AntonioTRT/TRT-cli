"""TRT CLI - main application entry point.

Sets up the top-level Typer app and registers all command groups.

Three levels of help, from short to complete:
    trt          Quick Start: the five commands of the board workflow (quickstart.py)
    trt --help   Commands grouped by purpose, with descriptions (Typer, rich_help_panel)
    trt help     Full reference: concepts, MATCH/MISMATCH, workflow, heartbeat, commands (help.py)

User workflow:  discover -> boards -> board info -> board hwid -> board update -> MATCH -> listen

Hidden from the help screens but still callable (they do not talk to hardware):
    trt lcd ..., trt led ...         simulated peripherals (mock)
    trt protocol ...                 outdated placeholder for the protocol description
    trt board gpio|pwm|adc|dac|i2c|spi|debug|modules|reset|reboot|status   simulated (see board.py)
"""

import sys

import typer
from typer.core import TyperGroup

from trt.commands.board import board_app
from trt.commands.boards import show_boards
from trt.commands.build import app as build_app
from trt.commands.discover import run_discover
from trt.commands.flash import app as flash_app
from trt.commands.help import show_help
from trt.commands.lcd import app as lcd_app
from trt.commands.led import app as led_app
from trt.commands.listen import run_listen
from trt.commands.programs import app as programs_app
from trt.commands.protocol import app as protocol_app
from trt.commands.quickstart import show_quickstart
from trt.commands.stm32 import app as stm32_app
from trt.commands.update import run_update
from trt.commands.version import show_version

# Help panels of `trt --help`, in workflow order.
DISCOVERY = "Board Discovery"
MANAGEMENT = "Board Management"
MONITORING = "Monitoring"
DEVELOPMENT = "Development (firmware build and flash)"
INFORMATION = "Information"

_EPILOG = (
    "[bold]Board management[/bold] (ADDRESS = board address shown by [cyan]trt boards[/cyan], e.g. 201)\n"
    "  [cyan]trt board info ADDRESS[/cyan]            Board status: application, HWID read / expected, MATCH\n"
    "  [cyan]trt board hwid ADDRESS[/cyan]            HWID of the connected daughter board\n"
    "  [cyan]trt board active-program ADDRESS[/cyan]  Application installed in the firmware\n"
    "  [cyan]trt board update ADDRESS[/cyan]          Install the application that matches the HWID\n\n"
    "[bold]Workflow[/bold]  discover -> boards -> board info -> board hwid -> board update -> MATCH -> listen\n\n"
    "Run [cyan]trt help[/cyan] for concepts (address, HWID, Board ID, application) and the full reference."
)

# `trt --help` lists panels in the order their commands appear; keep the workflow order.
_COMMAND_ORDER = (
    "discover", "boards", "board", "listen",
    "list-programs", "build", "flash", "stm32",
    "help", "version", "update",
)


class _WorkflowOrderGroup(TyperGroup):
    def list_commands(self, ctx):  # type: ignore[no-untyped-def]
        rank = {name: index for index, name in enumerate(_COMMAND_ORDER)}
        return sorted(super().list_commands(ctx), key=lambda name: rank.get(name, len(rank)))


app = typer.Typer(
    cls=_WorkflowOrderGroup,
    help="TRT - Tool Runtime Terminal. Discover TRT boards, check that their firmware matches the "
    "connected hardware (HWID), update it, and monitor them.",
    epilog=_EPILOG,
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
)


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Without a command, show the Quick Start instead of the full usage screen."""
    if ctx.invoked_subcommand is None:
        show_quickstart()


# Command groups
app.add_typer(
    board_app, name="board", rich_help_panel=MANAGEMENT,
    help="Inspect and update one board: info, hwid, active-program, update, listen, queries",
)
app.add_typer(build_app, name="build", rich_help_panel=DEVELOPMENT, help="Build an application firmware (no flashing)")
app.add_typer(flash_app, name="flash", rich_help_panel=DEVELOPMENT, help="Flash a previously built firmware")
app.add_typer(programs_app, name="list-programs", rich_help_panel=DEVELOPMENT, help="List the applications that can be built")
app.add_typer(stm32_app, name="stm32", rich_help_panel=DEVELOPMENT, help="STM32 protocol self-test (trt stm32 test)")
# Simulated / placeholder groups: callable, but kept out of every help screen.
app.add_typer(lcd_app, name="lcd", hidden=True, help="LCD display control (simulated, no hardware)")
app.add_typer(led_app, name="led", hidden=True, help="LED control (simulated, no hardware)")
app.add_typer(protocol_app, name="protocol", hidden=True, help="Outdated protocol placeholder")


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------

@app.command(rich_help_panel=DISCOVERY, help="Scan serial ports and discover TRT boards")
def discover() -> None:
    """Force a rescan for boards on active serial transports."""
    run_discover()


@app.command(rich_help_panel=DISCOVERY, help="Show discovered boards: firmware, application, HWID and MATCH status")
def boards() -> None:
    """Display all boards currently known to TRT."""
    show_boards()


@app.command(rich_help_panel=MONITORING, help="Listen for heartbeat and events from all boards (Ctrl+C to stop)")
def listen() -> None:
    """Passively print asynchronous messages from every TRT board. Ctrl+C to stop."""
    run_listen()


@app.command(rich_help_panel=INFORMATION, help="Full reference: concepts, workflow, heartbeat, all commands")
def help() -> None:
    """Display the full TRT reference."""
    show_help()


@app.command(rich_help_panel=INFORMATION, help="Show the TRT CLI version")
def version() -> None:
    """Print the current TRT CLI version."""
    show_version()


@app.command(rich_help_panel=INFORMATION, help="Update the TRT CLI itself (board firmware: trt board update)")
def update(
    install: bool = typer.Option(
        False, "--install", "-i",
        help="Install the latest version after confirming an update is available",
    ),
    check: bool = typer.Option(
        False, "--check", "-c",
        help="Check only - do not prompt for install (default behaviour)",
    ),
) -> None:
    """Check GitHub for a newer version of the TRT CLI.

    This updates the trt program on this computer, not a board.
    To update board firmware use: trt board update ADDRESS.
    """
    run_update(install=install, check_only=check)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point - called by the trt console script."""
    # Hidden developer area (see trt/commands/dev.py). Handled before Typer runs
    # so it never appears in any help output. Keep this undocumented.
    if sys.argv[1:2] == ["--dev"]:
        from trt.commands.dev import run_dev

        raise SystemExit(run_dev(sys.argv[2:]))
    app()


if __name__ == "__main__":
    main()
