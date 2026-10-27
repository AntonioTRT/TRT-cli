"""Hidden developer area: ``trt --dev``.

INTERNAL - do not mention this feature in user-facing docs (README, cli-reference,
``trt help``, the command tree in ``cli.py``). It is a temporary staging area for
experimental commands that are not ready to become real TRT commands.

Usage
-----
    trt --dev            list the development commands
    trt --dev <name>     run one of them

Where it is implemented
-----------------------
* ``--dev`` is NOT a Typer option. ``main()`` in ``trt/cli.py`` checks
  ``sys.argv`` before Typer runs and, if the first argument is ``--dev``, calls
  ``run_dev()`` from this file. Because Typer never sees it, it cannot show up
  in ``trt --help`` or ``trt help``.
* Everything else (the commands and their descriptions) lives in this file.
* ``--dev`` must be the first argument. ``CliRunner.invoke(app, ...)`` bypasses
  ``main()``, so tests must call ``run_dev()`` directly.

How to add a development command
--------------------------------
1. Write a function below (``def _my_feature(args): ...``). ``args`` is the list of
   extra command-line words after the command name.
2. Add one line to ``DEV_COMMANDS``: ``"my_feature": (_my_feature, "description")``.
   The description is what ``trt --dev`` prints in the list.

How to modify a development command
-----------------------------------
Edit its function, or change its description in ``DEV_COMMANDS``.

How to remove a development command
-----------------------------------
Delete its function and its line in ``DEV_COMMANDS``. Nothing else references it.

How to promote a development command into a normal TRT command
--------------------------------------------------------------
1. Move the logic into a service in ``trt/services/`` and any request/response
   types into ``trt/protocol/models.py`` (follow an existing command such as
   ``board info``).
2. Create the Typer command in ``trt/commands/`` and register it in
   ``trt/cli.py``.
3. Add it to ``trt/commands/help.py`` (only if it works against real hardware),
   to ``docs/cli-reference.md``, and add tests.
4. Remove it from this file (see "How to remove").
"""

from __future__ import annotations

from collections.abc import Callable

from rich.console import Console

console = Console()


# ---------------------------------------------------------------------------
# Development commands
# Add, modify or remove the functions below. Each one is a placeholder.
# ---------------------------------------------------------------------------

def _antonio(args: list[str]) -> None:
    console.print("Antonio test function")


def _caleb(args: list[str]) -> None:
    console.print("Caleb test function")


def _angel(args: list[str]) -> None:
    console.print("Angel test function")


# Registry of development commands: name -> (function, short description).
# TO ADD A COMMAND: add a line here and write its function above.
# TO REMOVE A COMMAND: delete its line here and its function above.
DEV_COMMANDS: dict[str, tuple[Callable[[list[str]], None], str]] = {
    "antonio": (_antonio, "Test function for Antonio"),
    "caleb": (_caleb, "Test function for Caleb"),
    "angel": (_angel, "Test function for Angel"),
}


def run_dev(args: list[str]) -> int:
    """Handle ``trt --dev [name] [extra args...]``. Returns the exit code."""
    if not args:
        console.print("Available development commands:\n")
        for name, (_, description) in DEV_COMMANDS.items():
            console.print(f"- {name:<9}{description}")
        return 0

    name = args[0]
    if name not in DEV_COMMANDS:
        console.print(f"Unknown development command: {name}")
        console.print("Run 'trt --dev' to list the available ones.")
        return 1

    DEV_COMMANDS[name][0](args[1:])
    return 0
