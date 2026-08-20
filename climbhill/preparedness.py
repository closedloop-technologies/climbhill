from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .policy import DEFAULT_POLICY, dump_policy


PREPAREDNESS_PATHS = [
    "goal.md",
    "AGENTS.md",
    "README.md",
    "ARCHITECTURE.md",
    "TESTING.md",
    "EVALS.md",
    ".climbhill/policy.yaml",
    ".climbhill/eval.yaml",
    ".agent/skills",
    "resources/README.md",
    ".github/pull_request_template.md",
]


DEFAULT_EVAL = {
    "version": 1,
    "commands": [
        {"id": "tests", "kind": "test", "command": "pytest", "required": True},
        {"id": "diff-check", "kind": "static", "command": "git diff --check", "required": True},
    ],
    "rubrics": [
        {
            "id": "policy-safety",
            "description": "Attempt avoids denied paths and records approval requirements.",
        },
        {
            "id": "report-quality",
            "description": "Attempt report explains goal, changes, tests, risks, costs, and next actions.",
        },
    ],
}


TEMPLATE_FILES: Dict[str, str] = {
    "goal.md": "# Repository Goal\n\nDescribe what this repository is trying to improve.\n",
    "AGENTS.md": "# Agent Instructions\n\nDescribe how coding agents should operate in this repository.\n",
    "README.md": "# Project\n\nDescribe setup, usage, and development workflows.\n",
    "ARCHITECTURE.md": "# Architecture\n\nDescribe important modules, ownership boundaries, and design constraints.\n",
    "TESTING.md": "# Testing\n\nRecord install, lint, typecheck, test, and build commands.\n",
    "EVALS.md": "# Evaluation Strategy\n\nDescribe how attempts should be evaluated before promotion.\n",
    "resources/README.md": "# Resources\n\nStore reusable context, prior art, postmortems, and promoted experiment learnings here.\n",
    ".github/pull_request_template.md": (
        "## Attempt Summary\n\n"
        "## Test Results\n\n"
        "## Policy Status\n\n"
        "## Risk Notes\n\n"
        "## Human Review Checklist\n\n"
        "- [ ] Protected surfaces reviewed\n"
        "- [ ] Tests and evals reviewed\n"
        "- [ ] Costs and lineage recorded\n"
    ),
}


@dataclass(frozen=True)
class PreparednessReport:
    repo_path: Path
    present: List[str]
    missing: List[str]
    git_remote: str
    current_commit: str

    @property
    def is_prepared(self) -> bool:
        return not self.missing


def _git_output(repo_path: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def inspect_preparedness(repo_path: Path) -> PreparednessReport:
    repo_path = repo_path.resolve()
    present: List[str] = []
    missing: List[str] = []
    for relative in PREPAREDNESS_PATHS:
        target = repo_path / relative
        if target.exists():
            present.append(relative)
        else:
            missing.append(relative)
    return PreparednessReport(
        repo_path=repo_path,
        present=present,
        missing=missing,
        git_remote=_git_output(repo_path, "config", "--get", "remote.origin.url"),
        current_commit=_git_output(repo_path, "rev-parse", "HEAD"),
    )


def initialize_repo(repo_path: Path, *, force: bool = False) -> List[Path]:
    repo_path = repo_path.resolve()
    created: List[Path] = []

    for relative, content in TEMPLATE_FILES.items():
        target = repo_path / relative
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        created.append(target)

    for directory in [
        ".climbhill",
        ".agent/skills",
        "resources",
        "resources/research",
        "resources/prior-art",
        "resources/benchmarks",
        "resources/case-studies",
        "resources/user-guidance",
        "resources/postmortems",
    ]:
        target = repo_path / directory
        target.mkdir(parents=True, exist_ok=True)
        if target not in created:
            created.append(target)

    policy_path = repo_path / ".climbhill" / "policy.yaml"
    if force or not policy_path.exists():
        policy_path.write_text(dump_policy(DEFAULT_POLICY), encoding="utf-8")
        created.append(policy_path)

    eval_path = repo_path / ".climbhill" / "eval.yaml"
    if force or not eval_path.exists():
        eval_path.write_text(dump_policy(DEFAULT_EVAL), encoding="utf-8")
        created.append(eval_path)

    reports_path = repo_path / ".climbhill" / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)

    return created
