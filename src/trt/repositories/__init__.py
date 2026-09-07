"""Repository layer for TRT.

This package contains persistence and state-access abstractions for board data.
The current implementation uses an in-memory mock registry, but the repository
boundary keeps the CLI and services independent from state construction.
"""

from trt.repositories.board_repository import BoardRepository

__all__ = ["BoardRepository"]
