"""Firmware flashing commands."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from trt.commands.build import (
    ARTIFACTS_SUBDIR,
    LATEST_MANIFEST,
    artifact_path,
    list_programs,
    resolve_cubeide_dir,
    run_checked,
)

console = Console()
app = typer.Typer(help="Flash firmware to supported boards", no_args_is_help=True)


@app.command(
    "stm32",
    help=(
        "Flash a previously built STM32 firmware (see: trt build stm32). With no name, flashes the "
        "most recently built firmware; with a name (trt flash stm32 program_blink), that application's "
        "build. Never builds."
    ),
)
def flash_stm32(
    program: str | None = typer.Argument(
        None, help="Application name, e.g. program_blink; omit for the most recent build"
    ),
    port: str | None = typer.Option(None, "--port", help="ST-LINK virtual COM port (--platformio only)"),
    project_dir: Path | None = typer.Option(
        None,
        "--project-dir",
        help="Path to the TRT-stm32 directory (or the CubeIDE project; the PlatformIO project with --platformio)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    platformio: bool = typer.Option(
        False, "--platformio", help="Build and upload the legacy PlatformIO project instead"
    ),
) -> None:
    if platformio:
        _flash_platformio(port, project_dir)
        return

    cube_dir = resolve_cubeide_dir(project_dir)
    elf, name = _select_artifact(cube_dir, program)

    programmer = shutil.which("STM32_Programmer_CLI")
    if programmer is None:
        console.print(
            "\n  [red]STM32_Programmer_CLI not found on PATH.[/red] "
            f"Flash {elf} with STM32CubeIDE or STM32CubeProgrammer.\n"
        )
        raise typer.Exit(1)

    console.print(f"  [cyan]Flashing[/cyan] {name}: {elf}")
    run_checked([programmer, "-c", "port=SWD", "-w", str(elf), "-v", "-rst"], "Flashing failed")
    console.print(f"\n  [bold green]{name} flashed successfully.[/bold green]\n")


def _select_artifact(cube_dir: Path, program: str | None) -> tuple[Path, str]:
    if program is None:
        manifest = cube_dir / ARTIFACTS_SUBDIR / LATEST_MANIFEST
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            name, elf = str(data["program"]), Path(data["elf"])
        except (OSError, ValueError, KeyError) as error:
            console.print("\n  [red]No STM32 build found.[/red] Run: trt build stm32 <program>\n")
            raise typer.Exit(1) from error
    else:
        name, elf = program, artifact_path(cube_dir, program)

    if not elf.is_file():
        built = sorted(p.name for p in (cube_dir / ARTIFACTS_SUBDIR).glob("program_*") if p.is_dir())
        hint = f"Built: {', '.join(built)}." if built else f"Available programs: {', '.join(list_programs(cube_dir))}."
        console.print(f"\n  [red]No built firmware for {name}.[/red] {hint} Run: trt build stm32 {name}\n")
        raise typer.Exit(1)
    return elf, name


def _flash_platformio(port: str | None, project_dir: Path | None) -> None:
    directory = _resolve_platformio_dir(project_dir)
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


def _resolve_platformio_dir(project_dir: Path | None) -> Path:
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
