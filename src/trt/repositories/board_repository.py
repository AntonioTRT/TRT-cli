"""Repository for board state."""

from __future__ import annotations

from trt.core.models import Board, BoardRegistry, BoardStatus, BoardType, make_mock_registry


class BoardRepository:
    """Storage abstraction for board state.

    The repository encapsulates how boards are loaded and retrieved. The current
    implementation uses a mock in-memory registry to preserve the CLI's existing
    behavior without real hardware detection.
    """

    def __init__(self, registry: BoardRegistry | None = None) -> None:
        self._registry = registry or make_mock_registry()

    @property
    def registry(self) -> BoardRegistry:
        return self._registry

    def get_all(self) -> list[Board]:
        return self._registry.all()

    def get_by_id(self, board_id: str) -> Board | None:
        return self._registry.get(board_id)

    def get_connected(self) -> list[Board]:
        return self._registry.connected()

    def load_mock_boards(self) -> None:
        self._registry = make_mock_registry()

    def create_board(self, board_id: str, board_type: BoardType = BoardType.TRT_CORE, status: BoardStatus = BoardStatus.READY) -> Board:
        from trt.core.models import BoardIdentity

        board = Board(
            identity=BoardIdentity(board_id=board_id, board_type=board_type),
            status=status,
        )
        self._registry.register(board)
        return board
