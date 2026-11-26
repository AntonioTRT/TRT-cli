"""Firmware build commands (build only; flashing lives in trt flash)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

from trt.core.applications import APP_NAME as _PROGRAM_NAME
from trt.core.applications import app_hwid

console = Console()
app = typer.Typer(help="Build board firmware without flashing", no_args_is_help=True)

PROGRAMS_SUBDIR = Path("Sources") / "programs"
ARTIFACTS_SUBDIR = Path("artifacts")
LATEST_MANIFEST = "latest.json"
# Where STM32CubeIDE bundles its toolchain, searched when a tool is not on PATH.
CUBEIDE_ROOTS = (Path("C:/ST"), Path("C:/Program Files/STMicroelectronics"))


def list_programs(cube_dir: Path) -> list[str]:
    """Application names available in the CubeIDE project (Sources/programs/app_<HWID>_<name>.c)."""
    return sorted(
        path.stem for path in (cube_dir / PROGRAMS_SUBDIR).glob("app_*.c") if _PROGRAM_NAME.match(path.stem)
    )


def program_macro(program: str) -> str:
    """app_0002_analog_family -> APP_0002_ANALOG_FAMILY (the ID defined in app_selector.h)."""
    return program.upper()


def app_for_hwid(cube_dir: Path, hwid: int) -> str | None:
    """The application that matches a HWID, or None. Two files with the same HWID are an error."""
    matches = [program for program in list_programs(cube_dir) if app_hwid(program) == hwid]
    if len(matches) > 1:
        raise ValueError(f"Several applications claim HWID {hwid}: {', '.join(matches)}")
    return matches[0] if matches else None


def cubeide_tool_dirs() -> list[Path]:
    """tools/bin directories of the STM32CubeIDE plugins (toolchain, CMake, Ninja, CubeProgrammer)."""
    dirs: list[Path] = []
    for root in CUBEIDE_ROOTS:
        if root.is_dir():
            dirs.extend(sorted(root.glob("STM32CubeIDE*/STM32CubeIDE/plugins/*/tools/bin"), reverse=True))
    return dirs


def ensure_stm32_tools(tools: tuple[str, ...]) -> list[str]:
    """Put STM32CubeIDE's bundled tools on PATH when they are missing; return the tools still missing."""
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if not missing:
        return []
    for directory in cubeide_tool_dirs():
        if any((directory / f"{tool}.exe").is_file() or (directory / tool).is_file() for tool in missing):
            os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"
    return [tool for tool in tools if shutil.which(tool) is None]


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
    program: str = typer.Argument(..., help="Application name, e.g. app_0002_analog_family"),
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
    build_stm32_app(cube_dir, program)
    console.print("  Flash it with: trt flash stm32\n")


def build_stm32_app(cube_dir: Path, program: str) -> Path:
    """Build one application (TRT-Core included) and store it as an artifact; returns the stored .elf."""
    ensure_stm32_tools(("ninja",))
    missing = ensure_stm32_tools(("cmake", "arm-none-eabi-gcc"))
    if missing:
        console.print(
            f"\n  [red]Missing build tools on PATH:[/red] {', '.join(missing)}. "
            "Install STM32CubeIDE (its bundled tools are found under C:/ST) "
            "or put cmake and arm-none-eabi-gcc on PATH.\n"
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
    return stored
