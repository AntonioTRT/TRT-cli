"""Update command — check for and install TRT CLI updates.

Scope:
    This command manages updates to the trt-cli Python package installed on
    the developer's machine.  It is entirely separate from board firmware
    updates, which will be handled by:

        trt board <id> update   (future command)

Usage:
    trt update                  Check for a newer version
    trt update --install        Download and install the latest version
    trt update --check          Same as trt update (explicit check-only mode)
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from trt.services.update_service import (
    InstallMethod,
    UpdateStatus,
    check_for_update,
    detect_install_method,
    install_update,
)
from trt.version import get_version

console = Console()


def run_update(
    install: bool = False,
    check_only: bool = False,
) -> None:
    """Execute the update check (and optional install).

    Args:
        install:    If True, attempt to install the latest version after
                    confirming one is available.
        check_only: If True, check only — never prompt for install.
    """
    current = get_version()
    method  = detect_install_method()

    console.print()
    console.print("  [bold]Checking for updates…[/bold]")
    console.print(f"  Current version : [cyan]{current}[/cyan]")
    console.print(f"  Install method  : [dim]{method.value}[/dim]")
    console.print(f"  Checking         : [dim]GitHub releases (AntonioTRT/TRT-cli)[/dim]")
    console.print()

    result = check_for_update()

    # ------------------------------------------------------------------
    # UP TO DATE
    # ------------------------------------------------------------------
    if result.status == UpdateStatus.UP_TO_DATE:
        if result.latest_version:
            console.print(
                f"  [bold green]✓ Up to date.[/bold green]  "
                f"Latest: [cyan]{result.latest_version}[/cyan]"
            )
        else:
            console.print("  [bold green]✓ No update available.[/bold green]")
            if result.error_message:
                console.print(f"  [dim]{result.error_message}[/dim]")
        console.print()
        return

    # ------------------------------------------------------------------
    # UPDATE AVAILABLE
    # ------------------------------------------------------------------
    if result.status == UpdateStatus.UPDATE_AVAILABLE:
        panel_text = (
            f"[bold]Update available![/bold]\n\n"
            f"  Current version : [yellow]{result.current_version}[/yellow]\n"
            f"  Latest version  : [bold green]{result.latest_version}[/bold green]\n\n"
            f"  [dim]{result.release_url}[/dim]"
        )
        console.print(
            Panel(panel_text, border_style="green", expand=False)
        )
        console.print()

        if install:
            _do_install(result.upgrade_command)
        elif not check_only:
            console.print(
                f"  Run [bold cyan]trt update --install[/bold cyan] to install it.\n"
            )
        return

    # ------------------------------------------------------------------
    # CHECK FAILED
    # ------------------------------------------------------------------
    if result.status == UpdateStatus.CHECK_FAILED:
        console.print(
            f"  [yellow]Could not reach GitHub.[/yellow]  "
            f"[dim]{result.error_message or 'Network error.'}[/dim]"
        )
        console.print(
            f"\n  Check manually: [cyan]{result.release_url}[/cyan]\n"
        )
        return

    # Fallback
    console.print("  [dim]Update status unknown.[/dim]\n")


def _do_install(upgrade_command: str) -> None:
    """Execute the install step and report results."""
    console.print("  [bold]Installing update…[/bold]")
    console.print()

    install_result = install_update()

    if install_result.success:
        ver_str = (
            f"  New version : [cyan]{install_result.new_version}[/cyan]\n"
            if install_result.new_version
            else ""
        )
        console.print(
            f"  [bold green]✓ Update installed successfully.[/bold green]\n"
            f"{ver_str}"
        )
    else:
        console.print(f"  [yellow]{install_result.message}[/yellow]\n")
