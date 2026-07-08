from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import awesome_deep_research.providers as providers_module
from awesome_deep_research.mcp_app import DeepResearchService
from awesome_deep_research.providers import (
    ExaAdapter,
    GeminiAdapter,
    JinaAdapter,
    OpenAIAdapter,
    PerplexityAdapter,
    ProviderRuntime,
    TavilyAdapter,
    YouResearchAdapter,
)


class FakeResponse:
    def __init__(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None):
        self.payload = payload
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Dict[str, Any]:
        return self.payload


async def noop_event(_: Dict[str, Any]) -> None:
    return None


def runtime(env: Dict[str, str]) -> ProviderRuntime:
    return ProviderRuntime(
        provider_id="deep-research-test",
        question="How can I grow basil at home?",
        run_dir=Path("/tmp/deep-research-test"),
        timeout_seconds=30,
        env=env,
        event_sink=noop_event,
    )


def test_default_list_providers_marks_self_hosted_disabled_without_mcp_adapter_flags() -> None:
    service = DeepResearchService(env={"OPENAI_API_KEY": "test", "TAVILY_API_KEY": "test"})

    by_id = {provider["id"]: provider for provider in service.list_providers()["providers"]}

    assert by_id["deep-research-openai"]["enabled"] is True
    assert by_id["deep-research-gpt-researcher"]["enabled"] is False
    assert "ADR_MCP_ENABLE_GPT_RESEARCHER" in by_id["deep-research-gpt-researcher"]["required_env_vars"]


def test_openai_adapter_parses_responses_payload(monkeypatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return FakeResponse(
            {
                "id": "resp_123",
                "model": "o4-mini-deep-research",
                "output_text": "Basil needs bright light.",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        )

    monkeypatch.setattr(providers_module.requests, "post", fake_post)

    output = asyncio.run(OpenAIAdapter().run(runtime({"OPENAI_API_KEY": "key"})))

    assert calls[0]["url"] == "https://api.openai.com/v1/responses"
    assert calls[0]["headers"]["Authorization"] == "Bearer key"
    assert output.text == "Basil needs bright light."
    assert output.metadata["usage"]["output_tokens"] == 5
    assert output.metadata["provider_request_id"] == "resp_123"


def test_gemini_adapter_preserves_citations(monkeypatch) -> None:
    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(
            {
                "output_text": "Plant basil after frost.",
                "citation": {
                    "type": "url_citation",
                    "title": "Basil guide",
                    "url": "https://example.com/basil",
                },
            }
        )

    monkeypatch.setattr(providers_module.requests, "post", fake_post)

    output = asyncio.run(GeminiAdapter().run(runtime({"GEMINI_API_KEY": "key"})))

    assert "Plant basil after frost." in output.text
    assert "[Basil guide](https://example.com/basil)" in output.text
    assert output.metadata["number_of_citations"] == 1


def test_search_api_adapters_preserve_provider_specific_counts(monkeypatch) -> None:
    responses = {
        "https://api.tavily.com/search": {
            "answer": "Basil likes sun.",
            "results": [{"title": "Basil", "url": "https://example.com/tavily"}],
        },
        "https://api.exa.ai/search": {
            "results": [{"title": "Basil", "url": "https://example.com/exa", "text": "Use a pot."}],
        },
    }

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(responses[url])

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(
            {
                "data": [
                    {
                        "title": "Basil",
                        "url": "https://example.com/jina",
                        "content": "Keep soil moist.",
                    }
                ]
            }
        )

    monkeypatch.setattr(providers_module.requests, "post", fake_post)
    monkeypatch.setattr(providers_module.requests, "get", fake_get)

    tavily = asyncio.run(TavilyAdapter().run(runtime({"TAVILY_API_KEY": "key"})))
    exa = asyncio.run(ExaAdapter().run(runtime({"EXA_API_KEY": "key"})))
    jina = asyncio.run(JinaAdapter().run(runtime({"JINA_API_KEY": "key"})))

    assert tavily.metadata["number_of_search_results"] == 1
    assert exa.metadata["number_of_search_results"] == 1
    assert jina.metadata["number_of_search_results"] == 1


def test_perplexity_and_you_adapters_extract_metadata(monkeypatch) -> None:
    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        if "perplexity" in url:
            return FakeResponse(
                {
                    "model": "sonar",
                    "choices": [{"message": {"content": "Basil grows indoors."}}],
                    "usage": {"cost": {"total_cost": 0.01}},
                    "citations": ["https://example.com/perplexity"],
                },
                headers={"request-id": "pplx-123"},
            )
        return FakeResponse(
            {
                "output": {
                    "content": "Basil likes containers.",
                    "sources": [{"title": "Container basil", "url": "https://example.com/you"}],
                }
            }
        )

    monkeypatch.setattr(providers_module.requests, "post", fake_post)

    perplexity = asyncio.run(PerplexityAdapter().run(runtime({"PERPLEXITY_API_KEY": "key"})))
    you = asyncio.run(YouResearchAdapter().run(runtime({"YOU_API_KEY": "key"})))

    assert perplexity.cost == 0.01
    assert perplexity.metadata["provider_request_id"] == "pplx-123"
    assert you.metadata["number_of_sources"] == 1
    assert "[Container basil](https://example.com/you)" in you.text
