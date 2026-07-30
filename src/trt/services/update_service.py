"""TRT CLI update service.

Responsible for checking GitHub releases and coordinating CLI self-updates.
The CLI application (trt-cli) and board firmware updates are INDEPENDENT:

    trt update            → updates the trt-cli Python package on this machine
    trt board <id> update → updates firmware on a connected board (future)

This module handles only the CLI side.

GitHub API endpoint (Phase 2):
    GET https://api.github.com/repos/AntonioTRT/TRT-cli/releases/latest

Response fields used:
    tag_name  — latest release tag, e.g. "v0.2.0"
    html_url  — release page URL for display
    body      — release notes

Install strategies (Phase 2):
    1. pip install --upgrade trt-cli        (standard pip install)
    2. pipx upgrade trt-cli                 (pipx managed install)
    3. uv pip install --upgrade trt-cli     (uv managed install)

The service auto-detects which installer was used and selects the right
upgrade command.  For now all installation methods are scaffolded.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from trt.version import get_version, get_version_info

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_REPO         = "AntonioTRT/TRT-cli"
GITHUB_API_URL      = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
PYPI_PACKAGE_NAME   = "trt-cli"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class UpdateStatus(str, Enum):
    """Result of an update check."""

    UP_TO_DATE       = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    CHECK_FAILED     = "check_failed"
    UNKNOWN          = "unknown"


class InstallMethod(str, Enum):
    """How trt-cli was installed on this machine.

    Used to select the correct upgrade command.
    """

    PIP    = "pip"
    PIPX   = "pipx"
    UV     = "uv"
    UNKNOWN = "unknown"


@dataclass
class UpdateCheckResult:
    """Result returned by :func:`check_for_update`.

    Attributes:
        status:          Outcome of the version check.
        current_version: Version string currently installed.
        latest_version:  Version string from the latest GitHub release,
                         or None if the check failed.
        release_url:     Link to the GitHub releases page.
        error_message:   Human-readable description of any failure.
    """

    status: UpdateStatus
    current_version: str
    latest_version: Optional[str] = None
    release_url: str = GITHUB_RELEASES_URL
    error_message: Optional[str] = None

    @property
    def is_update_available(self) -> bool:
        return self.status == UpdateStatus.UPDATE_AVAILABLE

    @property
    def upgrade_command(self) -> str:
        """Return the shell command to install the latest version."""
        method = detect_install_method()
        if method == InstallMethod.PIPX:
            return f"pipx upgrade {PYPI_PACKAGE_NAME}"
        if method == InstallMethod.UV:
            return f"uv pip install --upgrade {PYPI_PACKAGE_NAME}"
        return f"pip install --upgrade {PYPI_PACKAGE_NAME}"


@dataclass
class UpdateInstallResult:
    """Result returned by :func:`install_update`."""

    success: bool
    message: str
    new_version: Optional[str] = None


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def _parse_version(tag: str) -> tuple[int, ...]:
    """Parse a version string or tag into a comparable tuple.

    Handles tags like "v0.2.0", "0.2.0", "0.2.0-beta.1".
    Pre-release suffixes are stripped for comparison.

    Args:
        tag: Version string, optionally prefixed with "v".

    Returns:
        Tuple of integers, e.g. (0, 2, 0).
    """
    clean = tag.lstrip("v").split("-")[0]  # strip "v" prefix and pre-release suffix
    try:
        return tuple(int(p) for p in clean.split("."))
    except ValueError:
        return (0,)


def _is_newer(candidate: str, baseline: str) -> bool:
    """Return True if *candidate* is strictly newer than *baseline*."""
    return _parse_version(candidate) > _parse_version(baseline)


# ---------------------------------------------------------------------------
# Install method detection
# ---------------------------------------------------------------------------

def detect_install_method() -> InstallMethod:
    """Detect how trt-cli was installed.

    Checks (in order):
        1. Whether the current executable path contains "pipx"
        2. Whether the current executable path contains "uv"
        3. Falls back to pip

    Returns:
        The detected :class:`InstallMethod`.

    Future:
        Read dist-info INSTALLER file for a more reliable detection.
    """
    exe = sys.executable.lower()
    if "pipx" in exe:
        return InstallMethod.PIPX
    if "uv" in exe:
        return InstallMethod.UV
    # Phase 2: read trt_cli-*.dist-info/INSTALLER for precise detection
    return InstallMethod.PIP


# ---------------------------------------------------------------------------
# Core service functions
# ---------------------------------------------------------------------------

def check_for_update() -> UpdateCheckResult:
    """Check GitHub releases for a newer version of trt-cli.

    Phase 1 (current): returns UP_TO_DATE with a note that GitHub checking
    is not yet implemented.

    Phase 2: performs a real HTTP GET to :data:`GITHUB_API_URL`, parses the
    ``tag_name`` field, compares it against the installed version, and
    returns an appropriate :class:`UpdateCheckResult`.

    Returns:
        :class:`UpdateCheckResult` describing the outcome.
    """
    current = get_version()

    # ------------------------------------------------------------------
    # Phase 2 implementation goes here.
    #
    # Example:
    #
    #   import urllib.request, json
    #   try:
    #       with urllib.request.urlopen(GITHUB_API_URL, timeout=5) as resp:
    #           data = json.loads(resp.read())
    #       latest_tag = data["tag_name"]          # e.g. "v0.2.0"
    #       latest_ver = latest_tag.lstrip("v")
    #       release_url = data.get("html_url", GITHUB_RELEASES_URL)
    #       if _is_newer(latest_ver, current):
    #           return UpdateCheckResult(
    #               status=UpdateStatus.UPDATE_AVAILABLE,
    #               current_version=current,
    #               latest_version=latest_ver,
    #               release_url=release_url,
    #           )
    #       return UpdateCheckResult(
    #           status=UpdateStatus.UP_TO_DATE,
    #           current_version=current,
    #           latest_version=latest_ver,
    #           release_url=release_url,
    #       )
    #   except Exception as exc:
    #       return UpdateCheckResult(
    #           status=UpdateStatus.CHECK_FAILED,
    #           current_version=current,
    #           error_message=str(exc),
    #       )
    # ------------------------------------------------------------------

    # Phase 1: GitHub check not yet implemented
    return UpdateCheckResult(
        status=UpdateStatus.UP_TO_DATE,
        current_version=current,
        latest_version=None,
        error_message="GitHub release checking will be available in a future release.",
    )


def install_update(target_version: Optional[str] = None) -> UpdateInstallResult:
    """Install the latest (or a specific) version of trt-cli.

    Phase 1 (current): returns a descriptive mock result explaining that
    automatic installation is not yet implemented.

    Phase 2: builds and executes the appropriate upgrade command using the
    detected install method (pip / pipx / uv).

    Args:
        target_version: Specific version to install, or None for latest.

    Returns:
        :class:`UpdateInstallResult` describing the outcome.
    """
    # ------------------------------------------------------------------
    # Phase 2 implementation goes here.
    #
    #   check = check_for_update()
    #   if not check.is_update_available and target_version is None:
    #       return UpdateInstallResult(success=True, message="Already up to date.")
    #
    #   version_spec = f"=={target_version}" if target_version else ""
    #   cmd = check.upgrade_command + version_spec
    #
    #   result = subprocess.run(
    #       cmd.split(), capture_output=True, text=True, check=False
    #   )
    #   if result.returncode == 0:
    #       new_ver = get_version()  # re-import after update
    #       return UpdateInstallResult(
    #           success=True,
    #           message=f"Updated successfully.",
    #           new_version=new_ver,
    #       )
    #   return UpdateInstallResult(
    #       success=False,
    #       message=result.stderr.strip() or "Installation failed.",
    #   )
    # ------------------------------------------------------------------

    method = detect_install_method()
    cmd = UpdateCheckResult(
        status=UpdateStatus.UNKNOWN,
        current_version=get_version(),
    ).upgrade_command

    return UpdateInstallResult(
        success=False,
        message=(
            f"Automatic installation is not yet implemented.\n"
            f"Run the following command manually to upgrade:\n\n"
            f"    {cmd}"
        ),
    )
