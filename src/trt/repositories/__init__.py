"""Repository layer for TRT.

This package contains persistence and state-access abstractions for board data.
Discovery services populate repositories from protocol responses, keeping the
CLI independent from state construction.
"""

from trt.repositories.board_repository import BoardRepository

__all__ = ["BoardRepository"]
