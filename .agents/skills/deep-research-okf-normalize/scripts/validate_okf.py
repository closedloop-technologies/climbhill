#!/usr/bin/env python3
"""Validate the repository's OKF-style deep research bundles."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List


REQUIRED_FILES = {"index.md", "report.md", "findings.md", "uncertainties.md", "method.md", "log.md"}
RESERVED_FILES = {"index.md", "log.md"}
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
TYPE_RE = re.compile(r"^type\s*:\s*(?P<value>.+?)\s*$", re.MULTILINE)


def concept_files(bundle_dir: Path) -> Iterable[Path]:
    for path in sorted(bundle_dir.rglob("*.md")):
        if path.name not in RESERVED_FILES:
            yield path


def parse_frontmatter(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter block")
    type_match = TYPE_RE.search(match.group("body"))
    if not type_match or not type_match.group("value").strip().strip('"').strip("'"):
        raise ValueError(f"{path}: frontmatter missing non-empty type")
    return {"type": type_match.group("value").strip().strip('"').strip("'")}


def validate_bundle(bundle_dir: Path) -> List[str]:
    errors: List[str] = []
    if not bundle_dir.exists():
        return [f"{bundle_dir}: bundle directory does not exist"]
    if not bundle_dir.is_dir():
        return [f"{bundle_dir}: bundle path is not a directory"]

    present = {path.name for path in bundle_dir.glob("*.md")}
    for required in sorted(REQUIRED_FILES - present):
        errors.append(f"{bundle_dir}: missing required file {required}")

    for path in sorted(bundle_dir.rglob("*.md")):
        if path.is_symlink():
            errors.append(f"{path}: markdown file must not be a symlink")

    for path in concept_files(bundle_dir):
        try:
            parse_frontmatter(path)
        except ValueError as exc:
            errors.append(str(exc))

    for reserved in RESERVED_FILES & present:
        text = (bundle_dir / reserved).read_text(encoding="utf-8").strip()
        if not text:
            errors.append(f"{bundle_dir / reserved}: reserved file is empty")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path, help="OKF bundle directory to validate.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    errors = validate_bundle(args.bundle_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print(f"OKF bundle valid: {args.bundle_dir}")


if __name__ == "__main__":
    main()
