"""Mock transport used for the current CLI implementation."""

from __future__ import annotations

from typing import Any

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

        if operation == "discover":
            return self._response(request, {"boards": self._mock_boards()})

        if operation in {"board_reset", "board_reboot"}:
            return self._response(request, {"label": operation.replace("_", " "), "note": self._board_note(request.board_id)})

        if operation == "modules_list":
            return self._response(
                request,
                {
                    "modules": [],
                    "message": "No module data - firmware not connected.",
                    "note": self._board_note(request.board_id),
                },
            )

        if request.capability == "gpio":
            return self._response(request, self._gpio_payload(operation, payload, request.board_id))

        if request.capability == "pwm":
            return self._response(request, self._pwm_payload(operation, payload, request.board_id))

        if request.capability == "adc":
            return self._response(request, self._adc_payload(operation, payload, request.board_id))

        if request.capability == "dac":
            return self._response(request, self._dac_payload(operation, payload, request.board_id))

        if request.capability == "i2c":
            return self._response(request, self._i2c_payload(operation, payload, request.board_id))

        if request.capability == "spi":
            return self._response(request, self._spi_payload(operation, payload))

        if request.capability == "debug_shell":
            return self._response(request, self._debug_payload(operation, request.board_id))

        if request.capability == "lcd":
            return self._response(request, self._lcd_payload(operation, payload))

        if request.capability == "led":
            return self._response(request, self._led_payload(operation, payload))

        return self._response(request, {"operation": operation, "value": payload})

    def is_available(self) -> bool:
        return True

    def _response(self, request: ProtocolRequest, payload: dict[str, Any]) -> ProtocolResponse:
        return ProtocolResponse(
            status="ok",
            payload=payload,
            board_id=request.board_id,
            capability=request.capability,
            mock=True,
        )

    def _mock_boards(self) -> list[dict[str, Any]]:
        return [
            {
                "board_id": "board0",
                "board_type": "TRT_CORE",
                "revision": "A1",
                "firmware": "0.1.0",
                "serial": "000001",
                "status": "ready",
                "transport": {"transport_type": "usb", "port": "COM3"},
                "capabilities": {
                    "gpio": True,
                    "pwm": True,
                    "adc": True,
                    "dac": True,
                    "i2c": True,
                    "spi": True,
                    "uart": True,
                    "debug_shell": True,
                },
            },
            {
                "board_id": "board1",
                "board_type": "Arduino",
                "revision": "R3",
                "firmware": "0.1.0",
                "serial": "000002",
                "status": "connected",
                "transport": {"transport_type": "usb", "port": "COM4"},
                "capabilities": {"gpio": True, "pwm": True, "adc": True, "i2c": True},
            },
        ]

    def _board_note(self, board_id: str) -> str:
        return f"Mock data for {board_id}. Real values will appear once TRT Protocol is implemented."

    def _hardware_note(self, capability: str) -> str:
        return f"Hardware not connected. {capability} support will be activated once TRT Protocol is implemented."

    def _gpio_payload(self, operation: str, payload: dict[str, Any], board_id: str) -> dict[str, Any]:
        if operation == "gpio_list":
            return {
                "pins": [
                    {"pin": "PA0", "direction": "INPUT", "value": "0"},
                    {"pin": "PA1", "direction": "INPUT", "value": "1"},
                    {"pin": "PA5", "direction": "OUTPUT", "value": "1"},
                    {"pin": "PB3", "direction": "OUTPUT", "value": "0"},
                ],
                "note": self._board_note(board_id),
            }
        return {"operation": operation, "pin": payload.get("pin", "unknown"), "value": payload.get("value", "0")}

    def _pwm_channels(self) -> list[dict[str, Any]]:
        return [
            {"channel": "1", "frequency": "1000", "duty": "50", "state": "STOPPED"},
            {"channel": "2", "frequency": "20000", "duty": "25", "state": "STOPPED"},
        ]

    def _pwm_payload(self, operation: str, payload: dict[str, Any], board_id: str) -> dict[str, Any]:
        if operation == "pwm_list":
            return {"channels": self._pwm_channels(), "note": self._board_note(board_id)}
        return {"operation": operation, **payload}

    def _adc_payload(self, operation: str, payload: dict[str, Any], board_id: str) -> dict[str, Any]:
        if operation == "adc_list":
            return {
                "channels": [
                    {"channel": "1", "resolution": "12", "reference": "3.3V", "last_value": "-"},
                    {"channel": "2", "resolution": "12", "reference": "3.3V", "last_value": "-"},
                    {"channel": "3", "resolution": "12", "reference": "3.3V", "last_value": "-"},
                ],
                "note": self._board_note(board_id),
            }
        return {"operation": operation, "channel": payload.get("channel", 0), "value": 0, "millivolts": "0.00"}

    def _dac_payload(self, operation: str, payload: dict[str, Any], board_id: str) -> dict[str, Any]:
        if operation == "dac_list":
            return {
                "channels": [
                    {"channel": "1", "resolution": "12", "reference": "3.3V", "current_value": "0"},
                    {"channel": "2", "resolution": "12", "reference": "3.3V", "current_value": "0"},
                ],
                "note": self._board_note(board_id),
            }
        return {
            "operation": operation,
            "channel": payload.get("channel", 0),
            "value": payload.get("value", 0),
            "millivolts": "0.00",
        }

    def _i2c_payload(self, operation: str, payload: dict[str, Any], board_id: str) -> dict[str, Any]:
        if operation == "i2c_scan":
            return {
                "operation": operation,
                "devices": [],
                "message": "No devices found - mock scan, no hardware connected.",
                "note": self._board_note(board_id),
            }
        return {
            "operation": operation,
            "address": payload.get("address", "0x48"),
            "register": payload.get("register", "0x00"),
            "length": payload.get("length"),
            "data": payload.get("data"),
        }

    def _spi_payload(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "spi_transfer":
            return {"operation": operation, "tx": payload.get("data", "0x00"), "rx": "0x00"}
        return {
            "operation": operation,
            "baudrate": payload.get("baudrate", 1_000_000),
            "mode": payload.get("mode", 0),
            "msb_first": payload.get("msb_first", True),
        }

    def _debug_payload(self, operation: str, board_id: str) -> dict[str, Any]:
        messages = {
            "debug_logs": "No log data - firmware not connected.",
            "debug_monitor": "No data - firmware not connected.",
            "debug_shell": "Interactive shell will be available once TRT Protocol is implemented.",
        }
        return {"operation": operation, "message": messages.get(operation, "No data - firmware not connected."), "note": self._board_note(board_id)}

    def _lcd_payload(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "lcd_info":
            return {
                "type": "HD44780-compatible (I2C)",
                "columns": "unknown - not connected",
                "rows": "unknown - not connected",
                "backlight": "unknown - not connected",
                "note": self._hardware_note("LCD"),
            }
        labels = {
            "lcd_reset": "LCD reset",
            "lcd_clear": "LCD clear",
            "lcd_write": "LCD write",
        }
        return {"operation": operation, "label": labels.get(operation, operation), "note": self._hardware_note("LCD"), **payload}

    def _led_payload(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        labels = {
            "led_on": "LED ON",
            "led_off": "LED OFF",
            "led_blink": "LED BLINK",
            "led_brightness": "LED BRIGHTNESS",
            "led_color": "LED COLOR",
        }
        return {"operation": operation, "label": labels.get(operation, operation), "note": self._hardware_note("LED"), **payload}
