from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from awesome_deep_research import source_refresh
from benchmark import utils as benchmark_utils


REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_PROVIDER_SKILLS = {
    "deep-research-custom-data",
    "deep-research-openai",
    "deep-research-perplexity",
    "deep-research-exa",
    "deep-research-tavily",
    "deep-research-jina",
    "deep-research-xai-grok",
    "deep-research-you",
    "deep-research-gemini",
    "deep-research-gpt-researcher",
    "deep-research-langchain",
    "deep-research-stanford-storm",
    "deep-research-smolagents",
}
REQUIRED_OP_EXAMPLE_SKILLS = REQUIRED_PROVIDER_SKILLS - {"deep-research-custom-data"}
REQUIRED_AGENTS_RUNNABLE_SKILLS = {
    "deep-research-custom-data": "validate_manifest.py",
    "deep-research-exa": "exa_tools.py",
    "deep-research-gemini": "gemini_research.py",
    "deep-research-gpt-researcher": "run_research.py",
    "deep-research-jina": "jina_tools.py",
    "deep-research-langchain": "research.py",
    "deep-research-you": "you_research.py",
    "deep-research-okf-normalize": "normalize_to_okf.py",
    "deep-research-openai": "run_deep_research.py",
    "deep-research-perplexity": "ask.py",
    "deep-research-smolagents": "agent.py",
    "deep-research-stanford-storm": "run_storm.py",
    "deep-research-tavily": "tavily_search.py",
    "deep-research-xai-grok": "grok_research.py",
}
REQUIRED_ENV_NAMES = {
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "EXA_API_KEY",
    "TAVILY_API_KEY",
    "JINA_API_KEY",
    "XAI_API_KEY",
    "YOU_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "HF_TOKEN",
    "ANTHROPIC_API_KEY",
    "BING_SEARCH_API_KEY",
    "YDC_API_KEY",
}
CANONICAL_PROMPT_SNIPPETS = {
    "Deepresearch the deepresearchers",
    "AI-for-science",
    "under $1",
}
REQUIRED_SOURCE_INDEX_SNIPPETS = {
    "deep-research-openai",
    "deep-research-gemini",
    "deep-research-you",
    "okf/SPEC.md",
    "Last refreshed: 2026-06-23",
}


@dataclass
class AuditResult:
    name: str
    ok: bool
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_file(path: Path, label: str) -> AuditResult:
    return AuditResult(label, path.exists(), str(path.relative_to(REPO_ROOT)))


def check_plugin_manifest() -> AuditResult:
    path = REPO_ROOT / ".codex-plugin" / "plugin.json"
    if not path.exists():
        return AuditResult("codex plugin manifest", False, "missing .codex-plugin/plugin.json")
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return AuditResult("codex plugin manifest", False, f"invalid JSON: {exc}")
    ok = data.get("name") == "awesome-deep-researchers" and data.get("skills") == "./skills/"
    return AuditResult("codex plugin manifest", ok, "name and skills path")


def check_provider_skills() -> AuditResult:
    missing = []
    for skill_name in sorted(REQUIRED_PROVIDER_SKILLS):
        for root in [".agents/skills", "skills"]:
            path = REPO_ROOT / root / skill_name / "SKILL.md"
            if not path.exists():
                missing.append(str(path.relative_to(REPO_ROOT)))
    ok = not missing
    return AuditResult("provider skill docs", ok, "missing: " + ", ".join(missing) if missing else "all present")


def check_mirrored_skill_directories() -> AuditResult:
    agents_skills = {
        path.name for path in (REPO_ROOT / ".agents" / "skills").iterdir() if path.is_dir()
    }
    packaged_skills = {path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()}
    missing_from_agents = sorted(packaged_skills - agents_skills)
    missing_from_package = sorted(agents_skills - packaged_skills)
    failures = []
    if missing_from_agents:
        failures.append("missing from .agents/skills: " + ", ".join(missing_from_agents))
    if missing_from_package:
        failures.append("missing from skills: " + ", ".join(missing_from_package))
    return AuditResult(
        "mirrored skill directories",
        not failures,
        "; ".join(failures) if failures else "skill directory sets match",
    )


def check_mirrored_skill_docs() -> AuditResult:
    agents_docs = {
        path.relative_to(REPO_ROOT / ".agents" / "skills")
        for path in (REPO_ROOT / ".agents" / "skills").glob("*/SKILL.md")
    }
    packaged_docs = {
        path.relative_to(REPO_ROOT / "skills")
        for path in (REPO_ROOT / "skills").glob("*/SKILL.md")
    }
    failures = []
    for relative in sorted(agents_docs - packaged_docs):
        failures.append(f"missing from skills: {relative}")
    for relative in sorted(packaged_docs - agents_docs):
        failures.append(f"missing from .agents/skills: {relative}")
    for relative in sorted(agents_docs & packaged_docs):
        agents_text = read_text(REPO_ROOT / ".agents" / "skills" / relative)
        packaged_text = read_text(REPO_ROOT / "skills" / relative)
        if agents_text != packaged_text:
            failures.append(f"skill doc mirror differs: {relative}")
    return AuditResult(
        "mirrored skill docs",
        not failures,
        "; ".join(failures) if failures else "skill docs match",
    )


def check_mirrored_skill_tests() -> AuditResult:
    agents_tests = {
        path.relative_to(REPO_ROOT / ".agents" / "skills")
        for path in (REPO_ROOT / ".agents" / "skills").glob("*/tests/test_*.py")
    }
    packaged_tests = {
        path.relative_to(REPO_ROOT / "skills")
        for path in (REPO_ROOT / "skills").glob("*/tests/test_*.py")
    }
    failures = []
    for relative in sorted(agents_tests - packaged_tests):
        failures.append(f"missing from skills: {relative}")
    for relative in sorted(packaged_tests - agents_tests):
        failures.append(f"missing from .agents/skills: {relative}")
    for relative in sorted(agents_tests & packaged_tests):
        agents_text = read_text(REPO_ROOT / ".agents" / "skills" / relative)
        packaged_text = read_text(REPO_ROOT / "skills" / relative)
        if agents_text != packaged_text:
            failures.append(f"test mirror differs: {relative}")
    return AuditResult(
        "mirrored skill tests",
        not failures,
        "; ".join(failures) if failures else "skill tests match",
    )


def check_mirrored_skill_scripts() -> AuditResult:
    agents_scripts = {
        path.relative_to(REPO_ROOT / ".agents" / "skills")
        for path in (REPO_ROOT / ".agents" / "skills").glob("*/scripts/*.py")
    }
    packaged_scripts = {
        path.relative_to(REPO_ROOT / "skills")
        for path in (REPO_ROOT / "skills").glob("*/scripts/*.py")
    }
    failures = []
    for relative in sorted(agents_scripts - packaged_scripts):
        failures.append(f"missing from skills: {relative}")
    for relative in sorted(packaged_scripts - agents_scripts):
        failures.append(f"missing from .agents/skills: {relative}")
    for relative in sorted(agents_scripts & packaged_scripts):
        agents_text = read_text(REPO_ROOT / ".agents" / "skills" / relative)
        packaged_text = read_text(REPO_ROOT / "skills" / relative)
        if agents_text != packaged_text:
            failures.append(f"script mirror differs: {relative}")
    return AuditResult(
        "mirrored skill scripts",
        not failures,
        "; ".join(failures) if failures else "skill scripts match",
    )


def check_skill_frontmatter() -> AuditResult:
    failures = []
    for root in [".agents/skills", "skills"]:
        for path in sorted((REPO_ROOT / root).glob("*/SKILL.md")):
            text = read_text(path)
            relative = path.relative_to(REPO_ROOT)
            if not text.startswith("---\n"):
                failures.append(f"{relative} missing frontmatter")
                continue
            end = text.find("\n---", 4)
            if end == -1:
                failures.append(f"{relative} missing closing frontmatter")
                continue
            frontmatter = {}
            for line in text[4:end].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip().strip("\"'")
            if frontmatter.get("name") != path.parent.name:
                failures.append(f"{relative} name must match skill directory")
            if not frontmatter.get("description"):
                failures.append(f"{relative} description must be non-empty")
    return AuditResult(
        "skill frontmatter",
        not failures,
        "failures: " + ", ".join(failures) if failures else "all skill metadata valid",
    )


def check_provider_skill_commands() -> AuditResult:
    missing = []
    for skill_name in sorted(REQUIRED_OP_EXAMPLE_SKILLS):
        path = REPO_ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
        if path.exists() and "op run --env-file .env.adr" not in read_text(path):
            missing.append(skill_name)
    ok = not missing
    return AuditResult("provider op command examples", ok, ", ".join(missing) if missing else "all present")


def check_agents_runnable_skills() -> AuditResult:
    missing = []
    for skill_name, script_name in sorted(REQUIRED_AGENTS_RUNNABLE_SKILLS.items()):
        for root in [".agents/skills", "skills"]:
            script = REPO_ROOT / root / skill_name / "scripts" / script_name
            if not script.exists():
                missing.append(str(script.relative_to(REPO_ROOT)))
    ok = not missing
    return AuditResult("agents runnable skill scripts", ok, "missing: " + ", ".join(missing) if missing else "all present")


def check_no_compiled_python_artifacts() -> AuditResult:
    tracked_files = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
        check=True,
        capture_output=True,
    )
    compiled = sorted(
        path
        for path in tracked_files.stdout.splitlines()
        if "/__pycache__/" in path or path.endswith((".pyc", ".pyo"))
    )
    return AuditResult(
        "compiled Python artifacts",
        not compiled,
        "found: " + ", ".join(compiled) if compiled else "none present",
    )


def check_env_template() -> AuditResult:
    path = REPO_ROOT / ".env.adr.example"
    if not path.exists():
        return AuditResult("1Password env template", False, "missing .env.adr.example")
    text = read_text(path)
    missing = [name for name in sorted(REQUIRED_ENV_NAMES) if f"{name}=op://" not in text]
    return AuditResult(
        "1Password env template",
        not missing,
        "missing: " + ", ".join(missing) if missing else "all op references present",
    )


def check_gitignore_env() -> AuditResult:
    text = read_text(REPO_ROOT / ".gitignore")
    ok = ".env.adr" in text
    return AuditResult("env secret ignore", ok, ".env.adr ignored" if ok else ".env.adr not ignored")


def check_benchmark_tasks() -> AuditResult:
    text = read_text(REPO_ROOT / "docs" / "taxonomy-and-examples.md")
    missing = [snippet for snippet in sorted(CANONICAL_PROMPT_SNIPPETS) if snippet not in text]
    return AuditResult(
        "canonical benchmark tasks",
        not missing,
        "missing: " + ", ".join(missing) if missing else "all present",
    )


def check_benchmark_cost_gate() -> AuditResult:
    config = read_text(REPO_ROOT / "benchmark" / "config.py")
    runner = read_text(REPO_ROOT / "benchmark" / "benchmark.py")
    ok = "MAX_BENCHMARK_COST_USD = 1.00" in config and "Cost budget exceeded" in runner
    return AuditResult("under-$1 benchmark gate", ok, "MAX_BENCHMARK_COST_USD and enforcement")


def check_benchmark_command_coverage() -> AuditResult:
    missing = benchmark_utils.find_unregistered_benchmark_skills()
    return AuditResult(
        "benchmark command coverage",
        not missing,
        "missing: " + ", ".join(missing) if missing else "all runnable skills mapped",
    )


def check_okf_tooling() -> AuditResult:
    required = [
        REPO_ROOT / ".agents/skills/deep-research-okf-normalize/scripts/normalize_to_okf.py",
        REPO_ROOT / ".agents/skills/deep-research-okf-normalize/scripts/validate_okf.py",
        REPO_ROOT / "docs/okf-normalization.md",
    ]
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.exists()]
    return AuditResult("OKF tooling", not missing, "missing: " + ", ".join(missing) if missing else "all present")


def check_benchmark_auto_okf() -> AuditResult:
    runner = read_text(REPO_ROOT / "benchmark" / "benchmark.py")
    ok = "normalize_result_to_okf" in runner and "okf_valid" in runner
    return AuditResult("benchmark OKF normalization", ok, "automatic OKF metadata")


def check_custom_data_benchmark_command() -> AuditResult:
    utils = read_text(REPO_ROOT / "benchmark" / "utils.py")
    manifest = REPO_ROOT / "docs" / "examples" / "custom-data-corpus.example.json"
    ok = (
        '"deep-research-custom-data": "validate_manifest.py"' in utils
        and "custom-data-corpus.example.json" in utils
        and manifest.exists()
    )
    return AuditResult("custom data benchmark command", ok, "manifest validation command")


def check_provider_source_index() -> AuditResult:
    missing = []
    required_skill_names = sorted(
        path.name
        for path in (REPO_ROOT / ".agents" / "skills").iterdir()
        if path.is_dir()
    )
    for root in [".agents/skills", "skills"]:
        path = REPO_ROOT / root / "provider-source-index.md"
        if not path.exists():
            missing.append(str(path.relative_to(REPO_ROOT)))
            continue
        text = read_text(path)
        missing.extend(
            f"{path.relative_to(REPO_ROOT)} missing {snippet}"
            for snippet in sorted(REQUIRED_SOURCE_INDEX_SNIPPETS)
            if snippet not in text
        )
        missing.extend(
            f"{path.relative_to(REPO_ROOT)} missing skill {skill_name}"
            for skill_name in required_skill_names
            if f"`{skill_name}`" not in text
        )
    return AuditResult(
        "provider source index",
        not missing,
        "missing: " + ", ".join(missing) if missing else "all present",
    )


def check_mirrored_provider_source_indexes() -> AuditResult:
    agents_index = REPO_ROOT / ".agents" / "skills" / "provider-source-index.md"
    packaged_index = REPO_ROOT / "skills" / "provider-source-index.md"
    missing = [
        str(path.relative_to(REPO_ROOT))
        for path in [agents_index, packaged_index]
        if not path.exists()
    ]
    if missing:
        return AuditResult(
            "mirrored provider source indexes",
            False,
            "missing: " + ", ".join(missing),
        )
    ok = read_text(agents_index) == read_text(packaged_index)
    return AuditResult(
        "mirrored provider source indexes",
        ok,
        "source indexes match" if ok else "source indexes differ",
    )


def check_source_refresh_checker() -> AuditResult:
    path = REPO_ROOT / "awesome_deep_research" / "source_refresh.py"
    if not path.exists():
        return AuditResult("source refresh checker", False, "missing source_refresh.py")
    results = source_refresh.check_source_index(max_age_days=30)
    failures = [result.message for result in results if not result.ok]
    return AuditResult(
        "source refresh checker",
        not failures,
        "failures: " + ", ".join(failures) if failures else "fresh and complete",
    )


def check_readme_drift_controls() -> AuditResult:
    text = read_text(REPO_ROOT / "README.md")
    required = [
        "Pricing and model availability change frequently",
        "awesome_deep_research.source_refresh --check-links",
        "Under-$1 Benchmark Stance",
    ]
    missing = [snippet for snippet in required if snippet not in text]
    return AuditResult(
        "README drift controls",
        not missing,
        "missing: " + ", ".join(missing) if missing else "pricing drift guidance present",
    )


def check_scaffold_cleanup() -> AuditResult:
    checks = {
        "TODO.md": "# Completed Implementation Checklist",
        "pyproject.toml": "testpaths = [",
    }
    missing = [
        f"{path} missing {snippet}"
        for path, snippet in checks.items()
        if snippet not in read_text(REPO_ROOT / path)
    ]
    forbidden = {
        "TODO.md": ["# TODO"],
        "pyproject.toml": ["ADD/UPDATE THESE CONFIGURATIONS"],
    }
    lingering = [
        f"{path} contains {snippet}"
        for path, snippets in forbidden.items()
        for snippet in snippets
        if snippet in read_text(REPO_ROOT / path)
    ]
    failures = missing + lingering
    return AuditResult(
        "scaffold cleanup",
        not failures,
        "failures: " + ", ".join(failures) if failures else "starter checklist cleaned up",
    )


def check_domain_specific_guide() -> AuditResult:
    path = REPO_ROOT / "docs" / "domain-specific-deep-research.md"
    if not path.exists():
        return AuditResult("domain-specific guide", False, "missing docs/domain-specific-deep-research.md")
    text = read_text(path)
    required = [
        "Finance",
        "Medicine and life sciences",
        "General web research",
        "You.com Finance Research",
        "finance_research",
    ]
    missing = [snippet for snippet in required if snippet not in text]
    return AuditResult(
        "domain-specific guide",
        not missing,
        "missing: " + ", ".join(missing) if missing else "domain categories present",
    )


def check_api_key_signup_checklist() -> AuditResult:
    path = REPO_ROOT / "docs" / "api-key-signup-checklist.md"
    if not path.exists():
        return AuditResult("API key signup checklist", False, "missing docs/api-key-signup-checklist.md")
    text = read_text(path)
    required = [
        "op vault create awesome-deep-researchers",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "YOU_API_KEY",
        "op run --env-file .env.adr",
    ]
    missing = [snippet for snippet in required if snippet not in text]
    return AuditResult(
        "API key signup checklist",
        not missing,
        "missing: " + ", ".join(missing) if missing else "vault and key setup present",
    )


def run_audit() -> List[AuditResult]:
    return [
        check_plugin_manifest(),
        check_provider_skills(),
        check_mirrored_skill_directories(),
        check_mirrored_skill_docs(),
        check_mirrored_skill_tests(),
        check_mirrored_skill_scripts(),
        check_skill_frontmatter(),
        check_provider_skill_commands(),
        check_agents_runnable_skills(),
        check_no_compiled_python_artifacts(),
        check_env_template(),
        check_gitignore_env(),
        check_benchmark_tasks(),
        check_benchmark_cost_gate(),
        check_benchmark_command_coverage(),
        check_okf_tooling(),
        check_benchmark_auto_okf(),
        check_custom_data_benchmark_command(),
        check_provider_source_index(),
        check_mirrored_provider_source_indexes(),
        check_source_refresh_checker(),
        check_readme_drift_controls(),
        check_scaffold_cleanup(),
        check_domain_specific_guide(),
        check_file(REPO_ROOT / "docs" / "deep-research-agent.md", "deep research agent guide"),
        check_file(REPO_ROOT / "docs" / "custom-data-sources.md", "custom data source guide"),
        check_file(REPO_ROOT / "docs" / "live-benchmark-runbook.md", "live benchmark runbook"),
        check_file(REPO_ROOT / "benchmark" / "live_smoke.py", "live smoke runner"),
        check_file(REPO_ROOT / "docs" / "onepassword-env.md", "1Password setup guide"),
        check_api_key_signup_checklist(),
    ]


def format_results(results: Iterable[AuditResult]) -> str:
    lines = []
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        lines.append(f"{status}\t{result.name}\t{result.detail}")
    return "\n".join(lines)


def main() -> int:
    results = run_audit()
    print(format_results(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
