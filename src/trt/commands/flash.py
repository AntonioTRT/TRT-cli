"""Firmware flashing commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Flash firmware to supported boards", no_args_is_help=True)


@app.command("stm32", help="Build and upload the STM32 firmware with PlatformIO")
def flash_stm32(
    port: str | None = typer.Option(None, "--port", help="ST-LINK virtual COM port"),
    project_dir: Path | None = typer.Option(
        None,
        "--project-dir",
        help="Path to the TRT-stm32 PlatformIO project",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
) -> None:
    directory = _resolve_project_dir(project_dir)
    command = [sys.executable, "-m", "platformio", "run", "-d", str(directory), "-t", "upload"]
    if port:
        command.extend(["--upload-port", port])

    console.print(f"  [cyan]Uploading STM32 firmware from[/cyan] {directory}")
    try:
        result = subprocess.run(command, check=False)
    except OSError as error:
        console.print(f"\n  [red]Could not start PlatformIO:[/red] {error}\n")
        raise typer.Exit(1) from error

    if result.returncode:
        console.print(f"\n  [red]PlatformIO upload failed with exit code {result.returncode}.[/red]\n")
        raise typer.Exit(result.returncode)
    console.print("\n  [bold green]STM32 firmware uploaded successfully.[/bold green]\n")


def _resolve_project_dir(project_dir: Path | None) -> Path:
    if project_dir is not None:
        candidates = [project_dir.resolve()]
    else:
        roots = [Path.cwd(), Path(__file__).resolve().parents[4]]
        candidates = []
        for root in roots:
            candidates.extend((root / "TRT-stm32", root / "TRT-core" / "TRT-stm32"))

    for candidate in candidates:
        if (candidate / "platformio.ini").is_file():
            return candidate

    raise typer.BadParameter(
        "Could not locate TRT-stm32/platformio.ini. Use --project-dir to specify the PlatformIO project."
    )
