"""Application service for LED operations."""

from __future__ import annotations

from trt.protocol.models import (
    LedBlinkRequest,
    LedBrightnessRequest,
    LedColorRequest,
    LedOffRequest,
    LedOnRequest,
    ProtocolRequest,
    ProtocolResponse,
)
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient


class LEDService:
    """Routes LED operations through the protocol client."""

    def __init__(self, protocol_client: ProtocolClient | None = None) -> None:
        self.protocol_client = protocol_client or MockProtocolClient()

    def execute(self, request: ProtocolRequest) -> ProtocolResponse:
        return self.protocol_client.send(request)

    def on(self) -> ProtocolResponse:
        return self.execute(LedOnRequest())

    def off(self) -> ProtocolResponse:
        return self.execute(LedOffRequest())

    def blink(self, count: int, interval_ms: int) -> ProtocolResponse:
        return self.execute(LedBlinkRequest(count=count, interval_ms=interval_ms))

    def brightness(self, level: int) -> ProtocolResponse:
        return self.execute(LedBrightnessRequest(level=level))

    def color(self, red: int, green: int, blue: int) -> ProtocolResponse:
        return self.execute(LedColorRequest(red=red, green=green, blue=blue))
