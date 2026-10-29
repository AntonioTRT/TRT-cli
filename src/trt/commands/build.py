"""Firmware build commands (build only; flashing lives in trt flash)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Build board firmware without flashing", no_args_is_help=True)

PROGRAMS_SUBDIR = Path("Sources") / "programs"
ARTIFACTS_SUBDIR = Path("artifacts")
LATEST_MANIFEST = "latest.json"
_PROGRAM_NAME = re.compile(r"^program_[a-z0-9_]+$")


def list_programs(cube_dir: Path) -> list[str]:
    """Application names available in the CubeIDE project (Sources/programs/program_*.c)."""
    return sorted(path.stem for path in (cube_dir / PROGRAMS_SUBDIR).glob("program_*.c"))


def program_macro(program: str) -> str:
    """program_pulse_train -> PROGRAM_PULSE_TRAIN (the ID defined in app_selector.h)."""
    return program.upper()


def resolve_cubeide_dir(project_dir: Path | None) -> Path:
    if project_dir is not None:
        bases = [project_dir.resolve()]
    else:
        roots = [Path.cwd(), Path(__file__).resolve().parents[4]]
        bases = []
        for root in roots:
            bases.extend((root, root / "TRT-stm32", root / "TRT-core" / "TRT-stm32"))

    for base in bases:
        for candidate in (base, base / "am modulation"):
            if (candidate / "CMakeLists.txt").is_file() and (candidate / PROGRAMS_SUBDIR).is_dir():
                return candidate

    raise typer.BadParameter(
        "Could not locate the STM32CubeIDE project (CMakeLists.txt and Sources/programs). "
        "Use --project-dir to specify it."
    )


def run_checked(command: list[str], failure: str) -> None:
    try:
        result = subprocess.run(command, check=False)
    except OSError as error:
        console.print(f"\n  [red]{failure}:[/red] {error}\n")
        raise typer.Exit(1) from error
    if result.returncode:
        console.print(f"\n  [red]{failure} (exit code {result.returncode}).[/red]\n")
        raise typer.Exit(result.returncode)


def artifact_path(cube_dir: Path, program: str) -> Path:
    return cube_dir / ARTIFACTS_SUBDIR / program / f"{program}.elf"


@app.command("stm32", help="Build an STM32 application (with TRT-Core) without flashing")
def build_stm32(
    program: str = typer.Argument(..., help="Application name, e.g. program_blink"),
    project_dir: Path | None = typer.Option(
        None,
        "--project-dir",
        help="Path to the TRT-stm32 directory or the STM32CubeIDE project",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
) -> None:
    cube_dir = resolve_cubeide_dir(project_dir)
    available = list_programs(cube_dir)
    if not _PROGRAM_NAME.match(program) or program not in available:
        raise typer.BadParameter(f"Unknown program '{program}'. Available: {', '.join(available) or 'none'}.")

    missing = [tool for tool in ("cmake", "arm-none-eabi-gcc") if shutil.which(tool) is None]
    if missing:
        console.print(
            f"\n  [red]Missing build tools on PATH:[/red] {', '.join(missing)}. "
            "Install/enable the STM32CubeIDE toolchain (cmake, arm-none-eabi-gcc).\n"
        )
        raise typer.Exit(1)

    # A build directory per program keeps CubeIDE's own Debug/ build untouched.
    build_dir = cube_dir / "build" / program
    configure = [
        "cmake", "-S", str(cube_dir), "-B", str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={cube_dir / 'cubeide-gcc.cmake'}",
        "-DCMAKE_BUILD_TYPE=Debug",
        f"-DACTIVE_PROGRAM={program_macro(program)}",
    ]
    if shutil.which("ninja"):
        configure[1:1] = ["-G", "Ninja"]

    console.print(f"  [cyan]Building[/cyan] {program} (TRT-Core included) in {build_dir}")
    run_checked(configure, "CMake configure failed")
    run_checked(["cmake", "--build", str(build_dir)], "Build failed")

    elf = next(build_dir.glob("*.elf"), None)
    if elf is None:
        console.print("\n  [red]Build finished but no .elf was produced.[/red]\n")
        raise typer.Exit(1)

    stored = artifact_path(cube_dir, program)
    stored.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(elf, stored)
    manifest = {
        "program": program,
        "elf": str(stored),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (cube_dir / ARTIFACTS_SUBDIR / LATEST_MANIFEST).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    console.print(f"\n  [bold green]Built {program}.[/bold green] Artifact: {stored}")
    console.print("  Flash it with: trt flash stm32\n")
