"""Application service for LCD operations."""

from __future__ import annotations

from trt.protocol.models import (
    LcdClearRequest,
    LcdInfoRequest,
    LcdResetRequest,
    LcdWriteRequest,
    ProtocolRequest,
    ProtocolResponse,
)
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient


class LCDService:
    """Routes LCD operations through the protocol client."""

    def __init__(self, protocol_client: ProtocolClient | None = None) -> None:
        self.protocol_client = protocol_client or MockProtocolClient()

    def execute(self, request: ProtocolRequest) -> ProtocolResponse:
        return self.protocol_client.send(request)

    def info(self) -> ProtocolResponse:
        return self.execute(LcdInfoRequest())

    def reset(self) -> ProtocolResponse:
        return self.execute(LcdResetRequest())

    def clear(self) -> ProtocolResponse:
        return self.execute(LcdClearRequest())

    def write(self, text: str, line: int, col: int) -> ProtocolResponse:
        return self.execute(LcdWriteRequest(text=text, line=line, col=col))
