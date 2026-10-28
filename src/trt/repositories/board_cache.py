"""Persistent cache for recently discovered serial board connections."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypedDict


class SerialConnection(TypedDict):
    port: str
    baudrate: int


def cache_path() -> Path:
    override = os.environ.get("TRT_CLI_BOARD_CACHE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".trt" / "boards.json"


def load_serial_connections() -> dict[str, SerialConnection]:
    path = cache_path()
    if not path.exists():
        return {}
    try:
        contents = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read TRT board cache at {path}: {error}") from error

    if not isinstance(contents, dict) or not isinstance(contents.get("boards"), dict):
        raise RuntimeError(f"TRT board cache at {path} has an invalid format")

    connections: dict[str, SerialConnection] = {}
    for board_id, entry in contents["boards"].items():
        if (
            isinstance(board_id, str)
            and isinstance(entry, dict)
            and isinstance(entry.get("port"), str)
            and isinstance(entry.get("baudrate"), int)
        ):
            connections[board_id] = {
                "port": entry["port"],
                "baudrate": entry["baudrate"],
            }
    return connections


def save_serial_connections(discovered: dict[str, SerialConnection]) -> None:
    path = cache_path()
    connections = load_serial_connections()
    connections.update(discovered)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps({"boards": connections}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    except OSError as error:
        raise RuntimeError(f"Could not write TRT board cache at {path}: {error}") from error
