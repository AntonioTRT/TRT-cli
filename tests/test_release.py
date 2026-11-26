"""Release consistency: version metadata, changelog, and the workflow shown by every help level."""

from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

import trt
from trt.cli import app
from trt.commands.quickstart import WORKFLOW
from trt.version import __version__, get_version_info

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner(env={"COLUMNS": "120"})


def test_version_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == __version__ == trt.__version__
    assert ".".join(str(part) for part in get_version_info()) == __version__
    assert __version__ in runner.invoke(app, ["version"]).output


def test_changelog_has_an_entry_for_this_version() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## {__version__}" in changelog


def test_workflow_is_identical_on_every_help_level() -> None:
    assert WORKFLOW == "discover -> boards -> info -> hwid -> update -> MATCH -> listen"
    for args in ([], ["--help"], ["help"]):
        output = " ".join(runner.invoke(app, args).output.split())
        assert WORKFLOW in output, args


def test_readme_and_reference_show_the_workflow() -> None:
    for doc in ("README.md", "docs/cli-reference.md"):
        text = (ROOT / doc).read_text(encoding="utf-8")
        for command in ("trt discover", "trt boards", "trt board info", "trt board hwid", "trt board update", "trt listen"):
            assert command in text, (doc, command)
