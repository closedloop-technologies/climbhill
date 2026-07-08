from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from awesome_deep_research.mcp_server import build_fastmcp_server, forward_event_to_context


class FakeContext:
    def __init__(self) -> None:
        self.messages: List[str] = []

    async def info(self, message: str) -> None:
        self.messages.append(message)


def test_forward_event_to_context_sends_structured_json() -> None:
    ctx = FakeContext()
    event = {
        "timestamp": "2026-06-26T00:00:00+00:00",
        "provider_id": "deep-research-perplexity",
        "kind": "started",
        "message": "provider started",
    }

    asyncio.run(forward_event_to_context(ctx, event))

    assert json.loads(ctx.messages[0]) == event


def test_fastmcp_server_builds() -> None:
    server = build_fastmcp_server()

    assert server is not None
