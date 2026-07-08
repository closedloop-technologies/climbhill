#!/usr/bin/env python3
"""Run a bounded You.com Research API request."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import requests


API_URL = "https://api.you.com/v1/research"
FINANCE_API_URL = "https://api.you.com/v1/finance_research"


def api_key() -> str:
    key = os.getenv("YOU_API_KEY")
    if not key:
        raise SystemExit("YOU_API_KEY is not set.")
    return key


def api_url(api: str) -> str:
    if api == "finance":
        return FINANCE_API_URL
    return API_URL


def run_research(
    prompt: str,
    research_effort: str = "lite",
    timeout: int = 300,
    api: str = "general",
) -> Dict[str, Any]:
    response = requests.post(
        api_url(api),
        headers={
            "X-API-Key": api_key(),
            "Content-Type": "application/json",
        },
        json={
            "input": prompt,
            "research_effort": research_effort,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def source_lines(sources: List[Dict[str, Any]]) -> List[str]:
    lines = []
    for index, source in enumerate(sources, start=1):
        title = source.get("title") or source.get("url") or f"Source {index}"
        url = source.get("url", "")
        if url:
            lines.append(f"[{index}] [{title}]({url})")
    return lines


def render_markdown(payload: Dict[str, Any]) -> str:
    output = payload.get("output", payload)
    content = output.get("content") if isinstance(output, dict) else None
    sources = output.get("sources", []) if isinstance(output, dict) else []
    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2)
    content = content or json.dumps(payload, indent=2)

    sections = ["# You.com Research Result", "", str(content).strip()]
    source_section = source_lines(sources)
    if source_section:
        sections.extend(["", "# Citations", "", *source_section])
    return "\n".join(sections).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="Research prompt.")
    parser.add_argument(
        "--api",
        default="general",
        choices=["general", "finance"],
        help="Use general for open-web research or finance for You.com Finance Research.",
    )
    parser.add_argument(
        "--research-effort",
        default="lite",
        choices=["lite", "standard", "deep", "exhaustive", "frontier"],
        help="Use lite for under-$1 general benchmark smoke runs. Finance supports deep/exhaustive.",
    )
    parser.add_argument("--timeout", type=int, default=300, help="HTTP timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON instead of Markdown.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.api == "finance" and args.research_effort not in {"deep", "exhaustive"}:
        print("You.com Finance Research supports research_effort deep or exhaustive.", file=sys.stderr)
        raise SystemExit(2)
    try:
        payload = run_research(args.prompt, args.research_effort, args.timeout, args.api)
    except requests.HTTPError as exc:
        print(f"You.com Research request failed: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text[:1000], file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(f"You.com Research request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(payload))


if __name__ == "__main__":
    main()
