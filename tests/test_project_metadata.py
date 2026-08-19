from __future__ import annotations

import re
from pathlib import Path

import yaml

import climbhill

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 CI path
    import tomli as tomllib


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


def test_ci_workflow_runs_release_gates() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    triggers = workflow.get("on", workflow.get(True))

    assert "pull_request" in triggers
    assert triggers["push"]["branches"] == ["main"]

    test_job = workflow["jobs"]["test"]
    assert test_job["strategy"]["matrix"]["python-version"] == [
        "3.10",
        "3.11",
        "3.12",
        "3.13",
    ]
    commands = [
        step.get("run", "")
        for step in test_job["steps"]
        if "run" in step
    ]
    assert "pytest" in commands
    assert "python -m build" in commands
    assert "python -m twine check dist/*" in commands
    assert "python .github/scripts/validate_plugin.py ." in commands
    assert "python .github/scripts/validate_plugin.py plugin/climbhill-ai" in commands
    assert any("climbhill --help" in command for command in commands)


def test_pages_workflow_can_enable_pages() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "pages.yml").read_text())
    build_steps = workflow["jobs"]["build"]["steps"]

    configure_pages = next(
        step for step in build_steps if step.get("uses") == "actions/configure-pages@v5"
    )
    assert configure_pages["with"]["enablement"] is True

    build_site = next(step for step in build_steps if step.get("name") == "Build Remix site")
    assert build_site["run"] == "npm run www:build"

    upload = next(
        step for step in build_steps if step.get("uses") == "actions/upload-pages-artifact@v4"
    )
    assert upload["with"]["path"] == "www/dist"
