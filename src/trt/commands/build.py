"""Firmware build commands (build only; flashing lives in trt flash)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console

from trt.core.modes import MODE_NAME as _MODE_NAME
from trt.core.modes import mode_id

console = Console()
app = typer.Typer(help="Build board firmware without flashing", no_args_is_help=True)

MODES_SUBDIR = Path("Sources") / "modes"
ARTIFACTS_SUBDIR = Path("artifacts")
LATEST_MANIFEST = "latest.json"
# Where STM32CubeIDE bundles its toolchain, searched when a tool is not on PATH.
# Where STM32CubeIDE bundles its toolchain: (install root, glob of the plugin tool folders).
# Windows: C:/ST/STM32CubeIDE_2.2.0/STM32CubeIDE/plugins/...; Linux: /opt/st/stm32cubeide_2.2.0/plugins/...;
# macOS: /Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/...
CUBEIDE_LOCATIONS: tuple[tuple[Path, str], ...] = (
    (Path("C:/ST"), "STM32CubeIDE*/STM32CubeIDE/plugins/*/tools/bin"),
    (Path("C:/Program Files/STMicroelectronics"), "STM32CubeIDE*/STM32CubeIDE/plugins/*/tools/bin"),
    (Path("/opt/st"), "stm32cubeide*/plugins/*/tools/bin"),
    (Path.home() / "st", "stm32cubeide*/plugins/*/tools/bin"),
    (Path("/Applications"), "STM32CubeIDE.app/Contents/Eclipse/plugins/*/tools/bin"),
)


def list_modes(cube_dir: Path) -> list[str]:
    """Modes available in the CubeIDE project (Sources/modes/mode_<ID>_<name>.c)."""
    return sorted(
        path.stem for path in (cube_dir / MODES_SUBDIR).glob("mode_*.c") if _MODE_NAME.match(path.stem)
    )


def mode_macro(mode: str) -> str:
    """mode_0002_analog -> MODE_0002_ANALOG (the ID defined in mode_selector.h)."""
    return mode.upper()


def mode_for_hwid(cube_dir: Path, hwid: int) -> str | None:
    """The mode that matches a HWID, or None. Two files with the same mode ID are an error."""
    matches = [mode for mode in list_modes(cube_dir) if mode_id(mode) == hwid]
    if len(matches) > 1:
        raise ValueError(f"Several modes claim HWID {hwid}: {', '.join(matches)}")
    return matches[0] if matches else None


def cubeide_tool_dirs() -> list[Path]:
    """tools/bin directories of the STM32CubeIDE plugins (toolchain, CMake, Ninja, CubeProgrammer)."""
    dirs: list[Path] = []
    for root, pattern in CUBEIDE_LOCATIONS:
        if root.is_dir():
            dirs.extend(sorted(root.glob(pattern), reverse=True))
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
            if (candidate / "CMakeLists.txt").is_file() and (candidate / MODES_SUBDIR).is_dir():
                return candidate

    raise typer.BadParameter(
        "Could not locate the STM32CubeIDE project (CMakeLists.txt and Sources/modes). "
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


@app.command("stm32", help="Build an STM32 mode (with TRT-Core) without flashing")
def build_stm32(
    program: str = typer.Argument(..., metavar="MODE", help="Mode name, e.g. mode_0002_analog"),
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
    available = list_modes(cube_dir)
    if not _MODE_NAME.match(program) or program not in available:
        raise typer.BadParameter(f"Unknown mode '{program}'. Available: {', '.join(available) or 'none'}.")
    build_stm32_mode(cube_dir, program)
    console.print("  Flash it with: trt flash stm32\n")


def build_stm32_mode(cube_dir: Path, program: str) -> Path:
    """Build one mode (TRT-Core and Base Mode included) and store it as an artifact; returns the stored .elf."""
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
        f"-DACTIVE_MODE={mode_macro(program)}",
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
        "mode": program,
        "elf": str(stored),
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (cube_dir / ARTIFACTS_SUBDIR / LATEST_MANIFEST).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    console.print(f"\n  [bold green]Built {program}.[/bold green] Artifact: {stored}")
    return stored
