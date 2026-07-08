from __future__ import annotations

import re
from pathlib import Path

import awesome_deep_research


ROOT = Path(__file__).resolve().parents[1]


def test_package_version_matches_project_metadata() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    setup_py = (ROOT / "setup.py").read_text(encoding="utf-8")

    pyproject_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    setup_version = re.search(r'version="([^"]+)"', setup_py)

    assert pyproject_version is not None
    assert setup_version is not None
    assert awesome_deep_research.__version__ == pyproject_version.group(1)
    assert awesome_deep_research.__version__ == setup_version.group(1)
