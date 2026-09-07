"""Protocol client abstractions for TRT."""

from __future__ import annotations

from abc import ABC, abstractmethod

from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.transport.base import Transport
from trt.transport.mock_transport import MockTransport


class ProtocolClient(ABC):
    """Abstract client used by services to talk to boards.

    The protocol client is transport-agnostic. It accepts a transport instance and
    exposes request-based methods that remain independent of USB/CAN/TCP details.
    """

    def __init__(self, transport: Transport) -> None:
        self.transport = transport

    @abstractmethod
    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        """Deliver a request to the transport layer."""


class MockProtocolClient(ProtocolClient):
    """Mock protocol client used by the current CLI implementation."""

    def __init__(self, transport: Transport | None = None) -> None:
        super().__init__(transport or MockTransport())

    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        return self.transport.send(request)
