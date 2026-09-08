"""Repository for board state."""

from __future__ import annotations

from trt.core.models import Board, BoardRegistry


class BoardRepository:
    """Storage abstraction for board state.

    The repository encapsulates storage only. Discovery services populate it
    from protocol responses so device data does not originate here.
    """

    def __init__(self, registry: BoardRegistry | None = None) -> None:
        self._registry = registry or BoardRegistry()

    @property
    def registry(self) -> BoardRegistry:
        return self._registry

    def get_all(self) -> list[Board]:
        return self._registry.all()

    def get_by_id(self, board_id: str) -> Board | None:
        return self._registry.get(board_id)

    def get_connected(self) -> list[Board]:
        return self._registry.connected()

    def register(self, board: Board) -> Board:
        self._registry.register(board)
        return board
