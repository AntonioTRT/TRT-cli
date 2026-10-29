"""Application discovery commands."""

from __future__ import annotations

from pathlib import Path

import typer

from trt.commands.build import list_programs, resolve_cubeide_dir

app = typer.Typer(help="List the applications available for a board family", no_args_is_help=True)


@app.command("stm32", help="List STM32 applications (Sources/programs/program_*.c)")
def list_programs_stm32(
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
    programs = list_programs(resolve_cubeide_dir(project_dir))
    if not programs:
        typer.echo("No STM32 programs found in Sources/programs.", err=True)
        raise typer.Exit(1)
    for program in programs:
        typer.echo(program)
