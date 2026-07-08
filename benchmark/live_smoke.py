#!/usr/bin/env python3
"""Run under-$1 live smoke benchmarks for providers with configured keys."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.benchmark import BenchmarkRunner
from benchmark.utils import discover_skills


DEFAULT_LIVE_SKILLS = [
    "deep-research-you",
    "deep-research-gemini",
    "deep-research-tavily",
    "deep-research-jina",
]

REQUIRED_ENV_BY_SKILL: Dict[str, Sequence[str]] = {
    "deep-research-you": ["YOU_API_KEY"],
    "deep-research-gemini": ["GOOGLE_API_KEY"],
    "deep-research-tavily": ["TAVILY_API_KEY"],
    "deep-research-jina": ["JINA_API_KEY"],
    "deep-research-perplexity": ["PERPLEXITY_API_KEY"],
    "deep-research-exa": ["EXA_API_KEY"],
    "deep-research-openai": ["OPENAI_API_KEY"],
    "deep-research-xai-grok": ["XAI_API_KEY"],
    "deep-research-gpt-researcher": ["OPENAI_API_KEY", "TAVILY_API_KEY"],
    "deep-research-smolagents": ["OPENAI_API_KEY"],
    "deep-research-stanford-storm": ["OPENAI_API_KEY", "YDC_API_KEY"],
}


def missing_env_for_skill(skill_name: str) -> List[str]:
    return [name for name in REQUIRED_ENV_BY_SKILL.get(skill_name, []) if not os.getenv(name)]


def select_ready_skills(
    requested_skills: Iterable[str],
    available_skills: Iterable[str],
    fail_missing_env: bool = False,
) -> Tuple[List[str], List[str]]:
    available = set(available_skills)
    selected: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    for skill_name in requested_skills:
        if skill_name not in available:
            skipped.append(f"{skill_name}: not discovered")
            continue
        missing = missing_env_for_skill(skill_name)
        if missing:
            message = f"{skill_name}: missing {', '.join(missing)}"
            if fail_missing_env:
                errors.append(message)
            else:
                skipped.append(message)
            continue
        selected.append(skill_name)

    if errors:
        raise RuntimeError("; ".join(errors))
    return selected, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills",
        nargs="+",
        default=DEFAULT_LIVE_SKILLS,
        help="Skills to live-smoke. Defaults to low-cost provider/retrieval set.",
    )
    parser.add_argument(
        "--category",
        default="Repository Refresh & Meta Research",
        help="Benchmark category to run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark/results/live-smoke"),
        help="Output directory for live smoke results.",
    )
    parser.add_argument(
        "--fail-missing-env",
        action="store_true",
        help="Fail if any requested skill is missing required environment variables.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose benchmark output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    discovered = {skill["name"] for skill in discover_skills()}
    try:
        selected, skipped = select_ready_skills(args.skills, discovered, args.fail_missing_env)
    except RuntimeError as exc:
        print(f"Live smoke preflight failed: {exc}", file=sys.stderr)
        return 1

    for message in skipped:
        print(f"SKIP\t{message}", file=sys.stderr)

    if not selected:
        print("No live smoke skills are ready. Run through op run with .env.adr.", file=sys.stderr)
        return 1

    runner = BenchmarkRunner(output_dir=args.output_dir, verbose=args.verbose)
    runner.run_benchmark(skills=selected, categories=[args.category], max_questions=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
