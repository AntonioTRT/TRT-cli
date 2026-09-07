"""Capability policy and evaluation service for TRT."""

from __future__ import annotations

from trt.core.models import Board


class CapabilityService:
    """Resolve whether a board supports a given capability.

    This service keeps capability decisions out of the CLI layer and makes them
    reusable by any application service or future protocol layer.
    """

    def supports(self, board: Board, capability: str) -> bool:
        if board is None:
            return False
        return bool(board.capabilities.has(capability))

    def require(self, board: Board, capability: str) -> None:
        if not self.supports(board, capability):
            raise ValueError(f"Board {board.identity.board_id} does not support {capability}")
