"""Application service for LED operations."""

from __future__ import annotations

from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient


class LEDService:
    """Routes LED operations through the protocol client."""

    def __init__(self, protocol_client: ProtocolClient | None = None) -> None:
        self.protocol_client = protocol_client or MockProtocolClient()

    def execute(self, operation: str, payload: dict[str, object] | None = None) -> ProtocolResponse:
        request = ProtocolRequest(
            operation=operation,
            board_id="default",
            capability="led",
            payload=payload or {},
        )
        return self.protocol_client.send(request)

    def on(self) -> ProtocolResponse:
        return self.execute("led_on")

    def off(self) -> ProtocolResponse:
        return self.execute("led_off")

    def blink(self, count: int, interval_ms: int) -> ProtocolResponse:
        return self.execute("led_blink", {"count": count, "interval_ms": interval_ms})

    def brightness(self, level: int) -> ProtocolResponse:
        return self.execute("led_brightness", {"level": level})

    def color(self, red: int, green: int, blue: int) -> ProtocolResponse:
        return self.execute("led_color", {"red": red, "green": green, "blue": blue})