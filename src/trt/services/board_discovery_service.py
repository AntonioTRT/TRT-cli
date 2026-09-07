"""Board discovery service."""

from __future__ import annotations

from trt.repositories.board_repository import BoardRepository


class BoardDiscoveryService:
    """Encapsulates board discovery operations.

    This service keeps discovery orchestration out of CLI command handlers and
    makes search behavior reusable for future protocol or transport integrations.
    """

    def __init__(self, repository: BoardRepository | None = None) -> None:
        self.repository = repository or BoardRepository()

    def discover(self) -> list:
        return self.repository.get_all()
