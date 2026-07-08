from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from awesome_deep_research.mcp_app import DeepResearchService
from awesome_deep_research.providers import (
    ProviderAdapter,
    ProviderOutput,
    ProviderRegistry,
    ProviderRuntime,
    ProviderSpec,
)


class RecordingAdapter(ProviderAdapter):
    def __init__(self, name: str, events: List[str], fail: bool = False):
        self.name = name
        self.events = events
        self.fail = fail

    async def run(self, runtime: ProviderRuntime) -> ProviderOutput:
        self.events.append(f"adapter-start:{self.name}")
        await asyncio.sleep(0.01)
        if self.fail:
            raise RuntimeError(f"{self.name} failed")
        self.events.append(f"adapter-finish:{self.name}")
        return ProviderOutput(
            text=f"# {self.name}\n\nBasil grows well in bright light. https://example.com/{self.name}",
            raw_payload={"answer": self.name},
            metadata={"number_of_searches": 2, "model": "test-model"},
            cost=0.123,
        )


def make_service(tmp_path: Path, adapters: Dict[str, ProviderAdapter]) -> DeepResearchService:
    specs = [
        ProviderSpec("deep-research-alpha", ["alpha"], "commercial_api", ["ALPHA_API_KEY"]),
        ProviderSpec("deep-research-beta", ["beta"], "self_hosted_library", []),
    ]
    registry = ProviderRegistry(specs=specs, adapters=adapters)
    env = {
        "DEEP_RESEARCH_OUTPUT_ROOT": str(tmp_path),
        "ALPHA_API_KEY": "test-key",
    }
    return DeepResearchService(registry=registry, env=env)


def test_list_providers_returns_full_supported_list_with_enabled_state(tmp_path: Path) -> None:
    service = make_service(tmp_path, adapters={"deep-research-alpha": RecordingAdapter("alpha", [])})

    providers = service.list_providers()["providers"]

    assert providers == [
        {
            "id": "deep-research-alpha",
            "aliases": ["alpha"],
            "enabled": True,
            "required_env_vars": ["ALPHA_API_KEY"],
            "access_mode": "commercial_api",
        },
        {
            "id": "deep-research-beta",
            "aliases": ["beta"],
            "enabled": False,
            "required_env_vars": [],
            "access_mode": "self_hosted_library",
        },
    ]


@pytest.mark.parametrize(
    ("providers", "status", "code"),
    [
        ([], "invalid_request", "missing_providers"),
        (["unknown"], "invalid_request", "unknown_provider"),
    ],
)
def test_deep_research_preflight_rejects_invalid_provider_requests(
    tmp_path: Path, providers: List[str], status: str, code: str
) -> None:
    service = make_service(tmp_path, adapters={})

    result = asyncio.run(service.deep_research(question="How do I grow basil?", providers=providers))

    assert result["status"] == status
    assert result["error"]["code"] == code
    assert not list(tmp_path.iterdir())


def test_deep_research_preflight_rejects_disabled_selected_provider(tmp_path: Path) -> None:
    specs = [ProviderSpec("deep-research-alpha", ["alpha"], "commercial_api", ["ALPHA_API_KEY"])]
    service = DeepResearchService(
        registry=ProviderRegistry(specs=specs, adapters={}),
        env={"DEEP_RESEARCH_OUTPUT_ROOT": str(tmp_path)},
    )

    result = asyncio.run(service.deep_research(question="How do I grow basil?", providers=["alpha"]))

    assert result["status"] == "configuration_error"
    assert result["error"]["code"] == "disabled_provider"
    assert result["error"]["disabled_providers"] == [
        {
            "id": "deep-research-alpha",
            "missing_env_vars": ["ALPHA_API_KEY"],
            "adapter_available": False,
        }
    ]
    assert not list(tmp_path.iterdir())


def test_deep_research_runs_selected_providers_in_parallel_and_writes_artifacts(
    tmp_path: Path,
) -> None:
    adapter_events: List[str] = []
    streamed_events: List[Dict[str, Any]] = []
    service = make_service(
        tmp_path,
        adapters={
            "deep-research-alpha": RecordingAdapter("alpha", adapter_events),
            "deep-research-beta": RecordingAdapter("beta", adapter_events, fail=True),
        },
    )

    async def capture(event: Dict[str, Any]) -> None:
        streamed_events.append(event)

    result = asyncio.run(
        service.deep_research(
            question="How do I grow basil at home?",
            providers=["alpha", "deep-research-beta"],
            event_callback=capture,
        )
    )

    assert result["status"] == "partial_success"
    assert result["aggregate_okf_bundle_path"] is not None
    assert [provider["provider_id"] for provider in result["providers"]] == [
        "deep-research-alpha",
        "deep-research-beta",
    ]
    alpha = result["providers"][0]
    beta = result["providers"][1]
    assert alpha["status"] == "succeeded"
    assert alpha["cost"] == 0.123
    assert alpha["metadata"]["number_of_searches"] == 2
    assert beta["status"] == "failed"
    assert "beta failed" in beta["error"]

    assert adapter_events[:2] == ["adapter-start:alpha", "adapter-start:beta"]

    run_dir = Path(result["run_dir"])
    assert (run_dir / "summary.json").exists()
    assert Path(result["event_log_path"]).exists()
    assert Path(alpha["raw_output_path"]).exists()
    assert Path(alpha["okf_bundle_path"], "index.md").exists()
    assert Path(result["aggregate_okf_bundle_path"], "index.md").exists()

    event_lines = [
        json.loads(line)
        for line in Path(result["event_log_path"]).read_text(encoding="utf-8").splitlines()
    ]
    assert any(event["provider_id"] == "deep-research-alpha" and event["kind"] == "started" for event in event_lines)
    assert any(event["provider_id"] == "deep-research-beta" and event["kind"] == "error" for event in event_lines)
    assert streamed_events == event_lines


def test_deep_research_accepts_alias_without_deep_research_prefix(tmp_path: Path) -> None:
    service = make_service(
        tmp_path,
        adapters={"deep-research-alpha": RecordingAdapter("alpha", [])},
    )

    result = asyncio.run(service.deep_research(question="How do I grow basil?", providers=["alpha"]))

    assert result["status"] == "succeeded"
    assert result["providers"][0]["provider_id"] == "deep-research-alpha"
