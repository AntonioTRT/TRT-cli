"""Application service layer for TRT.

This package contains business logic that sits between the CLI layer and the
lower-level protocol, repository, and transport layers. Commands orchestrate
through services rather than directly constructing state or acting on mock
hardware behavior.
"""

from trt.services.board_discovery_service import BoardDiscoveryService
from trt.services.board_service import BoardService
from trt.services.capability_service import CapabilityService
from trt.services.update_service import (
    InstallMethod,
    UpdateStatus,
    check_for_update,
    detect_install_method,
    install_update,
)

__all__ = [
    "BoardDiscoveryService",
    "BoardService",
    "CapabilityService",
    "InstallMethod",
    "UpdateStatus",
    "check_for_update",
    "detect_install_method",
    "install_update",
]
