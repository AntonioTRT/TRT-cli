"""TRT CLI — main application entry point.

Sets up the top-level Typer app and registers all command groups.
Follows the git / docker / kubectl style: flat top-level verbs with
sub-command trees for complex domains.

Command tree:
    trt help
    trt version
    trt update
    trt boards
    trt discover
    trt board <id> info | status | reset | reboot | capabilities | modules
                         gpio list | read | write
                         pwm  list | start | stop | set
                         adc  list | read
                         dac  list | read | set
                         i2c  scan | read | write
                         spi  transfer | config
                         debug logs | monitor | shell
    trt lcd  info | reset | clear | write
    trt led  on | off | blink | brightness | color
    trt protocol info | version
"""

import typer

from trt.commands.board import board_app
from trt.commands.boards import show_boards
from trt.commands.discover import run_discover
from trt.commands.help import show_help
from trt.commands.lcd import app as lcd_app
from trt.commands.led import app as led_app
from trt.commands.protocol import app as protocol_app
from trt.commands.update import run_update
from trt.commands.version import show_version

app = typer.Typer(
    help="TRT — Tool Runtime Terminal  ·  Hardware control ecosystem for embedded boards.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-apps (command groups)
app.add_typer(board_app,    name="board",    help="Operate on a specific board")
app.add_typer(lcd_app,      name="lcd",      help="LCD display control")
app.add_typer(led_app,      name="led",      help="LED control (WS2812 / NeoPixel)")
app.add_typer(protocol_app, name="protocol", help="TRT Protocol information")


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------

@app.command(help="Show the full TRT command reference")
def help() -> None:
    """Display rich help with the complete command tree."""
    show_help()


@app.command(help="Display TRT CLI version")
def version() -> None:
    """Print the current TRT CLI version."""
    show_version()


@app.command(help="Check for TRT CLI updates")
def update(
    install: bool = typer.Option(
        False, "--install", "-i",
        help="Install the latest version after confirming an update is available",
    ),
    check: bool = typer.Option(
        False, "--check", "-c",
        help="Check only — do not prompt for install (default behaviour)",
    ),
) -> None:
    """Check GitHub for a newer version of TRT CLI.

    With no flags this checks for updates and prints the result.
    Use --install to also download and apply the update.

    Note: This command updates the trt-cli application on your machine.
    To update board firmware use:  trt board <id> update  (future command).
    """
    run_update(install=install, check_only=check)


@app.command(help="List all known boards")
def boards() -> None:
    """Display all boards currently known to TRT (mock data for now)."""
    show_boards()


@app.command(help="Rescan for connected boards (USB)")
def discover() -> None:
    """Force a rescan for boards on all active transports.

    Currently a mock implementation.  Future versions will trigger real
    USB enumeration via TRT Protocol.
    """
    run_discover()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point — called by the [cyan]trt[/cyan] console script."""
    app()


if __name__ == "__main__":
    main()

