#!/usr/bin/env python3
"""Normalize a deep research report into a small OKF-style markdown bundle."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List


LINK_OR_URL_RE = re.compile(r"\[[^\]]+\]\([^)]+\)|https?://\S+")
UNCERTAINTY_RE = re.compile(
    r"\b(uncertain|unclear|unknown|conflict|conflicting|caveat|limitation|"
    r"assumption|estimate|may|might|could|not verified|stale)\b",
    re.IGNORECASE,
)


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def frontmatter(kind: str, title: str, description: str, tags: Iterable[str]) -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    tag_list = ", ".join(tags)
    return (
        "---\n"
        f'type: "{yaml_escape(kind)}"\n'
        f'title: "{yaml_escape(title)}"\n'
        f'description: "{yaml_escape(description)}"\n'
        f"tags: [{tag_list}]\n"
        f'timestamp: "{timestamp}"\n'
        "---\n\n"
    )


def read_report(args: argparse.Namespace) -> str:
    if args.input:
        return Path(args.input).read_text(encoding="utf-8")
    if args.text:
        return args.text
    raise SystemExit("Provide --input or --text.")


def significant_lines(text: str) -> List[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("```", "---")):
            continue
        if line.startswith(("#", "-", "*", "1.", "2.", "3.")) or LINK_OR_URL_RE.search(line):
            lines.append(line)
    return lines


def extract_findings(text: str) -> List[str]:
    findings = []
    for line in significant_lines(text):
        if UNCERTAINTY_RE.search(line):
            continue
        findings.append(line)
    return findings[:40]


def extract_uncertainties(text: str) -> List[str]:
    uncertainties = [line for line in significant_lines(text) if UNCERTAINTY_RE.search(line)]
    return uncertainties[:40]


def write_concept(path: Path, kind: str, title: str, description: str, tags: List[str], body: str) -> None:
    path.write_text(frontmatter(kind, title, description, tags) + body.strip() + "\n", encoding="utf-8")


def bullet_lines(lines: List[str], fallback: str) -> str:
    if not lines:
        return f"- {fallback}\n"
    return "\n".join(f"- {line.lstrip('-* ')}" for line in lines) + "\n"


def normalize(args: argparse.Namespace) -> Path:
    report = read_report(args).strip()
    if not report:
        raise SystemExit("Input report is empty.")

    bundle_dir = Path(args.bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or "Deep research report"
    provider = args.provider or "unknown"
    prompt = args.prompt or title

    write_concept(
        bundle_dir / "report.md",
        "Research Report",
        title,
        "Raw or lightly normalized deep research output.",
        ["deep-research", "raw-output"],
        "# Report\n\n" + report,
    )
    write_concept(
        bundle_dir / "findings.md",
        "Research Findings",
        f"Findings for {title}",
        "Claim-like lines extracted from the research output.",
        ["deep-research", "findings"],
        "# Findings\n\n" + bullet_lines(extract_findings(report), "No explicit findings extracted."),
    )
    write_concept(
        bundle_dir / "uncertainties.md",
        "Uncertainty Register",
        f"Uncertainties for {title}",
        "Caveats, conflicts, assumptions, and verification gaps.",
        ["deep-research", "uncertainty"],
        "# Uncertainties\n\n"
        + bullet_lines(extract_uncertainties(report), "No explicit uncertainties extracted."),
    )
    write_concept(
        bundle_dir / "method.md",
        "Research Method",
        f"Method for {title}",
        "Prompt, provider, and normalization metadata.",
        ["deep-research", "method"],
        (
            "# Method\n\n"
            f"- Provider: `{provider}`\n"
            f"- Prompt: {prompt}\n"
            "- Normalizer: `deep-research-okf-normalize`\n"
            "- Notes: This bundle preserves unknown OKF frontmatter fields and keeps source claims traceable.\n"
        ),
    )

    (bundle_dir / "index.md").write_text(
        "# Deep Research OKF Bundle\n\n"
        f"* [Report](report.md) - Raw or lightly normalized output for {title}.\n"
        "* [Findings](findings.md) - Extracted claim-like lines.\n"
        "* [Uncertainties](uncertainties.md) - Caveats and verification gaps.\n"
        "* [Method](method.md) - Provider and prompt metadata.\n",
        encoding="utf-8",
    )
    (bundle_dir / "log.md").write_text(
        "# Bundle Update Log\n\n"
        f"## {datetime.now(timezone.utc).date().isoformat()}\n"
        "* **Creation**: Normalized deep research output into an OKF-style bundle.\n",
        encoding="utf-8",
    )
    return bundle_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to a raw research report.")
    parser.add_argument("--text", help="Raw report text.")
    parser.add_argument("--bundle-dir", required=True, help="Output OKF bundle directory.")
    parser.add_argument("--title", help="Display title for the report concept.")
    parser.add_argument("--provider", help="Provider or skill that produced the report.")
    parser.add_argument("--prompt", help="Original research prompt.")
    return parser


def main() -> None:
    bundle_dir = normalize(build_parser().parse_args())
    print(bundle_dir)


if __name__ == "__main__":
    main()
