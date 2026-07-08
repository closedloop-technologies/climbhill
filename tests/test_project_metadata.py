from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

import climbhill


ROOT = Path(__file__).resolve().parents[1]


def test_package_version_matches_project_metadata() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    pyproject_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)

    assert pyproject_version is not None
    assert climbhill.__version__ == pyproject_version.group(1)


def test_climbhill_console_script_is_primary_entry_point() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["climbhill"] == "climbhill.cli:main"


def test_pypi_publish_workflow_uses_trusted_publishing() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "publish.yml").read_text())

    publish = workflow["jobs"]["publish"]
    assert publish["environment"]["name"] == "pypi"
    assert publish["permissions"]["id-token"] == "write"
    assert publish["permissions"]["contents"] == "read"

    step_uses = [step.get("uses", "") for step in publish["steps"]]
    assert "pypa/gh-action-pypi-publish@release/v1" in step_uses

    build_commands = [
        step.get("run", "")
        for step in workflow["jobs"]["build"]["steps"]
        if "run" in step
    ]
    assert "python -m build" in build_commands
    assert "python -m twine check dist/*" in build_commands
