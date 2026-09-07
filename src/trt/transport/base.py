"""Base transport interface for TRT."""

from __future__ import annotations

from abc import ABC, abstractmethod

from trt.protocol.models import ProtocolRequest, ProtocolResponse


class Transport(ABC):
    """Abstract transport used by the protocol layer.

    Future USB, CAN, and TCP adapters will implement this interface while the
    protocol layer remains unchanged.
    """

    @abstractmethod
    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        """Send a protocol request and return a protocol response."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the transport is usable."""
