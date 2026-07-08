import sys
from pathlib import Path
from subprocess import CompletedProcess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from awesome_deep_research import op_env


def test_template_has_valid_op_references_for_core_scope():
    results = op_env.check_env_file(op_env.DEFAULT_TEMPLATE_FILE, op_env.names_for_scope("core"))

    assert all(result.ok for result in results), op_env.format_results(results)


def test_env_file_rejects_plain_secret(tmp_path: Path):
    env_file = tmp_path / ".env.adr"
    env_file.write_text("OPENAI_API_KEY=sk-plain-secret\n", encoding="utf-8")

    results = op_env.check_env_file(env_file, ["OPENAI_API_KEY"])

    assert results[0].ok is False
    assert results[0].detail == "not an op:// reference"


def test_env_file_rejects_duplicate_required_assignment(tmp_path: Path):
    env_file = tmp_path / ".env.adr"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=sk-plain-secret",
                "OPENAI_API_KEY=op://awesome-deep-researchers/api-keys/OPENAI_API_KEY",
            ]
        ),
        encoding="utf-8",
    )

    results = op_env.check_env_file(env_file, ["OPENAI_API_KEY"])

    assert results[0].ok is False
    assert results[0].detail == "duplicate assignment"


def test_env_file_rejects_whitespace_in_op_references(tmp_path: Path):
    env_file = tmp_path / ".env.adr"
    env_file.write_text(
        "OPENAI_API_KEY=op://awesome-deep-researchers/api keys/OPENAI_API_KEY\n",
        encoding="utf-8",
    )

    results = op_env.check_env_file(env_file, ["OPENAI_API_KEY"])

    assert results[0].ok is False
    assert results[0].detail == "not an op:// reference"


def test_env_file_rejects_encoded_op_reference_aliases(tmp_path: Path):
    env_file = tmp_path / ".env.adr"

    for reference in [
        "op://awesome-deep-researchers/api%2fkeys/OPENAI_API_KEY",
        "op://awesome-deep-researchers/api%3fkeys/OPENAI_API_KEY",
        "op://awesome-deep-researchers/api%23keys/OPENAI_API_KEY",
        "op://awesome-deep-researchers/api%2dkeys/OPENAI_API_KEY",
    ]:
        env_file.write_text(f"OPENAI_API_KEY={reference}\n", encoding="utf-8")

        results = op_env.check_env_file(env_file, ["OPENAI_API_KEY"])

        assert results[0].ok is False
        assert results[0].detail == "not an op:// reference"


def test_env_file_rejects_duplicate_op_references_across_required_names(tmp_path: Path):
    env_file = tmp_path / ".env.adr"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=op://awesome-deep-researchers/api-keys/SHARED",
                "TAVILY_API_KEY=op://awesome-deep-researchers/api-keys/SHARED",
            ]
        ),
        encoding="utf-8",
    )

    results = op_env.check_env_file(env_file, ["OPENAI_API_KEY", "TAVILY_API_KEY"])

    assert any(
        result.name == "op references"
        and result.ok is False
        and "duplicate references" in result.detail
        for result in results
    ), op_env.format_results(results)


def test_env_file_rejects_malformed_required_assignment_name(tmp_path: Path):
    env_file = tmp_path / ".env.adr"
    env_file.write_text(
        " OPENAI_API_KEY=op://awesome-deep-researchers/api-keys/OPENAI_API_KEY\n",
        encoding="utf-8",
    )

    results = op_env.check_env_file(env_file, ["OPENAI_API_KEY"])

    assert results[0].ok is False
    assert results[0].detail == "malformed assignment"


def test_env_file_rejects_malformed_unrequired_assignment_name(tmp_path: Path):
    env_file = tmp_path / ".env.adr"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=op://awesome-deep-researchers/api-keys/OPENAI_API_KEY",
                "bad key=op://awesome-deep-researchers/api-keys/BAD",
            ]
        ),
        encoding="utf-8",
    )

    results = op_env.check_env_file(env_file, ["OPENAI_API_KEY"])

    assert any(
        result.name == "bad key"
        and result.ok is False
        and result.detail == "malformed assignment"
        for result in results
    ), op_env.format_results(results)


def test_live_environment_reports_set_without_secret_value(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")

    results = op_env.check_live_environment(["OPENAI_API_KEY"])

    assert results[0].ok is True
    assert "secret-value" not in results[0].detail
    assert "chars" in results[0].detail


def test_scope_names_are_known_groups():
    assert "PERPLEXITY_API_KEY" in op_env.names_for_scope("commercial")
    assert "HF_TOKEN" in op_env.names_for_scope("oss")


def test_op_item_scaffold_reports_present_fields(monkeypatch):
    payload = """
    {
      "title": "api-keys",
      "vault": {"name": "awesome-deep-researchers"},
      "fields": [
        {"label": "OPENAI_API_KEY"},
        {"label": "TAVILY_API_KEY"}
      ]
    }
    """

    def fake_run(*args, **kwargs):
        return CompletedProcess(args[0], 0, stdout=payload, stderr="")

    monkeypatch.setattr(op_env.subprocess, "run", fake_run)

    results = op_env.check_op_item_scaffold(["OPENAI_API_KEY", "TAVILY_API_KEY"])

    assert all(result.ok for result in results), op_env.format_results(results)


def test_op_item_scaffold_reports_missing_fields(monkeypatch):
    payload = """
    {
      "title": "api-keys",
      "vault": {"name": "awesome-deep-researchers"},
      "fields": [{"label": "OPENAI_API_KEY"}]
    }
    """

    def fake_run(*args, **kwargs):
        return CompletedProcess(args[0], 0, stdout=payload, stderr="")

    monkeypatch.setattr(op_env.subprocess, "run", fake_run)

    results = op_env.check_op_item_scaffold(["OPENAI_API_KEY", "YOU_API_KEY"])

    assert any(result.name == "YOU_API_KEY" and not result.ok for result in results)


def test_op_item_scaffold_reports_duplicate_required_fields(monkeypatch):
    payload = """
    {
      "title": "api-keys",
      "vault": {"name": "awesome-deep-researchers"},
      "fields": [
        {"label": "OPENAI_API_KEY"},
        {"label": "OPENAI_API_KEY"}
      ]
    }
    """

    def fake_run(*args, **kwargs):
        return CompletedProcess(args[0], 0, stdout=payload, stderr="")

    monkeypatch.setattr(op_env.subprocess, "run", fake_run)

    results = op_env.check_op_item_scaffold(["OPENAI_API_KEY"])

    assert results[-1].name == "OPENAI_API_KEY"
    assert results[-1].ok is False
    assert results[-1].detail == "duplicate field"
