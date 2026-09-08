"""Mock transport used for the current CLI implementation."""

from __future__ import annotations

from trt.protocol.models import (
    ActionResponse,
    AdcListRequest,
    AdcListResponse,
    AdcReadRequest,
    AdcReadResponse,
    AnalogChannelState,
    BoardCapabilitiesPayload,
    BoardRebootRequest,
    BoardResetRequest,
    DacListRequest,
    DacListResponse,
    DacReadRequest,
    DacReadResponse,
    DacSetRequest,
    DacSetResponse,
    DebugLogsRequest,
    DebugMonitorRequest,
    DebugResponse,
    DebugShellRequest,
    GpioListRequest,
    GpioListResponse,
    GpioPinState,
    GpioReadRequest,
    GpioReadResponse,
    GpioWriteRequest,
    GpioWriteResponse,
    I2cReadRequest,
    I2cScanRequest,
    I2cScanResponse,
    I2cTransferResponse,
    I2cWriteRequest,
    LcdActionResponse,
    LcdClearRequest,
    LcdInfoRequest,
    LcdInfoResponse,
    LcdResetRequest,
    LcdWriteRequest,
    LedActionResponse,
    LedBlinkRequest,
    LedBrightnessRequest,
    LedColorRequest,
    LedOffRequest,
    LedOnRequest,
    ModulesListRequest,
    ModulesListResponse,
    ProtocolOperation,
    ProtocolRequest,
    ProtocolResponse,
    PwmChannelState,
    PwmListRequest,
    PwmListResponse,
    PwmSetRequest,
    PwmStartRequest,
    PwmStopRequest,
    PwmActionResponse,
    SpiConfigRequest,
    SpiConfigResponse,
    SpiTransferRequest,
    SpiTransferResponse,
)
from trt.transport.base import Transport


class MockTransport(Transport):
    """Transport implementation that simulates device communication."""

    def send(self, request: ProtocolRequest) -> ProtocolResponse:
        if isinstance(request, BoardResetRequest):
            return ActionResponse(operation=request.operation, board_id=request.board_id, label="board reset", note=self._board_note(request.board_id))

        if isinstance(request, BoardRebootRequest):
            return ActionResponse(operation=request.operation, board_id=request.board_id, label="board reboot", note=self._board_note(request.board_id))

        if isinstance(request, ModulesListRequest):
            return ModulesListResponse(
                board_id=request.board_id,
                modules=(),
                message="No module data - firmware not connected.",
                note=self._board_note(request.board_id),
            )

        if isinstance(request, GpioListRequest):
            return GpioListResponse(board_id=request.board_id, pins=self._gpio_pins(), note=self._board_note(request.board_id))

        if isinstance(request, GpioReadRequest):
            return GpioReadResponse(board_id=request.board_id, pin=request.pin, value="0")

        if isinstance(request, GpioWriteRequest):
            return GpioWriteResponse(board_id=request.board_id, pin=request.pin, value=str(request.value))

        if isinstance(request, PwmListRequest):
            return PwmListResponse(board_id=request.board_id, channels=self._pwm_channels(), note=self._board_note(request.board_id))

        if isinstance(request, PwmStartRequest | PwmStopRequest):
            return PwmActionResponse(operation=request.operation, board_id=request.board_id, channel=request.channel)

        if isinstance(request, PwmSetRequest):
            return PwmActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                channel=request.channel,
                frequency=request.frequency,
                duty=request.duty,
            )

        if isinstance(request, AdcListRequest):
            return AdcListResponse(board_id=request.board_id, channels=self._adc_channels(), note=self._board_note(request.board_id))

        if isinstance(request, AdcReadRequest):
            return AdcReadResponse(board_id=request.board_id, channel=request.channel, value=0, millivolts="0.00")

        if isinstance(request, DacListRequest):
            return DacListResponse(board_id=request.board_id, channels=self._dac_channels(), note=self._board_note(request.board_id))

        if isinstance(request, DacReadRequest):
            return DacReadResponse(board_id=request.board_id, channel=request.channel, value=0, millivolts="0.00")

        if isinstance(request, DacSetRequest):
            return DacSetResponse(board_id=request.board_id, channel=request.channel, value=request.value, millivolts="0.00")

        if isinstance(request, I2cScanRequest):
            return I2cScanResponse(
                board_id=request.board_id,
                devices=(),
                message="No devices found - mock scan, no hardware connected.",
                note=self._board_note(request.board_id),
            )

        if isinstance(request, I2cReadRequest):
            return I2cTransferResponse(
                operation=ProtocolOperation.I2C_READ,
                board_id=request.board_id,
                address=request.address,
                register=request.register,
                length=request.length,
            )

        if isinstance(request, I2cWriteRequest):
            return I2cTransferResponse(
                operation=ProtocolOperation.I2C_WRITE,
                board_id=request.board_id,
                address=request.address,
                register=request.register,
                data=request.data,
            )

        if isinstance(request, SpiTransferRequest):
            return SpiTransferResponse(board_id=request.board_id, tx=request.data, rx="0x00")

        if isinstance(request, SpiConfigRequest):
            return SpiConfigResponse(
                board_id=request.board_id,
                baudrate=request.baudrate,
                mode=request.mode,
                msb_first=request.msb_first,
            )

        if isinstance(request, DebugLogsRequest | DebugMonitorRequest | DebugShellRequest):
            return DebugResponse(
                operation=request.operation,
                board_id=request.board_id,
                message=self._debug_message(request.operation),
                note=self._board_note(request.board_id),
            )

        if isinstance(request, LcdInfoRequest):
            return LcdInfoResponse(
                board_id=request.board_id,
                display_type="HD44780-compatible (I2C)",
                columns="unknown - not connected",
                rows="unknown - not connected",
                backlight="unknown - not connected",
                note=self._hardware_note("LCD"),
            )

        if isinstance(request, LcdResetRequest | LcdClearRequest):
            return LcdActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                label=self._lcd_label(request.operation),
                note=self._hardware_note("LCD"),
            )

        if isinstance(request, LcdWriteRequest):
            return LcdActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                label="LCD write",
                note=self._hardware_note("LCD"),
                text=request.text,
                line=request.line,
                col=request.col,
            )

        if isinstance(request, LedOnRequest | LedOffRequest):
            return LedActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                label=self._led_label(request.operation),
                note=self._hardware_note("LED"),
            )

        if isinstance(request, LedBlinkRequest):
            return LedActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                label="LED BLINK",
                note=self._hardware_note("LED"),
                count=request.count,
                interval_ms=request.interval_ms,
            )

        if isinstance(request, LedBrightnessRequest):
            return LedActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                label="LED BRIGHTNESS",
                note=self._hardware_note("LED"),
                level=request.level,
            )

        if isinstance(request, LedColorRequest):
            return LedActionResponse(
                operation=request.operation,
                board_id=request.board_id,
                label="LED COLOR",
                note=self._hardware_note("LED"),
                red=request.red,
                green=request.green,
                blue=request.blue,
            )

        return ActionResponse(operation=request.operation, board_id=request.board_id, label=request.operation.value)

    def is_available(self) -> bool:
        return True

    def _board_note(self, board_id: str) -> str:
        return f"Mock data for {board_id}. Real values will appear once TRT Protocol is implemented."

    def _hardware_note(self, capability: str) -> str:
        return f"Hardware not connected. {capability} support will be activated once TRT Protocol is implemented."

    def _gpio_pins(self) -> tuple[GpioPinState, ...]:
        return (
            GpioPinState(pin="PA0", direction="INPUT", value="0"),
            GpioPinState(pin="PA1", direction="INPUT", value="1"),
            GpioPinState(pin="PA5", direction="OUTPUT", value="1"),
            GpioPinState(pin="PB3", direction="OUTPUT", value="0"),
        )

    def _pwm_channels(self) -> tuple[PwmChannelState, ...]:
        return (
            PwmChannelState(channel="1", frequency="1000", duty="50", state="STOPPED"),
            PwmChannelState(channel="2", frequency="20000", duty="25", state="STOPPED"),
        )

    def _adc_channels(self) -> tuple[AnalogChannelState, ...]:
        return (
            AnalogChannelState(channel="1", resolution="12", reference="3.3V", value="-"),
            AnalogChannelState(channel="2", resolution="12", reference="3.3V", value="-"),
            AnalogChannelState(channel="3", resolution="12", reference="3.3V", value="-"),
        )

    def _dac_channels(self) -> tuple[AnalogChannelState, ...]:
        return (
            AnalogChannelState(channel="1", resolution="12", reference="3.3V", value="0"),
            AnalogChannelState(channel="2", resolution="12", reference="3.3V", value="0"),
        )

    def _debug_message(self, operation: ProtocolOperation) -> str:
        messages = {
            ProtocolOperation.DEBUG_LOGS: "No log data - firmware not connected.",
            ProtocolOperation.DEBUG_MONITOR: "No data - firmware not connected.",
            ProtocolOperation.DEBUG_SHELL: "Interactive shell will be available once TRT Protocol is implemented.",
        }
        return messages[operation]

    def _lcd_label(self, operation: ProtocolOperation) -> str:
        labels = {
            ProtocolOperation.LCD_RESET: "LCD reset",
            ProtocolOperation.LCD_CLEAR: "LCD clear",
        }
        return labels[operation]

    def _led_label(self, operation: ProtocolOperation) -> str:
        labels = {
            ProtocolOperation.LED_ON: "LED ON",
            ProtocolOperation.LED_OFF: "LED OFF",
        }
        return labels[operation]
