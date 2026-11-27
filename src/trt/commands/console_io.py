"""Console output helpers shared by the entry point and long-running commands."""

from __future__ import annotations

import os
import sys


def stdout_closed() -> bool:
    """True when stdout can no longer be written (the reader of a pipe went away, e.g. `| head`)."""
    try:
        sys.stdout.flush()
    except OSError:
        return True
    return False


def discard_stdout() -> None:
    """Redirect stdout to the null device so Python's final flush does not report a second error."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
