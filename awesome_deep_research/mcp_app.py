from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from .okf import write_aggregate_okf_bundle, write_json, write_provider_okf_bundle
from .providers import (
    ProviderOutput,
    ProviderRegistry,
    ProviderResult,
    ProviderRuntime,
    environment,
    provider_enabled,
)


EventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


DEFAULT_OUTPUT_ROOT = "~/.deep-research/outputs"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_id_for(question: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(question.encode("utf-8")).hexdigest()[:8]
    return f"{stamp}-{digest}"


def configured_output_root(env: Mapping[str, str]) -> Path:
    return Path(env.get("DEEP_RESEARCH_OUTPUT_ROOT", DEFAULT_OUTPUT_ROOT)).expanduser()


def timeout_for(provider_id: str, default_seconds: int, env: Mapping[str, str]) -> int:
    specific_name = f"{provider_id.upper().replace('-', '_')}_TIMEOUT_SECONDS"
    value = env.get(specific_name) or env.get("DEEP_RESEARCH_TIMEOUT_SECONDS")
    if not value:
        return default_seconds
    try:
        timeout = int(value)
    except ValueError as exc:
        raise ValueError(f"{specific_name} or DEEP_RESEARCH_TIMEOUT_SECONDS must be an integer.") from exc
    if timeout <= 0:
        raise ValueError(f"{specific_name} or DEEP_RESEARCH_TIMEOUT_SECONDS must be positive.")
    return timeout


class DeepResearchService:
    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        env: Optional[Mapping[str, str]] = None,
    ):
        self.registry = registry or ProviderRegistry()
        self.env = env or environment()

    def list_providers(self) -> Dict[str, Any]:
        providers = []
        for spec in self.registry.list_specs():
            providers.append(
                {
                    "id": spec.provider_id,
                    "aliases": list(spec.aliases),
                    "enabled": provider_enabled(spec, self.env)
                    and self.registry.has_adapter(spec.provider_id),
                    "required_env_vars": list(spec.required_env_vars),
                    "access_mode": spec.access_mode,
                }
            )
        return {"providers": providers}

    async def deep_research(
        self,
        *,
        question: str,
        providers: Iterable[str],
        max_concurrency: Optional[int] = None,
        event_callback: Optional[EventCallback] = None,
    ) -> Dict[str, Any]:
        validation_error = self._validate_question_and_concurrency(question, max_concurrency)
        if validation_error:
            return validation_error

        requested = list(providers or [])
        resolved, request_error = self._resolve_requested_providers(requested)
        if request_error:
            return request_error

        config_error = self._validate_provider_configuration(resolved)
        if config_error:
            return config_error

        output_root = configured_output_root(self.env)
        run_dir = self._create_run_dir(output_root, question)
        events_path = run_dir / "events.jsonl"

        async def emit(event: Dict[str, Any]) -> None:
            event = {"timestamp": utc_now(), **event}
            with events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
            if event_callback:
                await event_callback(event)

        await emit({"kind": "started", "message": "research run started", "provider_id": None})

        semaphore = asyncio.Semaphore(max_concurrency or len(resolved))
        tasks = [
            asyncio.create_task(self._run_one_provider(provider_id, question, run_dir, semaphore, emit))
            for provider_id in resolved
        ]
        provider_results = await asyncio.gather(*tasks)

        provider_summaries = [self._provider_result_summary(result) for result in provider_results]
        successful = [summary for summary in provider_summaries if summary["status"] == "succeeded"]

        aggregate_path = None
        if successful:
            aggregate_dir = run_dir / "aggregate-okf"
            write_aggregate_okf_bundle(
                aggregate_dir,
                question=question,
                provider_results=provider_summaries,
            )
            aggregate_path = str(aggregate_dir)

        run_status = self._run_status(provider_summaries)
        summary = {
            "status": run_status,
            "question": question,
            "run_dir": str(run_dir),
            "aggregate_okf_bundle_path": aggregate_path,
            "providers": provider_summaries,
            "event_log_path": str(events_path),
        }
        write_json(run_dir / "summary.json", summary)
        await emit({"kind": "finished", "message": f"research run {run_status}", "provider_id": None})
        return summary

    def _create_run_dir(self, output_root: Path, question: str) -> Path:
        output_root.mkdir(parents=True, exist_ok=True)
        base = run_id_for(question)
        for index in range(1000):
            suffix = "" if index == 0 else f"-{index:03d}"
            run_dir = output_root / f"{base}{suffix}"
            try:
                run_dir.mkdir(parents=True, exist_ok=False)
                return run_dir
            except FileExistsError:
                continue
        raise RuntimeError("Could not create a unique Run Directory.")

    def _validate_question_and_concurrency(
        self, question: str, max_concurrency: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(question, str) or not question.strip():
            return {
                "status": "invalid_request",
                "error": {
                    "code": "missing_question",
                    "message": "`question` must be a non-empty string.",
                },
            }
        if max_concurrency is not None and max_concurrency <= 0:
            return {
                "status": "invalid_request",
                "error": {
                    "code": "invalid_max_concurrency",
                    "message": "`max_concurrency` must be positive when provided.",
                },
            }
        return None

    def _resolve_requested_providers(
        self, requested: List[str]
    ) -> Tuple[List[str], Optional[Dict[str, Any]]]:
        if not requested:
            return [], {
                "status": "invalid_request",
                "error": {
                    "code": "missing_providers",
                    "message": "`providers` must name at least one provider. Use `list_providers`.",
                },
                "providers": self.list_providers()["providers"],
            }

        resolved: List[str] = []
        seen = set()
        for provider_name in requested:
            if not isinstance(provider_name, str) or not provider_name.strip():
                return [], {
                    "status": "invalid_request",
                    "error": {
                        "code": "invalid_provider_name",
                        "message": "Each provider must be a non-empty string. Use `list_providers`.",
                    },
                }
            provider_id = self.registry.resolve(provider_name)
            if provider_id is None:
                return [], {
                    "status": "invalid_request",
                    "error": {
                        "code": "unknown_provider",
                        "message": f"Unknown provider `{provider_name}`. Use `list_providers`.",
                    },
                    "providers": self.list_providers()["providers"],
                }
            if provider_id not in seen:
                resolved.append(provider_id)
                seen.add(provider_id)
        return resolved, None

    def _validate_provider_configuration(self, provider_ids: List[str]) -> Optional[Dict[str, Any]]:
        disabled = []
        for provider_id in provider_ids:
            spec = self.registry.get_spec(provider_id)
            missing = [name for name in spec.required_env_vars if not self.env.get(name)]
            adapter_available = self.registry.has_adapter(provider_id)
            if missing or not adapter_available:
                disabled.append(
                    {
                        "id": provider_id,
                        "missing_env_vars": missing,
                        "adapter_available": adapter_available,
                    }
                )

        if disabled:
            return {
                "status": "configuration_error",
                "error": {
                    "code": "disabled_provider",
                    "message": (
                        "One or more selected providers are disabled in the MCP server "
                        "environment or lack a direct MCP Provider Adapter. Add missing "
                        "env vars to the MCP server definition, or select an enabled "
                        "provider from `list_providers`."
                    ),
                    "disabled_providers": disabled,
                },
            }
        return None

    async def _run_one_provider(
        self,
        provider_id: str,
        question: str,
        run_dir: Path,
        semaphore: asyncio.Semaphore,
        emit: EventCallback,
    ) -> ProviderResult:
        async with semaphore:
            spec = self.registry.get_spec(provider_id)
            provider_dir = run_dir / "providers" / provider_id
            raw_dir = provider_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()

            await emit({"provider_id": provider_id, "kind": "started", "message": "provider started"})
            try:
                timeout = timeout_for(provider_id, spec.default_timeout_seconds, self.env)
                runtime = ProviderRuntime(
                    provider_id=provider_id,
                    question=question,
                    run_dir=run_dir,
                    timeout_seconds=timeout,
                    env=self.env,
                    event_sink=emit,
                )
                output = await asyncio.wait_for(
                    self.registry.get_adapter(provider_id).run(runtime),
                    timeout=timeout,
                )
                result = self._persist_success(provider_id, question, provider_dir, raw_dir, output, started)
                await emit(
                    {
                        "provider_id": provider_id,
                        "kind": "finished",
                        "message": "provider finished",
                    }
                )
                return result
            except asyncio.TimeoutError:
                latency = time.monotonic() - started
                message = "provider timed out"
                write_json(raw_dir / "error.json", {"error": message, "provider_id": provider_id})
                await emit({"provider_id": provider_id, "kind": "error", "message": message})
                return ProviderResult(provider_id=provider_id, status="timed_out", latency_seconds=latency, error=message)
            except Exception as exc:
                latency = time.monotonic() - started
                message = str(exc)
                write_json(raw_dir / "error.json", {"error": message, "provider_id": provider_id})
                await emit({"provider_id": provider_id, "kind": "error", "message": message})
                return ProviderResult(provider_id=provider_id, status="failed", latency_seconds=latency, error=message)

    def _persist_success(
        self,
        provider_id: str,
        question: str,
        provider_dir: Path,
        raw_dir: Path,
        output: ProviderOutput,
        started: float,
    ) -> ProviderResult:
        raw_text_path = raw_dir / "response.md"
        raw_json_path = raw_dir / "response.json"
        raw_text_path.write_text(output.text.strip() + "\n", encoding="utf-8")
        write_json(
            raw_json_path,
            {
                "provider_id": provider_id,
                "text": output.text,
                "raw_payload": output.raw_payload,
                "metadata": output.metadata,
                "cost": output.cost,
            },
        )
        okf_dir = provider_dir / "okf"
        write_provider_okf_bundle(
            okf_dir,
            question=question,
            provider_id=provider_id,
            report_text=output.text,
            metadata=output.metadata,
            raw_output_path=raw_json_path,
        )
        return ProviderResult(
            provider_id=provider_id,
            status="succeeded",
            latency_seconds=time.monotonic() - started,
            raw_output_path=str(raw_json_path),
            okf_bundle_path=str(okf_dir),
            cost=output.cost,
            metadata=dict(output.metadata),
        )

    def _provider_result_summary(self, result: ProviderResult) -> Dict[str, Any]:
        summary = asdict(result)
        summary["latency_seconds"] = round(result.latency_seconds, 6)
        return summary

    def _run_status(self, provider_summaries: List[Mapping[str, Any]]) -> str:
        successes = [summary for summary in provider_summaries if summary["status"] == "succeeded"]
        if len(successes) == len(provider_summaries):
            return "succeeded"
        if successes:
            return "partial_success"
        return "failed"
