"""Mode discovery commands: `trt list-modes <platform>`."""

from __future__ import annotations

from pathlib import Path

import typer

from trt.commands.build import list_modes, resolve_cubeide_dir

app = typer.Typer(help="List the modes that can be built for a platform", no_args_is_help=True)


@app.command("stm32", help="List STM32 modes (Sources/modes/mode_<ID>_<name>.c)")
def list_modes_stm32(
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
    modes = list_modes(resolve_cubeide_dir(project_dir))
    if not modes:
        typer.echo("No STM32 modes found in Sources/modes.", err=True)
        raise typer.Exit(1)
    for mode in modes:
        typer.echo(mode)
