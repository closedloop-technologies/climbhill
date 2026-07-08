from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence
from urllib.parse import unquote

from .audit import REQUIRED_ENV_NAMES, REPO_ROOT


DEFAULT_ENV_FILE = REPO_ROOT / ".env.adr"
DEFAULT_TEMPLATE_FILE = REPO_ROOT / ".env.adr.example"
DEFAULT_OP_VAULT = "awesome-deep-researchers"
DEFAULT_OP_ITEM = "api-keys"
OP_REF_RE = re.compile(r"^op://[^\s/]+/[^\s/]+/[^\s/]+$")
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
MALFORMED_PERCENT_ENCODING_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
ENCODED_PATH_SEPARATOR_RE = re.compile(r"%2f|%5c", re.IGNORECASE)


@dataclass
class EnvCheckResult:
    name: str
    ok: bool
    detail: str


def has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def has_safe_op_reference_segments(value: str) -> bool:
    if not OP_REF_RE.match(value):
        return False
    for segment in value.removeprefix("op://").split("/"):
        if MALFORMED_PERCENT_ENCODING_RE.search(segment):
            return False
        decoded_segment = unquote(segment)
        if has_control_character(decoded_segment):
            return False
        if any(character.isspace() for character in decoded_segment):
            return False
        if "?" in segment or "#" in segment or "?" in decoded_segment or "#" in decoded_segment:
            return False
        if ENCODED_PATH_SEPARATOR_RE.search(segment):
            return False
        if decoded_segment != segment:
            return False
    return True


def iter_env_assignments(path: Path) -> Iterable[tuple[str, str]]:
    for raw_key, value in iter_raw_env_assignments(path):
        yield raw_key.strip(), value


def iter_raw_env_assignments(path: Path) -> Iterable[tuple[str, str]]:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = raw_line.split("=", 1)
        yield key, value.strip().strip('"').strip("'")


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in iter_env_assignments(path):
        values[key] = value
    return values


def check_env_file(path: Path, required_names: Iterable[str]) -> List[EnvCheckResult]:
    if not path.exists():
        return [EnvCheckResult("env file", False, f"{path} does not exist")]

    values = parse_env_file(path)
    counts: dict[str, int] = {}
    malformed: set[str] = set()
    for raw_key, _value in iter_raw_env_assignments(path):
        key = raw_key.strip()
        counts[key] = counts.get(key, 0) + 1
        if key != raw_key or not ENV_NAME_RE.match(key):
            malformed.add(key)

    results = []
    required_names = sorted(required_names)
    for name in required_names:
        value = values.get(name, "")
        if counts.get(name, 0) > 1:
            results.append(EnvCheckResult(name, False, "duplicate assignment"))
        elif name in malformed:
            results.append(EnvCheckResult(name, False, "malformed assignment"))
        elif not value:
            results.append(EnvCheckResult(name, False, "missing"))
        elif not has_safe_op_reference_segments(value):
            results.append(EnvCheckResult(name, False, "not an op:// reference"))
        else:
            results.append(EnvCheckResult(name, True, "op reference present"))
    for name in sorted(malformed - set(required_names)):
        results.append(EnvCheckResult(name or "<blank>", False, "malformed assignment"))
    op_reference_counts = Counter(
        values.get(name, "")
        for name in required_names
        if has_safe_op_reference_segments(values.get(name, ""))
    )
    duplicate_references = sorted(
        reference for reference, count in op_reference_counts.items() if count > 1
    )
    if duplicate_references:
        results.append(
            EnvCheckResult(
                "op references",
                False,
                "duplicate references: " + ", ".join(duplicate_references),
            )
        )
    return results


def check_live_environment(required_names: Iterable[str]) -> List[EnvCheckResult]:
    results = []
    for name in sorted(required_names):
        value = os.getenv(name)
        if value:
            results.append(EnvCheckResult(name, True, f"set ({len(value)} chars)"))
        else:
            results.append(EnvCheckResult(name, False, "not set"))
    return results


def check_op_item_scaffold(
    required_names: Iterable[str],
    *,
    vault: str = DEFAULT_OP_VAULT,
    item: str = DEFAULT_OP_ITEM,
) -> List[EnvCheckResult]:
    command = ["op", "item", "get", item, "--vault", vault, "--format", "json"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        return [EnvCheckResult("op item", False, f"unable to run op: {exc}")]

    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "op item get failed"
        return [EnvCheckResult("op item", False, detail)]

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return [EnvCheckResult("op item", False, f"invalid JSON from op: {exc}")]

    fields = payload.get("fields", [])
    label_counts = Counter(
        field.get("label") for field in fields if isinstance(field, dict)
    )
    labels = set(label_counts)
    results = [
        EnvCheckResult("op vault", payload.get("vault", {}).get("name") == vault, vault),
        EnvCheckResult("op item", payload.get("title") == item, item),
    ]
    for name in sorted(required_names):
        if label_counts.get(name, 0) > 1:
            results.append(EnvCheckResult(name, False, "duplicate field"))
            continue
        results.append(
            EnvCheckResult(
                name,
                name in labels,
                "field present" if name in labels else "missing field",
            )
        )
    return results


def names_for_scope(scope: Optional[str]) -> Sequence[str]:
    if not scope:
        return sorted(REQUIRED_ENV_NAMES)

    groups = {
        "core": ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "EXA_API_KEY", "TAVILY_API_KEY"],
        "commercial": [
            "OPENAI_API_KEY",
            "PERPLEXITY_API_KEY",
            "EXA_API_KEY",
            "TAVILY_API_KEY",
            "JINA_API_KEY",
            "XAI_API_KEY",
            "YOU_API_KEY",
            "GOOGLE_API_KEY",
            "GOOGLE_CLOUD_PROJECT",
        ],
        "oss": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "TAVILY_API_KEY", "HF_TOKEN", "BING_SEARCH_API_KEY", "YDC_API_KEY"],
    }
    if scope not in groups:
        raise ValueError(f"Unknown scope '{scope}'. Expected one of: {', '.join(sorted(groups))}")
    return groups[scope]


def format_results(results: Iterable[EnvCheckResult]) -> str:
    lines = []
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        lines.append(f"{status}\t{result.name}\t{result.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check 1Password-backed benchmark environment references.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Dotenv file with op:// references. Defaults to .env.adr.",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Check .env.adr.example instead of .env.adr.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Check currently resolved environment variables. Run through op run.",
    )
    parser.add_argument(
        "--op-scaffold",
        action="store_true",
        help="Check that the configured 1Password vault/item has the required field labels.",
    )
    parser.add_argument("--vault", default=DEFAULT_OP_VAULT, help="1Password vault name.")
    parser.add_argument("--item", default=DEFAULT_OP_ITEM, help="1Password item title.")
    parser.add_argument(
        "--scope",
        choices=["core", "commercial", "oss"],
        help="Limit checks to a provider group.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    required_names = names_for_scope(args.scope)

    if args.live:
        results = check_live_environment(required_names)
    elif args.op_scaffold:
        results = check_op_item_scaffold(required_names, vault=args.vault, item=args.item)
    else:
        env_file = DEFAULT_TEMPLATE_FILE if args.template else args.env_file
        results = check_env_file(env_file, required_names)

    print(format_results(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
