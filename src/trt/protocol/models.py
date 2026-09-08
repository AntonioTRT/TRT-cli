"""Typed protocol contract for TRT.

The protocol layer uses typed request and response models so service code does
not depend on raw operation strings or unstructured payload dictionaries. These
models are the host-side contract that TRT-Core firmware can implement later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ProtocolOperation(str, Enum):
    """Typed identifiers for supported protocol operations."""

    DISCOVER = "discover"
    GET_VERSION = "get_version"
    GET_CAPABILITIES = "get_capabilities"
    BOARD_INFO = "board_info"
    BUILD_ID = "build_id"
    BOARD_RESET = "board_reset"
    BOARD_REBOOT = "board_reboot"
    MODULES_LIST = "modules_list"
    GPIO_LIST = "gpio_list"
    GPIO_READ = "gpio_read"
    GPIO_WRITE = "gpio_write"
    PWM_LIST = "pwm_list"
    PWM_START = "pwm_start"
    PWM_STOP = "pwm_stop"
    PWM_SET = "pwm_set"
    ADC_LIST = "adc_list"
    ADC_READ = "adc_read"
    DAC_LIST = "dac_list"
    DAC_READ = "dac_read"
    DAC_SET = "dac_set"
    I2C_SCAN = "i2c_scan"
    I2C_READ = "i2c_read"
    I2C_WRITE = "i2c_write"
    SPI_TRANSFER = "spi_transfer"
    SPI_CONFIG = "spi_config"
    DEBUG_LOGS = "debug_logs"
    DEBUG_MONITOR = "debug_monitor"
    DEBUG_SHELL = "debug_shell"
    LCD_INFO = "lcd_info"
    LCD_RESET = "lcd_reset"
    LCD_CLEAR = "lcd_clear"
    LCD_WRITE = "lcd_write"
    LED_ON = "led_on"
    LED_OFF = "led_off"
    LED_BLINK = "led_blink"
    LED_BRIGHTNESS = "led_brightness"
    LED_COLOR = "led_color"


@dataclass(frozen=True, kw_only=True)
class ProtocolRequest:
    """Base class for typed protocol requests."""

    operation: ProtocolOperation
    board_id: str
    capability: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class DiscoverRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.DISCOVER, init=False)
    board_id: str = "*"
    capability: str | None = field(default="discovery", init=False)


@dataclass(frozen=True, kw_only=True)
class GetVersionRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.GET_VERSION, init=False)


@dataclass(frozen=True, kw_only=True)
class GetCapabilitiesRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.GET_CAPABILITIES, init=False)


@dataclass(frozen=True, kw_only=True)
class BoardInfoRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.BOARD_INFO, init=False)


@dataclass(frozen=True, kw_only=True)
class BuildIdRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.BUILD_ID, init=False)


@dataclass(frozen=True, kw_only=True)
class BoardResetRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.BOARD_RESET, init=False)


@dataclass(frozen=True, kw_only=True)
class BoardRebootRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.BOARD_REBOOT, init=False)


@dataclass(frozen=True, kw_only=True)
class ModulesListRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.MODULES_LIST, init=False)


@dataclass(frozen=True, kw_only=True)
class GpioListRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.GPIO_LIST, init=False)
    capability: str | None = field(default="gpio", init=False)


@dataclass(frozen=True, kw_only=True)
class GpioReadRequest(ProtocolRequest):
    pin: str
    operation: ProtocolOperation = field(default=ProtocolOperation.GPIO_READ, init=False)
    capability: str | None = field(default="gpio", init=False)


@dataclass(frozen=True, kw_only=True)
class GpioWriteRequest(ProtocolRequest):
    pin: str
    value: int
    operation: ProtocolOperation = field(default=ProtocolOperation.GPIO_WRITE, init=False)
    capability: str | None = field(default="gpio", init=False)


@dataclass(frozen=True, kw_only=True)
class PwmListRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.PWM_LIST, init=False)
    capability: str | None = field(default="pwm", init=False)


@dataclass(frozen=True, kw_only=True)
class PwmStartRequest(ProtocolRequest):
    channel: int
    operation: ProtocolOperation = field(default=ProtocolOperation.PWM_START, init=False)
    capability: str | None = field(default="pwm", init=False)


@dataclass(frozen=True, kw_only=True)
class PwmStopRequest(ProtocolRequest):
    channel: int
    operation: ProtocolOperation = field(default=ProtocolOperation.PWM_STOP, init=False)
    capability: str | None = field(default="pwm", init=False)


@dataclass(frozen=True, kw_only=True)
class PwmSetRequest(ProtocolRequest):
    channel: int
    frequency: float
    duty: float
    operation: ProtocolOperation = field(default=ProtocolOperation.PWM_SET, init=False)
    capability: str | None = field(default="pwm", init=False)


@dataclass(frozen=True, kw_only=True)
class AdcListRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.ADC_LIST, init=False)
    capability: str | None = field(default="adc", init=False)


@dataclass(frozen=True, kw_only=True)
class AdcReadRequest(ProtocolRequest):
    channel: int
    operation: ProtocolOperation = field(default=ProtocolOperation.ADC_READ, init=False)
    capability: str | None = field(default="adc", init=False)


@dataclass(frozen=True, kw_only=True)
class DacListRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.DAC_LIST, init=False)
    capability: str | None = field(default="dac", init=False)


@dataclass(frozen=True, kw_only=True)
class DacReadRequest(ProtocolRequest):
    channel: int
    operation: ProtocolOperation = field(default=ProtocolOperation.DAC_READ, init=False)
    capability: str | None = field(default="dac", init=False)


@dataclass(frozen=True, kw_only=True)
class DacSetRequest(ProtocolRequest):
    channel: int
    value: int
    operation: ProtocolOperation = field(default=ProtocolOperation.DAC_SET, init=False)
    capability: str | None = field(default="dac", init=False)


@dataclass(frozen=True, kw_only=True)
class I2cScanRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.I2C_SCAN, init=False)
    capability: str | None = field(default="i2c", init=False)


@dataclass(frozen=True, kw_only=True)
class I2cReadRequest(ProtocolRequest):
    address: str
    register: str
    length: int
    operation: ProtocolOperation = field(default=ProtocolOperation.I2C_READ, init=False)
    capability: str | None = field(default="i2c", init=False)


@dataclass(frozen=True, kw_only=True)
class I2cWriteRequest(ProtocolRequest):
    address: str
    register: str
    data: str
    operation: ProtocolOperation = field(default=ProtocolOperation.I2C_WRITE, init=False)
    capability: str | None = field(default="i2c", init=False)


@dataclass(frozen=True, kw_only=True)
class SpiTransferRequest(ProtocolRequest):
    data: str
    operation: ProtocolOperation = field(default=ProtocolOperation.SPI_TRANSFER, init=False)
    capability: str | None = field(default="spi", init=False)


@dataclass(frozen=True, kw_only=True)
class SpiConfigRequest(ProtocolRequest):
    baudrate: int
    mode: int
    msb_first: bool
    operation: ProtocolOperation = field(default=ProtocolOperation.SPI_CONFIG, init=False)
    capability: str | None = field(default="spi", init=False)


@dataclass(frozen=True, kw_only=True)
class DebugLogsRequest(ProtocolRequest):
    follow: bool = False
    operation: ProtocolOperation = field(default=ProtocolOperation.DEBUG_LOGS, init=False)
    capability: str | None = field(default="debug_shell", init=False)


@dataclass(frozen=True, kw_only=True)
class DebugMonitorRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.DEBUG_MONITOR, init=False)
    capability: str | None = field(default="debug_shell", init=False)


@dataclass(frozen=True, kw_only=True)
class DebugShellRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.DEBUG_SHELL, init=False)
    capability: str | None = field(default="debug_shell", init=False)


@dataclass(frozen=True, kw_only=True)
class LcdInfoRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.LCD_INFO, init=False)
    board_id: str = "default"
    capability: str | None = field(default="lcd", init=False)


@dataclass(frozen=True, kw_only=True)
class LcdResetRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.LCD_RESET, init=False)
    board_id: str = "default"
    capability: str | None = field(default="lcd", init=False)


@dataclass(frozen=True, kw_only=True)
class LcdClearRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.LCD_CLEAR, init=False)
    board_id: str = "default"
    capability: str | None = field(default="lcd", init=False)


@dataclass(frozen=True, kw_only=True)
class LcdWriteRequest(ProtocolRequest):
    text: str
    line: int
    col: int
    operation: ProtocolOperation = field(default=ProtocolOperation.LCD_WRITE, init=False)
    board_id: str = "default"
    capability: str | None = field(default="lcd", init=False)


@dataclass(frozen=True, kw_only=True)
class LedOnRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.LED_ON, init=False)
    board_id: str = "default"
    capability: str | None = field(default="led", init=False)


@dataclass(frozen=True, kw_only=True)
class LedOffRequest(ProtocolRequest):
    operation: ProtocolOperation = field(default=ProtocolOperation.LED_OFF, init=False)
    board_id: str = "default"
    capability: str | None = field(default="led", init=False)


@dataclass(frozen=True, kw_only=True)
class LedBlinkRequest(ProtocolRequest):
    count: int
    interval_ms: int
    operation: ProtocolOperation = field(default=ProtocolOperation.LED_BLINK, init=False)
    board_id: str = "default"
    capability: str | None = field(default="led", init=False)


@dataclass(frozen=True, kw_only=True)
class LedBrightnessRequest(ProtocolRequest):
    level: int
    operation: ProtocolOperation = field(default=ProtocolOperation.LED_BRIGHTNESS, init=False)
    board_id: str = "default"
    capability: str | None = field(default="led", init=False)


@dataclass(frozen=True, kw_only=True)
class LedColorRequest(ProtocolRequest):
    red: int
    green: int
    blue: int
    operation: ProtocolOperation = field(default=ProtocolOperation.LED_COLOR, init=False)
    board_id: str = "default"
    capability: str | None = field(default="led", init=False)


@dataclass(frozen=True)
class BoardCapabilitiesPayload:
    gpio: bool = False
    pwm: bool = False
    adc: bool = False
    dac: bool = False
    i2c: bool = False
    spi: bool = False
    uart: bool = False
    can: bool = False
    lcd: bool = False
    relay: bool = False
    debug_shell: bool = False

    def to_dict(self) -> dict[str, bool]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class TransportPayload:
    transport_type: str
    port: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class DiscoveredBoardPayload:
    board_id: str
    board_type: str
    revision: str
    firmware: str
    serial: str | None
    status: str
    transport: TransportPayload
    capabilities: BoardCapabilitiesPayload

    def to_dict(self) -> dict[str, Any]:
        return {
            "board_id": self.board_id,
            "board_type": self.board_type,
            "revision": self.revision,
            "firmware": self.firmware,
            "serial": self.serial,
            "status": self.status,
            "transport": self.transport.to_dict(),
            "capabilities": self.capabilities.to_dict(),
        }


@dataclass(frozen=True)
class GpioPinState:
    pin: str
    direction: str
    value: str

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class PwmChannelState:
    channel: str
    frequency: str
    duty: str
    state: str

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class AnalogChannelState:
    channel: str
    resolution: str
    reference: str
    value: str

    def to_dict(self, value_key: str) -> dict[str, str]:
        return {
            "channel": self.channel,
            "resolution": self.resolution,
            "reference": self.reference,
            value_key: self.value,
        }


@dataclass(frozen=True, kw_only=True)
class ProtocolResponse:
    """Base class for typed protocol responses."""

    operation: ProtocolOperation
    status: str = "ok"
    board_id: str | None = None
    capability: str | None = None
    error: str | None = None
    mock: bool = True

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    def to_payload(self) -> dict[str, Any]:
        return {"operation": self.operation.value}


@dataclass(frozen=True, kw_only=True)
class DiscoverResponse(ProtocolResponse):
    boards: tuple[DiscoveredBoardPayload, ...]
    operation: ProtocolOperation = field(default=ProtocolOperation.DISCOVER, init=False)
    capability: str | None = field(default="discovery", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"boards": [board.to_dict() for board in self.boards]}


@dataclass(frozen=True, kw_only=True)
class GetVersionResponse(ProtocolResponse):
    version: str
    operation: ProtocolOperation = field(default=ProtocolOperation.GET_VERSION, init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"version": self.version}


@dataclass(frozen=True, kw_only=True)
class GetCapabilitiesResponse(ProtocolResponse):
    capabilities: BoardCapabilitiesPayload
    operation: ProtocolOperation = field(default=ProtocolOperation.GET_CAPABILITIES, init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"capabilities": self.capabilities.to_dict()}


@dataclass(frozen=True, kw_only=True)
class BoardInfoResponse(ProtocolResponse):
    board_type: str
    operation: ProtocolOperation = field(default=ProtocolOperation.BOARD_INFO, init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"board_type": self.board_type}


@dataclass(frozen=True, kw_only=True)
class BuildIdResponse(ProtocolResponse):
    build_id: str
    operation: ProtocolOperation = field(default=ProtocolOperation.BUILD_ID, init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"build_id": self.build_id}


@dataclass(frozen=True, kw_only=True)
class ActionResponse(ProtocolResponse):
    label: str
    note: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"operation": self.operation.value, "label": self.label}
        if self.note is not None:
            payload["note"] = self.note
        return payload


@dataclass(frozen=True, kw_only=True)
class ModulesListResponse(ProtocolResponse):
    modules: tuple[str, ...]
    message: str
    note: str
    operation: ProtocolOperation = field(default=ProtocolOperation.MODULES_LIST, init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"modules": list(self.modules), "message": self.message, "note": self.note}


@dataclass(frozen=True, kw_only=True)
class GpioListResponse(ProtocolResponse):
    pins: tuple[GpioPinState, ...]
    note: str
    operation: ProtocolOperation = field(default=ProtocolOperation.GPIO_LIST, init=False)
    capability: str | None = field(default="gpio", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"pins": [pin.to_dict() for pin in self.pins], "note": self.note}


@dataclass(frozen=True, kw_only=True)
class GpioReadResponse(ProtocolResponse):
    pin: str
    value: str
    operation: ProtocolOperation = field(default=ProtocolOperation.GPIO_READ, init=False)
    capability: str | None = field(default="gpio", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"operation": self.operation.value, "pin": self.pin, "value": self.value}


@dataclass(frozen=True, kw_only=True)
class GpioWriteResponse(GpioReadResponse):
    operation: ProtocolOperation = field(default=ProtocolOperation.GPIO_WRITE, init=False)


@dataclass(frozen=True, kw_only=True)
class PwmListResponse(ProtocolResponse):
    channels: tuple[PwmChannelState, ...]
    note: str
    operation: ProtocolOperation = field(default=ProtocolOperation.PWM_LIST, init=False)
    capability: str | None = field(default="pwm", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"channels": [channel.to_dict() for channel in self.channels], "note": self.note}


@dataclass(frozen=True, kw_only=True)
class PwmActionResponse(ProtocolResponse):
    channel: int
    frequency: float | None = None
    duty: float | None = None
    capability: str | None = field(default="pwm", init=False)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"operation": self.operation.value, "channel": self.channel}
        if self.frequency is not None:
            payload["frequency"] = self.frequency
        if self.duty is not None:
            payload["duty"] = self.duty
        return payload


@dataclass(frozen=True, kw_only=True)
class AnalogListResponse(ProtocolResponse):
    channels: tuple[AnalogChannelState, ...]
    note: str
    value_key: str = field(default="value", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"channels": [channel.to_dict(self.value_key) for channel in self.channels], "note": self.note}


@dataclass(frozen=True, kw_only=True)
class AdcListResponse(AnalogListResponse):
    operation: ProtocolOperation = field(default=ProtocolOperation.ADC_LIST, init=False)
    capability: str | None = field(default="adc", init=False)
    value_key: str = field(default="last_value", init=False)


@dataclass(frozen=True, kw_only=True)
class DacListResponse(AnalogListResponse):
    operation: ProtocolOperation = field(default=ProtocolOperation.DAC_LIST, init=False)
    capability: str | None = field(default="dac", init=False)
    value_key: str = field(default="current_value", init=False)


@dataclass(frozen=True, kw_only=True)
class AnalogReadResponse(ProtocolResponse):
    channel: int
    value: int
    millivolts: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "operation": self.operation.value,
            "channel": self.channel,
            "value": self.value,
            "millivolts": self.millivolts,
        }


@dataclass(frozen=True, kw_only=True)
class AdcReadResponse(AnalogReadResponse):
    operation: ProtocolOperation = field(default=ProtocolOperation.ADC_READ, init=False)
    capability: str | None = field(default="adc", init=False)


@dataclass(frozen=True, kw_only=True)
class DacReadResponse(AnalogReadResponse):
    operation: ProtocolOperation = field(default=ProtocolOperation.DAC_READ, init=False)
    capability: str | None = field(default="dac", init=False)


@dataclass(frozen=True, kw_only=True)
class DacSetResponse(AnalogReadResponse):
    operation: ProtocolOperation = field(default=ProtocolOperation.DAC_SET, init=False)
    capability: str | None = field(default="dac", init=False)


@dataclass(frozen=True, kw_only=True)
class I2cScanResponse(ProtocolResponse):
    devices: tuple[str, ...]
    message: str
    note: str
    operation: ProtocolOperation = field(default=ProtocolOperation.I2C_SCAN, init=False)
    capability: str | None = field(default="i2c", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"operation": self.operation.value, "devices": list(self.devices), "message": self.message, "note": self.note}


@dataclass(frozen=True, kw_only=True)
class I2cTransferResponse(ProtocolResponse):
    address: str
    register: str
    length: int | None = None
    data: str | None = None
    capability: str | None = field(default="i2c", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {
            "operation": self.operation.value,
            "address": self.address,
            "register": self.register,
            "length": self.length,
            "data": self.data,
        }


@dataclass(frozen=True, kw_only=True)
class SpiTransferResponse(ProtocolResponse):
    tx: str
    rx: str
    operation: ProtocolOperation = field(default=ProtocolOperation.SPI_TRANSFER, init=False)
    capability: str | None = field(default="spi", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"operation": self.operation.value, "tx": self.tx, "rx": self.rx}


@dataclass(frozen=True, kw_only=True)
class SpiConfigResponse(ProtocolResponse):
    baudrate: int
    mode: int
    msb_first: bool
    operation: ProtocolOperation = field(default=ProtocolOperation.SPI_CONFIG, init=False)
    capability: str | None = field(default="spi", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {"operation": self.operation.value, "baudrate": self.baudrate, "mode": self.mode, "msb_first": self.msb_first}


@dataclass(frozen=True, kw_only=True)
class DebugResponse(ProtocolResponse):
    message: str
    note: str

    def to_payload(self) -> dict[str, Any]:
        return {"operation": self.operation.value, "message": self.message, "note": self.note}


@dataclass(frozen=True, kw_only=True)
class LcdInfoResponse(ProtocolResponse):
    display_type: str
    columns: str
    rows: str
    backlight: str
    note: str
    operation: ProtocolOperation = field(default=ProtocolOperation.LCD_INFO, init=False)
    capability: str | None = field(default="lcd", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {
            "type": self.display_type,
            "columns": self.columns,
            "rows": self.rows,
            "backlight": self.backlight,
            "note": self.note,
        }


@dataclass(frozen=True, kw_only=True)
class LcdActionResponse(ActionResponse):
    text: str | None = None
    line: int | None = None
    col: int | None = None
    capability: str | None = field(default="lcd", init=False)

    def to_payload(self) -> dict[str, Any]:
        payload = super().to_payload()
        if self.text is not None:
            payload["text"] = self.text
        if self.line is not None:
            payload["line"] = self.line
        if self.col is not None:
            payload["col"] = self.col
        return payload


@dataclass(frozen=True, kw_only=True)
class LedActionResponse(ActionResponse):
    count: int | None = None
    interval_ms: int | None = None
    level: int | None = None
    red: int | None = None
    green: int | None = None
    blue: int | None = None
    capability: str | None = field(default="led", init=False)

    def to_payload(self) -> dict[str, Any]:
        payload = super().to_payload()
        for key in ("count", "interval_ms", "level", "red", "green", "blue"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        return payload
