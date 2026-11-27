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

PROGRAMS_SUBDIR = Path("Sources") / "apps"
ARTIFACTS_SUBDIR = Path("artifacts")
LATEST_MANIFEST = "latest.json"
# Artifact name of the common image, where the daughter-board HWID selects the application.
FIRMWARE_NAME = "firmware"
_APP_NAME = re.compile(r"^app_([0-9a-f]{4})_[a-z0-9_]+$")
_APP_ID = re.compile(r"^(?:0x)?([0-9a-f]{4})$")
_HWID = re.compile(r"^(?:0x)?([0-9a-f])$")


def list_programs(cube_dir: Path) -> list[str]:
    """Application names available in the CubeIDE project (Sources/apps/app_<id>_<name>.c)."""
    return sorted(
        path.stem
        for path in (cube_dir / PROGRAMS_SUBDIR).glob("app_*.c")
        if _APP_NAME.match(path.stem)
    )


def resolve_app(text: str, available: list[str]) -> str | None:
    """Accept a full application name (app_0003_keypad_reader) or just its ID (0003)."""
    if text in available:
        return text
    match = _APP_ID.match(text.lower())
    if match:
        return next((name for name in available if name.startswith(f"app_{match.group(1)}_")), None)
    return None


def override_id(app_name: str) -> str:
    """app_0003_keypad_reader -> 0003 (the value of CMake's ACTIVE_APP_OVERRIDE)."""
    match = _APP_NAME.match(app_name)
    assert match is not None, app_name
    return match.group(1)


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
        "Could not locate the STM32CubeIDE project (CMakeLists.txt and Sources/apps). "
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


@app.command(
    "stm32",
    help=(
        "Build the STM32 firmware (with TRT-Core) without flashing. With no application, builds the "
        "common image: the daughter-board HWID selects the application at startup. With an application "
        "(name or ID, e.g. app_0003_keypad_reader or 0003) it builds a development image that always "
        "runs that application and skips HWID selection."
    ),
)
def build_stm32(
    program: str | None = typer.Argument(
        None, help="Application name or ID, e.g. app_0001_signal_generator or 0001; omit for the common image"
    ),
    hwid: str | None = typer.Option(
        None,
        "--hwid",
        help="HWID (one hex digit) a board without HWID lines (NUCLEO) reports, to simulate a daughter board",
    ),
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
    name = FIRMWARE_NAME
    override = ""
    if program is not None:
        resolved = resolve_app(program, available)
        if resolved is None:
            raise typer.BadParameter(
                f"Unknown application '{program}'. Available: {', '.join(available) or 'none'}."
            )
        name, override = resolved, override_id(resolved)
    hwid_digit = ""
    if hwid is not None:
        match = _HWID.match(hwid.lower())
        if match is None:
            raise typer.BadParameter(f"--hwid '{hwid}': expected one hex digit, e.g. 0x2.")
        if program is not None:
            raise typer.BadParameter("--hwid has no effect together with an application (it skips HWID selection).")
        hwid_digit = match.group(1)

    missing = [tool for tool in ("cmake", "arm-none-eabi-gcc") if shutil.which(tool) is None]
    if missing:
        console.print(
            f"\n  [red]Missing build tools on PATH:[/red] {', '.join(missing)}. "
            "Install/enable the STM32CubeIDE toolchain (cmake, arm-none-eabi-gcc).\n"
        )
        raise typer.Exit(1)

    # A build directory per image keeps CubeIDE's own Debug/ build untouched. Both options are
    # always passed (empty = unset) so a value cached by an earlier build cannot leak into this one.
    build_dir = cube_dir / "build" / name
    configure = [
        "cmake", "-S", str(cube_dir), "-B", str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={cube_dir / 'cubeide-gcc.cmake'}",
        "-DCMAKE_BUILD_TYPE=Debug",
        f"-DACTIVE_APP_OVERRIDE={override}",
        f"-DTRT_HWID_DEFAULT={hwid_digit and '0x' + hwid_digit}",
    ]
    if shutil.which("ninja"):
        configure[1:1] = ["-G", "Ninja"]

    mode = f"always runs {name}" if override else "application chosen from the HWID at startup"
    console.print(f"  [cyan]Building[/cyan] {name} (TRT-Core included; {mode}) in {build_dir}")
    run_checked(configure, "CMake configure failed")
    run_checked(["cmake", "--build", str(build_dir)], "Build failed")

    elf = next(build_dir.glob("*.elf"), None)
    if elf is None:
        console.print("\n  [red]Build finished but no .elf was produced.[/red]\n")
        raise typer.Exit(1)

    stored = artifact_path(cube_dir, name)
    stored.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(elf, stored)
    manifest = {
        "program": name,
        "elf": str(stored),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (cube_dir / ARTIFACTS_SUBDIR / LATEST_MANIFEST).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    console.print(f"\n  [bold green]Built {name}.[/bold green] Artifact: {stored}")
    console.print("  Flash it with: trt flash stm32\n")
