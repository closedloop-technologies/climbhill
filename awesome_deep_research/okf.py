from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


LINK_OR_URL_RE = re.compile(r"\[[^\]]+\]\([^)]+\)|https?://\S+")
UNCERTAINTY_RE = re.compile(
    r"\b(uncertain|unclear|unknown|conflict|conflicting|caveat|limitation|"
    r"assumption|estimate|may|might|could|not verified|stale|missing citation)\b",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def frontmatter(kind: str, title: str, description: str, tags: Iterable[str]) -> str:
    tag_list = ", ".join(tags)
    return (
        "---\n"
        f'type: "{yaml_escape(kind)}"\n'
        f'title: "{yaml_escape(title)}"\n'
        f'description: "{yaml_escape(description)}"\n'
        f"tags: [{tag_list}]\n"
        f'timestamp: "{utc_now()}"\n'
        "---\n\n"
    )


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
    return [line for line in significant_lines(text) if not UNCERTAINTY_RE.search(line)][:40]


def extract_uncertainties(text: str) -> List[str]:
    return [line for line in significant_lines(text) if UNCERTAINTY_RE.search(line)][:40]


def bullet_lines(lines: List[str], fallback: str) -> str:
    if not lines:
        return f"- {fallback}\n"
    return "\n".join(f"- {line.lstrip('-* ')}" for line in lines) + "\n"


def write_concept(path: Path, kind: str, title: str, description: str, tags: List[str], body: str) -> None:
    path.write_text(frontmatter(kind, title, description, tags) + body.strip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_provider_okf_bundle(
    bundle_dir: Path,
    *,
    question: str,
    provider_id: str,
    report_text: str,
    metadata: Mapping[str, Any],
    raw_output_path: Path,
) -> Path:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    title = f"{provider_id} research for {question}"
    relative_raw_path = raw_output_path.as_posix()

    write_concept(
        bundle_dir / "report.md",
        "Research Report",
        title,
        "Raw or lightly normalized provider research output.",
        ["deep-research", "raw-output"],
        "# Report\n\n" + report_text,
    )
    write_concept(
        bundle_dir / "findings.md",
        "Research Findings",
        f"Findings from {provider_id}",
        "Claim-like lines extracted from the provider output.",
        ["deep-research", "findings"],
        "# Findings\n\n" + bullet_lines(extract_findings(report_text), "No explicit findings extracted."),
    )
    write_concept(
        bundle_dir / "uncertainties.md",
        "Uncertainty Register",
        f"Uncertainties from {provider_id}",
        "Caveats, conflicts, assumptions, and verification gaps.",
        ["deep-research", "uncertainty"],
        "# Uncertainties\n\n"
        + bullet_lines(extract_uncertainties(report_text), "No explicit uncertainties extracted."),
    )
    write_concept(
        bundle_dir / "method.md",
        "Research Method",
        f"Method for {provider_id}",
        "Prompt, provider, raw evidence, and metadata.",
        ["deep-research", "method"],
        (
            "# Method\n\n"
            f"- Provider: `{provider_id}`\n"
            f"- Prompt: {question}\n"
            f"- Raw Provider Output: `{relative_raw_path}`\n"
            "- Normalizer: `awesome_deep_research.okf.write_provider_okf_bundle`\n\n"
            "## Provider-Specific Metadata\n\n"
            "```json\n"
            + json.dumps(metadata, indent=2, sort_keys=True)
            + "\n```\n"
        ),
    )
    (bundle_dir / "index.md").write_text(
        "# Provider OKF Bundle\n\n"
        f"* Provider: `{provider_id}`\n"
        f"* Question: {question}\n"
        f"* Raw Provider Output: `{relative_raw_path}`\n"
        "* [Report](report.md)\n"
        "* [Findings](findings.md)\n"
        "* [Uncertainties](uncertainties.md)\n"
        "* [Method](method.md)\n",
        encoding="utf-8",
    )
    (bundle_dir / "log.md").write_text(
        "# Bundle Update Log\n\n"
        f"## {datetime.now(timezone.utc).date().isoformat()}\n"
        "* **Creation**: Normalized Raw Provider Output into a Provider OKF Bundle.\n",
        encoding="utf-8",
    )
    return bundle_dir


def write_aggregate_okf_bundle(
    bundle_dir: Path,
    *,
    question: str,
    provider_results: Iterable[Mapping[str, Any]],
) -> Path:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    successful = [result for result in provider_results if result.get("status") == "succeeded"]
    failed = [result for result in provider_results if result.get("status") != "succeeded"]

    report_lines = ["# Aggregate Report", "", f"Question: {question}", ""]
    finding_lines: List[str] = []
    uncertainty_lines: List[str] = []
    method_lines = ["# Method", "", f"- Prompt: {question}", "- Aggregation: mechanical", ""]

    for result in successful:
        provider_id = str(result["provider_id"])
        okf_path = result.get("okf_bundle_path")
        raw_path = result.get("raw_output_path")
        report_lines.extend(
            [
                f"## {provider_id}",
                "",
                f"- Provider OKF Bundle: `{okf_path}`",
                f"- Raw Provider Output: `{raw_path}`",
                "",
            ]
        )
        finding_lines.append(f"- `{provider_id}` succeeded. See `{okf_path}`.")
        method_lines.append(f"- `{provider_id}`: succeeded; OKF `{okf_path}`; raw `{raw_path}`")

    for result in failed:
        provider_id = str(result["provider_id"])
        error = result.get("error") or result.get("status")
        uncertainty_lines.append(f"- `{provider_id}` did not produce usable OKF output: {error}")
        method_lines.append(f"- `{provider_id}`: {result.get('status')}; {error}")

    write_concept(
        bundle_dir / "report.md",
        "Research Report",
        f"Aggregate research for {question}",
        "Mechanical aggregate of successful provider OKF bundles.",
        ["deep-research", "aggregate"],
        "\n".join(report_lines),
    )
    write_concept(
        bundle_dir / "findings.md",
        "Research Findings",
        f"Aggregate findings for {question}",
        "Pointers to successful provider findings.",
        ["deep-research", "findings"],
        "# Findings\n\n" + bullet_lines(finding_lines, "No provider succeeded."),
    )
    write_concept(
        bundle_dir / "uncertainties.md",
        "Uncertainty Register",
        f"Aggregate uncertainties for {question}",
        "Provider failures and verification gaps.",
        ["deep-research", "uncertainty"],
        "# Uncertainties\n\n" + bullet_lines(uncertainty_lines, "No provider failures recorded."),
    )
    write_concept(
        bundle_dir / "method.md",
        "Research Method",
        f"Aggregate method for {question}",
        "Mechanical aggregation metadata.",
        ["deep-research", "method"],
        "\n".join(method_lines),
    )
    (bundle_dir / "index.md").write_text(
        "# Aggregate OKF Bundle\n\n"
        f"* Question: {question}\n"
        "* [Report](report.md)\n"
        "* [Findings](findings.md)\n"
        "* [Uncertainties](uncertainties.md)\n"
        "* [Method](method.md)\n",
        encoding="utf-8",
    )
    (bundle_dir / "log.md").write_text(
        "# Bundle Update Log\n\n"
        f"## {datetime.now(timezone.utc).date().isoformat()}\n"
        "* **Creation**: Mechanically aggregated successful Provider OKF Bundles.\n",
        encoding="utf-8",
    )
    return bundle_dir
