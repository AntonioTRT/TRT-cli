"""Transport abstractions for TRT.

The transport layer encapsulates how a message reaches a board. The current
implementation intentionally provides a mock transport only, with extension
points reserved for future USB/CAN/TCP implementations.
"""

from trt.transport.base import Transport
from trt.transport.mock_transport import MockTransport

__all__ = ["Transport", "MockTransport"]
