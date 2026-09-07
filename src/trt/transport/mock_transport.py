"""Mock transport used for the current CLI implementation."""

from __future__ import annotations

from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.transport.base import Transport


class MockTransport(Transport):
    """Transport implementation that simulates device communication.

    This is intentionally a mock implementation so the protocol layer can be
    exercised without real USB/CAN/TCP connectivity.
    """

    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        operation = request.operation
        payload = request.payload

        if request.capability == "gpio":
            value = payload.get("value", "0")
            return ProtocolResponse(
                status="ok",
                payload={"operation": operation, "pin": payload.get("pin", "unknown"), "value": value},
                board_id=request.board_id,
                capability=request.capability,
                mock=True,
            )

        if request.capability == "adc":
            return ProtocolResponse(
                status="ok",
                payload={"operation": operation, "channel": payload.get("channel", 0), "value": 0},
                board_id=request.board_id,
                capability=request.capability,
                mock=True,
            )

        if request.capability == "i2c":
            return ProtocolResponse(
                status="ok",
                payload={"operation": operation, "devices": []},
                board_id=request.board_id,
                capability=request.capability,
                mock=True,
            )

        if request.capability == "spi":
            return ProtocolResponse(
                status="ok",
                payload={"operation": operation, "tx": payload.get("data", "0x00"), "rx": "0x00"},
                board_id=request.board_id,
                capability=request.capability,
                mock=True,
            )

        return ProtocolResponse(
            status="ok",
            payload={"operation": operation, "value": payload},
            board_id=request.board_id,
            capability=request.capability,
            mock=True,
        )

    def is_available(self) -> bool:
        return True
