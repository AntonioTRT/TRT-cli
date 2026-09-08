"""Application service for LCD operations."""

from __future__ import annotations

from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient


class LCDService:
    """Routes LCD operations through the protocol client."""

    def __init__(self, protocol_client: ProtocolClient | None = None) -> None:
        self.protocol_client = protocol_client or MockProtocolClient()

    def execute(self, operation: str, payload: dict[str, object] | None = None) -> ProtocolResponse:
        request = ProtocolRequest(
            operation=operation,
            board_id="default",
            capability="lcd",
            payload=payload or {},
        )
        return self.protocol_client.send(request)

    def info(self) -> ProtocolResponse:
        return self.execute("lcd_info")

    def reset(self) -> ProtocolResponse:
        return self.execute("lcd_reset")

    def clear(self) -> ProtocolResponse:
        return self.execute("lcd_clear")

    def write(self, text: str, line: int, col: int) -> ProtocolResponse:
        return self.execute("lcd_write", {"text": text, "line": line, "col": col})