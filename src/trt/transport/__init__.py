"""Transport abstractions for TRT.

The transport layer encapsulates how a message reaches a board. SerialTransport
provides the current real Arduino Uno path, while MockTransport remains
available for explicit tests and support paths.
"""

from trt.transport.base import Transport
from trt.transport.mock_transport import MockTransport
from trt.transport.serial_transport import SerialTransport

__all__ = ["Transport", "MockTransport", "SerialTransport"]
