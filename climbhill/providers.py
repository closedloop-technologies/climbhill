from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional
from urllib.parse import quote

import requests


ProviderEventSink = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    aliases: List[str]
    access_mode: str
    required_env_vars: List[str]
    default_timeout_seconds: int = 300


@dataclass
class ProviderOutput:
    text: str
    raw_payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cost: Optional[float] = None


@dataclass
class ProviderResult:
    provider_id: str
    status: str
    latency_seconds: float
    raw_output_path: Optional[str] = None
    okf_bundle_path: Optional[str] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass(frozen=True)
class ProviderRuntime:
    provider_id: str
    question: str
    run_dir: Path
    timeout_seconds: int
    env: Mapping[str, str]
    event_sink: ProviderEventSink


class ProviderAdapter:
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        raise NotImplementedError


class UnimplementedProviderAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        raise RuntimeError(
            f"No direct Provider Adapter is implemented for {runtime.provider_id}. "
            "This provider is discoverable, but its MCP adapter still needs to be wired."
        )


class StaticProviderAdapter(ProviderAdapter):
    def __init__(self, text: str, metadata: Optional[Dict[str, Any]] = None, cost: Optional[float] = None):
        self.text = text
        self.metadata = metadata or {}
        self.cost = cost

    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        return ProviderOutput(text=self.text, raw_payload={"text": self.text}, metadata=dict(self.metadata), cost=self.cost)


class PerplexityAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env["PERPLEXITY_API_KEY"]
        payload = {
            "model": runtime.env.get("PERPLEXITY_MODEL", "sonar"),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert researcher. Answer with current, neutral, "
                        "citation-backed information."
                    ),
                },
                {"role": "user", "content": runtime.question},
            ],
            "extra_body": {
                "search_context_size": runtime.env.get("PERPLEXITY_SEARCH_CONTEXT_SIZE", "low")
            },
        }

        response = await asyncio.to_thread(
            requests.post,
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        text = ""
        if choices:
            text = ((choices[0].get("message") or {}).get("content") or "").strip()
        usage = body.get("usage") or {}
        cost = None
        usage_cost = usage.get("cost")
        if isinstance(usage_cost, dict):
            cost = usage_cost.get("total_cost")
        metadata = {
            "model": body.get("model") or payload["model"],
            "usage": usage,
            "citations": body.get("citations"),
            "provider_request_id": response.headers.get("request-id"),
        }
        return ProviderOutput(text=text, raw_payload=body, metadata=metadata, cost=cost)


class OpenAIAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env["OPENAI_API_KEY"]
        model = runtime.env.get("OPENAI_DEEP_RESEARCH_MODEL", "o4-mini-deep-research")
        effort = runtime.env.get("OPENAI_DEEP_RESEARCH_EFFORT", "medium")
        payload = {
            "model": model,
            "input": [{"role": "user", "content": runtime.question}],
            "reasoning": {"effort": effort},
        }

        response = await asyncio.to_thread(
            requests.post,
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "OpenAI-Beta": "assistants=v2",
            },
            data=json.dumps(payload),
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        text = body.get("output_text") or _extract_text(body) or json.dumps(body, indent=2)
        usage = body.get("usage") or {}
        metadata = {
            "model": body.get("model") or model,
            "effort": effort,
            "usage": usage,
            "provider_request_id": body.get("id") or response.headers.get("request-id"),
        }
        return ProviderOutput(text=text.strip(), raw_payload=body, metadata=metadata)


class GeminiAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env.get("GOOGLE_API_KEY") or runtime.env["GEMINI_API_KEY"]
        mode = runtime.env.get("GEMINI_MODE", "grounded")
        if mode == "deep-research-start":
            payload = {
                "agent": runtime.env.get("GEMINI_DEEP_RESEARCH_AGENT", "deep-research-preview-04-2026"),
                "input": runtime.question,
                "background": True,
                "agent_config": {
                    "type": "deep-research",
                    "thinking_summaries": "none",
                    "visualization": "off",
                    "collaborative_planning": False,
                },
            }
        else:
            payload = {
                "model": runtime.env.get("GEMINI_MODEL", "gemini-3.5-flash"),
                "input": runtime.question,
                "tools": [{"type": "google_search"}],
            }

        response = await asyncio.to_thread(
            requests.post,
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        citations = _extract_url_citations(body)
        text = _extract_text(body) or json.dumps(body, indent=2)
        if citations:
            text += "\n\n# Citations\n\n" + "\n".join(
                f"[{index}] [{citation['title']}]({citation['url']})"
                for index, citation in enumerate(citations, start=1)
            )
        metadata = {
            "mode": mode,
            "model": payload.get("model"),
            "agent": payload.get("agent"),
            "citations": citations,
            "number_of_citations": len(citations),
        }
        return ProviderOutput(text=text.strip(), raw_payload=body, metadata=metadata)


class TavilyAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env["TAVILY_API_KEY"]
        max_results = int(runtime.env.get("TAVILY_MAX_RESULTS", "5"))
        payload = {
            "query": runtime.question,
            "search_depth": runtime.env.get("TAVILY_SEARCH_DEPTH", "basic"),
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
        }

        response = await asyncio.to_thread(
            requests.post,
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        answer = body.get("answer") or ""
        results = body.get("results") or []
        source_lines = []
        for result in results:
            title = result.get("title") or result.get("url") or "source"
            url = result.get("url")
            if url:
                source_lines.append(f"- [{title}]({url})")
        text = answer.strip()
        if source_lines:
            text = text + "\n\n## Sources\n" + "\n".join(source_lines)
        metadata = {
            "search_depth": payload["search_depth"],
            "max_results": max_results,
            "number_of_search_results": len(results),
            "results": results,
        }
        return ProviderOutput(text=text.strip(), raw_payload=body, metadata=metadata)


class ExaAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env["EXA_API_KEY"]
        num_results = int(runtime.env.get("EXA_NUM_RESULTS", "5"))
        payload = {
            "query": runtime.question,
            "numResults": num_results,
            "type": "auto",
            "contents": {"text": True},
        }
        response = await asyncio.to_thread(
            requests.post,
            "https://api.exa.ai/search",
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        results = body.get("results") or []
        lines = ["# Exa Search Results", ""]
        for index, result in enumerate(results, start=1):
            title = result.get("title") or result.get("url") or f"Result {index}"
            url = result.get("url")
            text = result.get("text") or ""
            lines.append(f"## {index}. {title}")
            if url:
                lines.append(url)
            if text:
                lines.append(text.strip())
            lines.append("")
        metadata = {
            "num_results": num_results,
            "number_of_search_results": len(results),
            "results": results,
        }
        return ProviderOutput(text="\n".join(lines).strip(), raw_payload=body, metadata=metadata)


class JinaAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env.get("JINA_API_KEY")
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        response = await asyncio.to_thread(
            requests.get,
            f"https://s.jina.ai/{quote(runtime.question)}",
            headers=headers,
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        results = body.get("data") or []
        lines = ["# Jina Search Results", ""]
        for index, result in enumerate(results, start=1):
            title = result.get("title") or result.get("url") or f"Result {index}"
            url = result.get("url")
            content = result.get("content") or ""
            lines.append(f"## {index}. {title}")
            if url:
                lines.append(url)
            if content:
                lines.append(content.strip())
            lines.append("")
        metadata = {
            "number_of_search_results": len(results),
            "results": results,
        }
        return ProviderOutput(text="\n".join(lines).strip(), raw_payload=body, metadata=metadata)


class YouResearchAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        api_key = runtime.env["YOU_API_KEY"]
        research_effort = runtime.env.get("YOU_RESEARCH_EFFORT", "lite")
        payload = {"input": runtime.question, "research_effort": research_effort}
        response = await asyncio.to_thread(
            requests.post,
            "https://api.you.com/v1/research",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=runtime.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        output = body.get("output", body)
        content = output.get("content") if isinstance(output, dict) else None
        sources = output.get("sources", []) if isinstance(output, dict) else []
        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)
        text = str(content or json.dumps(body, indent=2)).strip()
        source_lines = []
        for index, source in enumerate(sources, start=1):
            title = source.get("title") or source.get("url") or f"Source {index}"
            url = source.get("url")
            if url:
                source_lines.append(f"[{index}] [{title}]({url})")
        if source_lines:
            text += "\n\n# Citations\n\n" + "\n".join(source_lines)
        metadata = {
            "research_effort": research_effort,
            "number_of_sources": len(sources),
            "sources": sources,
        }
        return ProviderOutput(text=text, raw_payload=body, metadata=metadata)


class GrokAdapter(ProviderAdapter):
    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        return await asyncio.to_thread(self._run_sync, runtime)

    def _run_sync(self, runtime: ProviderRuntime) -> ProviderOutput:
        try:
            from xai_sdk import Client
            from xai_sdk.chat import user
            from xai_sdk.tools import web_search, x_search
        except ImportError as exc:
            raise RuntimeError("xai-sdk is required for deep-research-xai-grok.") from exc

        client = Client(api_key=runtime.env["XAI_API_KEY"])
        tools = []
        if _truthy(runtime.env.get("XAI_ENABLE_WEB_SEARCH", "true")):
            tools.append(web_search())
        if _truthy(runtime.env.get("XAI_ENABLE_X_SEARCH", "false")):
            tools.append(x_search())

        model = runtime.env.get("XAI_MODEL", "grok-4.1-fast-reasoning")
        chat = client.chat.create(model=model, tools=tools)
        chat.append(user(runtime.question))

        final_response = None
        tool_call_count = 0
        for chunk in chat.stream():
            if getattr(chunk, "tool_calls", None):
                tool_call_count += len(chunk.tool_calls)
            final_response = chunk

        content = getattr(final_response, "content", None) if final_response else None
        citations = getattr(final_response, "citations", None) if final_response else None
        citation_payloads = []
        citation_lines = []
        for citation in citations or []:
            title = getattr(citation, "title", None) or getattr(citation, "url", None) or "source"
            url = getattr(citation, "url", None)
            citation_payloads.append({"title": title, "url": url})
            if url:
                citation_lines.append(f"- [{title}]({url})")
        text = content or "No final response received."
        if citation_lines:
            text += "\n\n# Citations\n\n" + "\n".join(citation_lines)
        metadata = {
            "model": model,
            "web_search_enabled": any(tool.__class__.__name__ for tool in tools),
            "x_search_enabled": _truthy(runtime.env.get("XAI_ENABLE_X_SEARCH", "false")),
            "tool_call_count": tool_call_count,
            "citations": citation_payloads,
            "number_of_citations": len(citation_payloads),
        }
        return ProviderOutput(text=text.strip(), raw_payload={"content": content, "citations": citation_payloads}, metadata=metadata)


def _truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _extract_text(payload: Any) -> str:
    blocks: List[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key in ["output_text", "text"]:
                item = value.get(key)
                if isinstance(item, str) and item.strip():
                    blocks.append(item.strip())
            content = value.get("content")
            if isinstance(content, str) and content.strip():
                blocks.append(content.strip())
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    deduped = list(dict.fromkeys(blocks))
    return "\n\n".join(deduped)


def _extract_url_citations(payload: Any) -> List[Dict[str, str]]:
    citations: List[Dict[str, str]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("type") == "url_citation" and value.get("url"):
                citations.append({"title": value.get("title") or value["url"], "url": value["url"]})
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return list({citation["url"]: citation for citation in citations}.values())


DEFAULT_PROVIDER_SPECS: List[ProviderSpec] = [
    ProviderSpec("deep-research-perplexity", ["perplexity"], "commercial_api", ["PERPLEXITY_API_KEY"]),
    ProviderSpec("deep-research-openai", ["openai"], "commercial_api", ["OPENAI_API_KEY"]),
    ProviderSpec("deep-research-gemini", ["gemini"], "commercial_api", ["GEMINI_API_KEY"]),
    ProviderSpec("deep-research-you", ["you", "you-com"], "commercial_api", ["YOU_API_KEY"]),
    ProviderSpec("deep-research-xai-grok", ["xai-grok", "grok"], "commercial_api", ["XAI_API_KEY"]),
    ProviderSpec("deep-research-exa", ["exa"], "search_api", ["EXA_API_KEY"]),
    ProviderSpec("deep-research-jina", ["jina"], "search_api", ["JINA_API_KEY"]),
    ProviderSpec("deep-research-tavily", ["tavily"], "search_api", ["TAVILY_API_KEY"]),
    ProviderSpec("deep-research-gpt-researcher", ["gpt-researcher"], "self_hosted_library", ["ADR_MCP_ENABLE_GPT_RESEARCHER", "OPENAI_API_KEY", "TAVILY_API_KEY"]),
    ProviderSpec("deep-research-langchain", ["langchain"], "self_hosted_library", ["ADR_MCP_ENABLE_LANGCHAIN", "OPENAI_API_KEY"]),
    ProviderSpec("deep-research-smolagents", ["smolagents"], "self_hosted_library", ["ADR_MCP_ENABLE_SMOLAGENTS", "OPENAI_API_KEY"]),
    ProviderSpec("deep-research-stanford-storm", ["stanford-storm", "storm"], "self_hosted_library", ["ADR_MCP_ENABLE_STANFORD_STORM", "OPENAI_API_KEY"]),
]


DEFAULT_ADAPTERS: Dict[str, ProviderAdapter] = {
    "deep-research-exa": ExaAdapter(),
    "deep-research-gemini": GeminiAdapter(),
    "deep-research-jina": JinaAdapter(),
    "deep-research-openai": OpenAIAdapter(),
    "deep-research-perplexity": PerplexityAdapter(),
    "deep-research-tavily": TavilyAdapter(),
    "deep-research-xai-grok": GrokAdapter(),
    "deep-research-you": YouResearchAdapter(),
}


class ProviderRegistry:
    def __init__(
        self,
        specs: Optional[Iterable[ProviderSpec]] = None,
        adapters: Optional[Mapping[str, ProviderAdapter]] = None,
    ):
        self._specs = {spec.provider_id: spec for spec in (specs or DEFAULT_PROVIDER_SPECS)}
        self._adapters = dict(adapters or DEFAULT_ADAPTERS)
        self._aliases: Dict[str, str] = {}
        for spec in self._specs.values():
            self._aliases[spec.provider_id] = spec.provider_id
            short_id = spec.provider_id
            if short_id.startswith("deep-research-"):
                short_id = short_id[len("deep-research-") :]
            self._aliases[short_id] = spec.provider_id
            for alias in spec.aliases:
                self._aliases[alias] = spec.provider_id

    def list_specs(self) -> List[ProviderSpec]:
        return [self._specs[key] for key in sorted(self._specs)]

    def resolve(self, provider_name: str) -> Optional[str]:
        key = provider_name.strip().lower()
        return self._aliases.get(key)

    def get_spec(self, provider_id: str) -> ProviderSpec:
        return self._specs[provider_id]

    def get_adapter(self, provider_id: str) -> ProviderAdapter:
        return self._adapters.get(provider_id, UnimplementedProviderAdapter())

    def has_adapter(self, provider_id: str) -> bool:
        return provider_id in self._adapters


def provider_enabled(spec: ProviderSpec, env: Mapping[str, str]) -> bool:
    return all(bool(env.get(name)) for name in spec.required_env_vars)


def environment() -> Mapping[str, str]:
    return os.environ
