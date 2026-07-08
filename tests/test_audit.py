import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from awesome_deep_research import audit


def test_audit_passes_current_repo_requirements():
    results = audit.run_audit()

    assert results
    assert all(result.ok for result in results), audit.format_results(results)


def test_audit_covers_goal_critical_checks():
    names = {result.name for result in audit.run_audit()}

    assert "codex plugin manifest" in names
    assert "provider skill docs" in names
    assert "mirrored skill directories" in names
    assert "mirrored skill docs" in names
    assert "mirrored skill tests" in names
    assert "mirrored skill scripts" in names
    assert "skill frontmatter" in names
    assert "provider op command examples" in names
    assert "agents runnable skill scripts" in names
    assert "compiled Python artifacts" in names
    assert "1Password env template" in names
    assert "env secret ignore" in names
    assert "canonical benchmark tasks" in names
    assert "under-$1 benchmark gate" in names
    assert "benchmark command coverage" in names
    assert "OKF tooling" in names
    assert "benchmark OKF normalization" in names
    assert "custom data benchmark command" in names
    assert "provider source index" in names
    assert "mirrored provider source indexes" in names
    assert "custom data source guide" in names
    assert "live benchmark runbook" in names
    assert "live smoke runner" in names
    assert "source refresh checker" in names
    assert "README drift controls" in names
    assert "scaffold cleanup" in names
    assert "domain-specific guide" in names
    assert "API key signup checklist" in names


def test_compiled_artifact_audit_scans_all_tracked_files(monkeypatch):
    class Result:
        stdout = "awesome_deep_research/__pycache__/audit.cpython-313.pyc\n"

    def fake_run(*args, **kwargs):
        assert args[0] == ["git", "ls-files"]
        return Result()

    monkeypatch.setattr(audit.subprocess, "run", fake_run)

    result = audit.check_no_compiled_python_artifacts()

    assert result.ok is False
    assert result.name == "compiled Python artifacts"
    assert "awesome_deep_research/__pycache__/audit.cpython-313.pyc" in result.detail


def test_readme_mentions_op_env_checker():
    readme = (audit.REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "awesome_deep_research.op_env --template" in readme


def test_custom_data_source_guide_covers_requested_sources():
    guide = (audit.REPO_ROOT / "docs" / "custom-data-sources.md").read_text(encoding="utf-8")
    skill = (
        audit.REPO_ROOT / ".agents" / "skills" / "deep-research-custom-data" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for term in ["Google Docs", "YouTube", "Local files", "S3", "arXiv"]:
        assert term in guide
        assert term in skill

    assert "validate_manifest.py" in guide
    assert "validate_manifest.py" in skill
