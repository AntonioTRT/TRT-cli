"""DTO-like protocol models for TRT.

These models are intentionally transport-agnostic and independent from the CLI
presentation layer. They describe a request/response flow in a form that can be
implemented by future USB, CAN, or TCP protocol clients.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProtocolRequest:
    """A transport-independent protocol request."""

    operation: str
    board_id: str
    capability: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProtocolResponse:
    """A transport-independent protocol response."""

    status: str
    payload: str | dict[str, Any] | None = None
    board_id: str | None = None
    capability: str | None = None
    error: str | None = None
    mock: bool = True

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"
