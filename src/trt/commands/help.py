"""`trt help` - the full TRT reference: concepts, status, workflow, heartbeat and commands.

Plain ASCII on purpose: Windows consoles without UTF-8 print non-ASCII punctuation as '?'.
"""

from rich.console import Console
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from trt.commands.quickstart import WORKFLOW

console = Console()

_INDENT = (0, 0, 0, 2)


def _section(title: str) -> None:
    console.print()
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print("[dim]" + "-" * len(title) + "[/dim]")


def _text(text: str) -> None:
    console.print(Padding(text, _INDENT), highlight=False)


def _rows(rows: list[tuple[str, str]], key_style: str = "cyan") -> None:
    table = Table(show_header=False, box=None, padding=(0, 2), pad_edge=False)
    table.add_column(style=key_style, no_wrap=True)
    table.add_column()
    for key, value in rows:
        table.add_row(escape(key), value)  # keys are literal: [mode] is not markup
    console.print(Padding(table, _INDENT), highlight=False)


def show_help() -> None:
    console.print()
    console.print("[bold cyan]TRT - Tool Runtime Terminal[/bold cyan]")
    _text(
        "Discover TRT boards, check that the mode matches the connected hardware,\n"
        "update it, and monitor the board. Workflow:\n"
        f"[bold]{WORKFLOW}[/bold]"
    )

    _section("Concepts")
    _text("[bold]Board Address[/bold]  How TRT talks to a board: the number in every command.")
    _text("  Examples: 101, 201, 301.  Used as [cyan]trt board info <address>[/cyan].")
    _text("  Shown by [cyan]trt boards[/cyan]. It is NOT a hardware identifier.")
    console.print()
    _text("[bold]Board ID[/bold]  Identifies the carrier board, to select its board profile.")
    _text("  Not implemented yet (planned: ADC resistor-divider identification).")
    _text("  Today the carrier shows as name, type and revision in [cyan]trt board info[/cyan].")
    console.print()
    _text("[bold]HWID[/bold]  Identifies the daughter board connected to the carrier, read from")
    _text("  the ID pins at boot. It decides which mode the board needs.")
    _text("  Shown as the pin pattern D6 D5 D4 D3 (VCC = 1, GND or open = 0).")
    console.print()
    _text("[bold]Mode[/bold]  What the firmware does with the daughter board: mode_<ID>_<name>.")
    _text("  The mode ID is the HWID it is written for, the same on every platform:")
    _rows(
        [
            ("  HWID 0000", "mode_0000_base         Base Mode: no daughter board"),
            ("  HWID 0010", "mode_0002_analog       Analog"),
            ("  HWID 0011", "mode_0003_keypad       Keypad"),
            ("  HWID 0100", "mode_0004_encoder      Encoder"),
            ("  HWID 0101", "mode_0005_display_i2c  Display (I2C, OLED)"),
            ("  HWID 0110", "mode_0006_display_spi  Display (SPI, TFT)"),
            ("  HWID 0111", "mode_0007_led          LED (rings, strips)"),
            ("  HWID 1100", "mode_0012_blink        Blink / test (never production)"),
        ]
    )
    _text("  Reserved: 0001 self-describing module, 1110 factory test, 1111 fault.")
    _text("  Base Mode is the recovery / maintenance runtime (TRT-Core, discovery,")
    _text("  information, HWID, update, heartbeat). Every firmware image contains it.")
    console.print()
    _text("Address  != Board ID  how to reach the board  vs  which carrier it is")
    _text("Board ID != HWID      the carrier             vs  the daughter board")
    _text("HWID     != Mode      the connected hardware  vs  the installed firmware")

    _section("Reading the board status")
    _text("[cyan]trt boards[/cyan] and [cyan]trt board info[/cyan] show, for every board:")
    _rows(
        [
            ("HWID", "read from the hardware / expected by the installed mode"),
            ("Status", "[bold green]MATCH[/bold green] mode fits the hardware, nothing to do"),
            ("", "[bold red]MISMATCH[/bold red] mode is for other hardware: run trt board update"),
            ("", "[yellow]NO HWID[/yellow] firmware too old to read the HWID: run trt board update"),
            ("", "[yellow]NO MODE[/yellow] firmware declares no mode_<ID>_* mode"),
        ]
    )
    console.print()
    _text("Example MATCH                      Example MISMATCH")
    _text("  HWID read      0010                HWID read      0010")
    _text("  HWID expected  0010                HWID expected  0000")
    _text("  Status         [bold green]MATCH[/bold green]               Status         [bold red]MISMATCH[/bold red]")
    _text("  analog board + analog mode         analog board + base mode: update!")
    console.print()
    _text("[cyan]trt boards[/cyan] shows it as  [bold]0010 / 0010  MATCH[/bold]  or  [bold]0010 / 0000  MISMATCH[/bold]")

    _section("Typical workflow")
    _rows(
        [
            ("1. trt discover", "find the boards on the serial ports"),
            ("2. trt boards", "address, mode, HWID, status"),
            ("3. trt board info 201", "check one board in detail"),
            ("4. trt board hwid 201", "which daughter board is connected"),
            ("5. trt board mode 201", "which mode is installed"),
            ("6. trt board update 201", "if MISMATCH: build, flash, reboot, verify"),
            ("7. trt boards", "confirm the board now shows MATCH"),
            ("8. trt listen", "monitor the running board (Ctrl+C)"),
        ]
    )
    _text("[dim]trt board update 201 --check only reports: exit 0 = MATCH, 1 = MISMATCH.[/dim]")

    _section("Heartbeat")
    _text("Every running TRT board sends a HEARTBEAT about once per second.")
    _text("A heartbeat confirms that:")
    _text("  - the firmware is running (the board is powered and not stuck),")
    _text("  - TRT-Core is running (its main loop is being polled),")
    _text("  - the board-to-PC link works (USB/serial port and baud rate).")
    _rows(
        [
            ("trt listen", "print heartbeats and events from all boards"),
            ("trt board listen <address>", "print them from one board"),
        ]
    )
    _text("Output: [bold]Board 201: HEARTBEAT[/bold], once per second.")
    _text("Use it after flashing or rewiring: no line for a few seconds means the")
    _text("board is not running or not connected.")
    _text("Heartbeats only prove the board -> PC direction. If they arrive but commands")
    _text("time out, the board is not receiving: reset it or run [cyan]trt board update[/cyan].")
    _text("Stop listening (Ctrl+C) before other commands: a serial port can be open")
    _text("in one program only.")

    _section("Commands")
    console.print("[bold]  Board discovery[/bold]")
    _rows(
        [
            ("  trt discover", "Scan serial ports and discover TRT boards"),
            ("  trt boards", "Show discovered boards and their MATCH status"),
        ]
    )
    console.print("[bold]  Board management[/bold]")
    _rows(
        [
            ("  trt board info <address>", "Status (mode, HWID, MATCH) + details"),
            ("  trt board hwid <address>", "HWID of the daughter board"),
            ("  trt board mode <address>", "Mode installed in the firmware"),
            ("  trt board update <address>", "Install the mode matching the HWID"),
            ("  trt board update <address> --check", "Report MATCH / MISMATCH only"),
            ("  trt board <query> <address>", "One value. <query>: name, type,"),
            ("", "revision, version, build-id,"),
            ("", "runtime, uptime, id, transport,"),
            ("", "capabilities"),
        ]
    )
    console.print("[bold]  Monitoring[/bold]")
    _rows(
        [
            ("  trt listen", "Heartbeat and events from all boards"),
            ("  trt board listen <address>", "Heartbeat and events from one board"),
        ]
    )
    console.print("[bold]  Development[/bold]  [dim](STM32 firmware; trt board update runs these for you)[/dim]")
    _rows(
        [
            ("  trt list-modes stm32", "Modes that can be built"),
            ("  trt build stm32 <mode>", "Build one mode, no flashing"),
            ("  trt flash stm32 [mode]", "Flash the latest (or named) build"),
            ("  trt flash stm32 --platformio", "Legacy PlatformIO build and upload"),
            ("  trt stm32 test", "Protocol self-test of an STM32 board"),
        ]
    )
    console.print("[bold]  Information[/bold]")
    _rows(
        [
            ("  trt", "Quick Start"),
            ("  trt --help", "All commands, grouped"),
            ("  trt help", "This reference"),
            ("  trt version", "TRT CLI version"),
            ("  trt update", "Update the TRT CLI itself (not a board)"),
        ]
    )
    console.print()
    for line in (
        "Not listed: simulated commands that do not talk to hardware yet (LCD, LED,",
        "board peripheral commands) and an outdated protocol placeholder.",
        "Options of any command: trt <command> --help.",
        "Hardware details: TRT-core docs/hwid-and-firmware-update.md",
    ):
        _text(f"[dim]{line}[/dim]")
    console.print()
