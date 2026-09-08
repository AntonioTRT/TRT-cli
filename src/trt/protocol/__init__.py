"""Protocol abstractions for TRT.

The protocol layer defines typed transport-independent request and response
models and provides a client abstraction for future real hardware communication.
"""

from trt.protocol.models import (
    DiscoverRequest,
    DiscoverResponse,
    BoardInfoRequest,
    BoardInfoResponse,
    BuildIdRequest,
    BuildIdResponse,
    GetCapabilitiesRequest,
    GetCapabilitiesResponse,
    GetVersionRequest,
    GetVersionResponse,
    GpioReadRequest,
    GpioReadResponse,
    GpioWriteRequest,
    GpioWriteResponse,
    ProtocolOperation,
    ProtocolRequest,
    ProtocolResponse,
)

__all__ = [
    "ProtocolOperation",
    "ProtocolRequest",
    "ProtocolResponse",
    "DiscoverRequest",
    "DiscoverResponse",
    "BoardInfoRequest",
    "BoardInfoResponse",
    "BuildIdRequest",
    "BuildIdResponse",
    "GetVersionRequest",
    "GetVersionResponse",
    "GetCapabilitiesRequest",
    "GetCapabilitiesResponse",
    "GpioReadRequest",
    "GpioReadResponse",
    "GpioWriteRequest",
    "GpioWriteResponse",
]
