from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal installs
    yaml = None


DEFAULT_POLICY: Dict[str, Any] = {
    "version": 1,
    "repo": {
        "name": "target-repo",
        "default_branch": "main",
    },
    "edit_policy": {
        "allow": [
            "src/**",
            "docs/**",
            "examples/**",
            "README.md",
            "goal.md",
            "AGENTS.md",
            "TESTING.md",
            "EVALS.md",
            "resources/**",
            ".agent/skills/**",
            ".climbhill/**",
        ],
        "deny": [
            ".env",
            ".env.*",
            "**/*.snap",
            "package-lock.json",
            "pnpm-lock.yaml",
        ],
        "require_human_approval": [
            "tests/**",
            ".github/workflows/**",
            "migrations/**",
            "security/**",
            "infra/**",
        ],
    },
    "commands": {
        "test": "pytest",
    },
    "budgets": {
        "max_parallel_candidates": 5,
        "max_usd_per_run": 20,
        "max_minutes_per_candidate": 45,
    },
    "promotion": {
        "require_tests_pass": True,
        "require_policy_pass": True,
        "require_human_approval": True,
        "create_pr_by_default": True,
    },
}


@dataclass(frozen=True)
class PathPolicyResult:
    path: str
    classification: str
    matched_pattern: str


def _normalize_path(path: str | Path) -> str:
    normalized = Path(path).as_posix()
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _patterns(policy: Dict[str, Any], section: str) -> List[str]:
    values = policy.get("edit_policy", {}).get(section, [])
    return [str(value) for value in values]


def _matches(path: str, pattern: str) -> bool:
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return False


def classify_path(path: str | Path, policy: Dict[str, Any]) -> PathPolicyResult:
    normalized = _normalize_path(path)

    for pattern in _patterns(policy, "deny"):
        if _matches(normalized, pattern):
            return PathPolicyResult(normalized, "denied", pattern)

    for pattern in _patterns(policy, "require_human_approval"):
        if _matches(normalized, pattern):
            return PathPolicyResult(normalized, "requires_approval", pattern)

    for pattern in _patterns(policy, "allow"):
        if _matches(normalized, pattern):
            return PathPolicyResult(normalized, "allowed", pattern)

    return PathPolicyResult(normalized, "unspecified", "")


def check_paths(paths: Iterable[str | Path], policy: Dict[str, Any]) -> List[PathPolicyResult]:
    return [classify_path(path, policy) for path in paths]


def paths_from_patch(patch_text: str) -> List[str]:
    paths: List[str] = []
    for line in patch_text.splitlines():
        path = ""
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            path = line[6:]
        elif line.startswith("diff --git a/"):
            parts = line.split()
            if len(parts) >= 4 and parts[3].startswith("b/"):
                path = parts[3][2:]
        if path and path != "/dev/null" and path not in paths:
            paths.append(path)
    return paths


def policy_allows_promotion(results: Iterable[PathPolicyResult]) -> bool:
    return all(result.classification == "allowed" for result in results)


def load_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return DEFAULT_POLICY
    if yaml is None:
        raise RuntimeError("PyYAML is required to read ClimbHill policy files.")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Policy file must contain a mapping: {path}")
    return loaded


def dump_policy(policy: Dict[str, Any]) -> str:
    if yaml is None:
        raise RuntimeError("PyYAML is required to write ClimbHill policy files.")
    return yaml.safe_dump(policy, sort_keys=False)
