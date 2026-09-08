"""Serial-backed TRT protocol client."""

from __future__ import annotations

from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.protocol.protocol_client import ProtocolClient
from trt.transport.serial_transport import SerialTransport


class SerialProtocolClient(ProtocolClient):
    """Protocol client that delegates typed requests to a serial transport."""

    def __init__(self, transport: SerialTransport | None = None) -> None:
        super().__init__(transport or SerialTransport())

    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        return self.transport.send(request)
