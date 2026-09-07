"""Protocol abstractions for TRT.

The protocol layer defines transport-independent request and response models and
provides a client abstraction for future real hardware communication.
"""

from trt.protocol.models import ProtocolRequest, ProtocolResponse
from trt.protocol.protocol_client import MockProtocolClient, ProtocolClient

__all__ = [
    "ProtocolClient",
    "MockProtocolClient",
    "ProtocolRequest",
    "ProtocolResponse",
]
