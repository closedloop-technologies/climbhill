from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from .mcp_app import DeepResearchService

try:
    from mcp.server.fastmcp import Context as FastMCPContext
except ImportError:  # pragma: no cover - optional dependency
    FastMCPContext = Any


def create_service() -> DeepResearchService:
    return DeepResearchService()


async def list_providers() -> Dict[str, Any]:
    return create_service().list_providers()


async def deep_research(
    question: str,
    providers: List[str],
    max_concurrency: Optional[int] = None,
) -> Dict[str, Any]:
    return await create_service().deep_research(
        question=question,
        providers=providers,
        max_concurrency=max_concurrency,
    )


async def forward_event_to_context(ctx: Any, event: Dict[str, Any]) -> None:
    await ctx.info(json.dumps(event, sort_keys=True))


def build_fastmcp_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The MCP server dependency is not installed. Install with "
            "`pip install 'climbhill-ai[mcp]'` or add `mcp` to this environment."
        ) from exc

    server = FastMCP("awesome-deep-research")

    @server.tool(name="list_providers")
    async def list_providers_tool() -> Dict[str, Any]:
        """List supported deep research providers and MCP configuration state."""
        return await list_providers()

    @server.tool(name="deep_research")
    async def deep_research_tool(
        ctx: FastMCPContext,
        question: str,
        providers: List[str],
        max_concurrency: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run selected deep research providers and write OKF artifacts."""
        service = create_service()
        return await service.deep_research(
            question=question,
            providers=providers,
            max_concurrency=max_concurrency,
            event_callback=lambda event: forward_event_to_context(ctx, event),
        )

    return server


def main() -> int:
    try:
        server = build_fastmcp_server()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    server.run()
    return 0


def smoke_main() -> int:
    """Small JSON smoke path for environments without an MCP client."""
    payload = asyncio.run(list_providers())
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
