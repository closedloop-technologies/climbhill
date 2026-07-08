#!/usr/bin/env python3
"""Run Gemini grounded research or start a Gemini Deep Research interaction."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List

import requests


INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"


def api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GOOGLE_API_KEY or GEMINI_API_KEY is not set.")
    return key


def create_interaction(payload: Dict[str, Any], timeout: int = 300) -> Dict[str, Any]:
    response = requests.post(
        INTERACTIONS_URL,
        headers={
            "x-goog-api-key": api_key(),
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def grounded_research(prompt: str, model: str, timeout: int = 300) -> Dict[str, Any]:
    return create_interaction(
        {
            "model": model,
            "input": prompt,
            "tools": [{"type": "google_search"}],
        },
        timeout=timeout,
    )


def start_deep_research(prompt: str, agent: str, timeout: int = 300) -> Dict[str, Any]:
    return create_interaction(
        {
            "agent": agent,
            "input": prompt,
            "background": True,
            "agent_config": {
                "type": "deep-research",
                "thinking_summaries": "none",
                "visualization": "off",
                "collaborative_planning": False,
            },
        },
        timeout=timeout,
    )


def iter_text_blocks(payload: Any) -> Iterable[str]:
    if isinstance(payload, dict):
        for key in ["output_text", "text"]:
            value = payload.get(key)
            if isinstance(value, str):
                yield value
        for value in payload.values():
            yield from iter_text_blocks(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from iter_text_blocks(item)


def iter_citations(payload: Any) -> Iterable[Dict[str, str]]:
    if isinstance(payload, dict):
        if payload.get("type") == "url_citation" and payload.get("url"):
            yield {
                "title": payload.get("title") or payload["url"],
                "url": payload["url"],
            }
        for value in payload.values():
            yield from iter_citations(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from iter_citations(item)


def render_markdown(payload: Dict[str, Any], mode: str) -> str:
    text_blocks = [text.strip() for text in iter_text_blocks(payload) if text.strip()]
    content = "\n\n".join(dict.fromkeys(text_blocks))
    if not content:
        content = json.dumps(payload, indent=2)

    sections = [f"# Gemini {mode} Result", "", content]
    citations = list({citation["url"]: citation for citation in iter_citations(payload)}.values())
    if citations:
        sections.extend(["", "# Citations", ""])
        for index, citation in enumerate(citations, start=1):
            sections.append(f"[{index}] [{citation['title']}]({citation['url']})")
    return "\n".join(sections).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="Research prompt.")
    parser.add_argument(
        "--mode",
        default="grounded",
        choices=["grounded", "deep-research-start"],
        help="Use grounded for under-$1 benchmark runs; deep-research-start only starts a background agent task.",
    )
    parser.add_argument("--model", default="gemini-3.5-flash", help="Grounded Interactions API model.")
    parser.add_argument("--agent", default="deep-research-preview-04-2026", help="Gemini Deep Research agent.")
    parser.add_argument("--timeout", type=int, default=300, help="HTTP timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON instead of Markdown.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.mode == "grounded":
            payload = grounded_research(args.prompt, args.model, args.timeout)
        else:
            payload = start_deep_research(args.prompt, args.agent, args.timeout)
    except requests.HTTPError as exc:
        print(f"Gemini request failed: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text[:1000], file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(f"Gemini request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(payload, args.mode))


if __name__ == "__main__":
    main()
