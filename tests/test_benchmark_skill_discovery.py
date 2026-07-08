import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.utils import (
    discover_skills,
    find_unregistered_benchmark_skills,
    get_skill_command_info,
    parse_taxonomy_questions,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROVIDER_SKILLS = {
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
OP_EXAMPLE_SKILLS = PROVIDER_SKILLS - {"deep-research-custom-data"}


def test_discover_skills_includes_agents_skills():
    skills = discover_skills()
    names = {skill["name"] for skill in skills}

    assert "deep-research-okf-normalize" in names
    assert "deep-research-you" in names
    assert "deep-research-gemini" in names

    okf_skill = next(skill for skill in skills if skill["name"] == "deep-research-okf-normalize")
    assert okf_skill["script_path"].endswith("normalize_to_okf.py")


def test_okf_normalizer_command_is_registered():
    command_info = get_skill_command_info("deep-research-okf-normalize")

    assert "--bundle-dir" in command_info["command"]
    assert "{question_slug}" in command_info["command"]
    assert command_info["supports_query"] is True


def test_custom_data_manifest_validator_command_is_registered():
    command_info = get_skill_command_info("deep-research-custom-data")

    assert "custom-data-corpus.example.json" in command_info["command"]
    assert command_info["supports_query"] is False


def test_all_discovered_skills_have_explicit_benchmark_commands():
    assert find_unregistered_benchmark_skills() == []


def test_unknown_skill_does_not_get_implicit_benchmark_fallback():
    with pytest.raises(KeyError):
        get_skill_command_info("new-unregistered-skill")


def test_you_and_gemini_commands_are_registered_for_under_one_dollar_defaults():
    you_command = get_skill_command_info("deep-research-you")["command"]
    gemini_command = get_skill_command_info("deep-research-gemini")["command"]

    assert "--research-effort lite" in you_command
    assert "--mode grounded" in gemini_command


def test_agents_provider_guides_exist_with_plugin_mirror():
    for skill_name in PROVIDER_SKILLS:
        agents_skill = REPO_ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
        plugin_skill = REPO_ROOT / "skills" / skill_name / "SKILL.md"

        assert agents_skill.exists(), f"Missing .agents skill for {skill_name}"
        assert plugin_skill.exists(), f"Missing plugin skill mirror for {skill_name}"
        if skill_name in OP_EXAMPLE_SKILLS:
            assert "op run --env-file .env.adr" in agents_skill.read_text(encoding="utf-8")


def test_taxonomy_includes_requested_canonical_tasks():
    questions = parse_taxonomy_questions()
    flattened = "\n".join(question for items in questions.values() for question in items)

    assert "Deepresearch the deepresearchers" in flattened
    assert "AI-for-science" in flattened
    assert "under $1" in flattened


def test_onepassword_setup_doc_lists_required_provider_keys():
    doc = (REPO_ROOT / "docs" / "onepassword-env.md").read_text(encoding="utf-8")

    for env_name in [
        "OPENAI_API_KEY",
        "PERPLEXITY_API_KEY",
        "EXA_API_KEY",
        "TAVILY_API_KEY",
        "JINA_API_KEY",
        "XAI_API_KEY",
        "YOU_API_KEY",
        "GOOGLE_API_KEY",
    ]:
        assert env_name in doc
