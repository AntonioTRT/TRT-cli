"""Version information for TRT."""

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_info() -> tuple[int, int, int]:
    """Get the version as a tuple of integers."""
    return __version_info__
