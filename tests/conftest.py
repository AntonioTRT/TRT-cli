"""Shared test configuration.

* Tests never touch the real ``~/.trt/boards.json``: the board cache is redirected to a temporary
  file for every test (``TRT_CLI_BOARD_CACHE``).
* Tests marked ``hardware`` need a real TRT board (Arduino Uno on COM4). They are skipped unless
  ``TRT_HARDWARE_TESTS=1`` is set; they then use the real cache as before.
"""

from __future__ import annotations

import os

import pytest

HARDWARE_ENABLED = os.environ.get("TRT_HARDWARE_TESTS") == "1"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if HARDWARE_ENABLED:
        return
    skip = pytest.mark.skip(reason="needs a real TRT board; set TRT_HARDWARE_TESTS=1 to run")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def isolated_board_cache(request: pytest.FixtureRequest, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    if "hardware" in request.keywords and HARDWARE_ENABLED:
        return
    monkeypatch.setenv("TRT_CLI_BOARD_CACHE", str(tmp_path / "boards.json"))
