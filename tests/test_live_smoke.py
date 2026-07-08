import sys
import subprocess
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark import live_smoke


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_missing_env_for_skill_reports_unset_required_env(monkeypatch):
    monkeypatch.delenv("YOU_API_KEY", raising=False)

    assert live_smoke.missing_env_for_skill("deep-research-you") == ["YOU_API_KEY"]


def test_select_ready_skills_skips_missing_env(monkeypatch):
    monkeypatch.delenv("YOU_API_KEY", raising=False)

    selected, skipped = live_smoke.select_ready_skills(
        ["deep-research-you"],
        available_skills=["deep-research-you"],
    )

    assert selected == []
    assert skipped == ["deep-research-you: missing YOU_API_KEY"]


def test_select_ready_skills_requires_jina_env(monkeypatch):
    monkeypatch.delenv("JINA_API_KEY", raising=False)

    selected, skipped = live_smoke.select_ready_skills(
        ["deep-research-jina"],
        available_skills=["deep-research-jina"],
    )

    assert selected == []
    assert skipped == ["deep-research-jina: missing JINA_API_KEY"]


def test_select_ready_skills_reports_undiscovered_skill():
    selected, skipped = live_smoke.select_ready_skills(
        ["missing-skill"],
        available_skills=[],
    )

    assert selected == []
    assert skipped == ["missing-skill: not discovered"]


def test_select_ready_skills_can_fail_on_missing_env(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="deep-research-gemini: missing GOOGLE_API_KEY"):
        live_smoke.select_ready_skills(
            ["deep-research-gemini"],
            available_skills=["deep-research-gemini"],
            fail_missing_env=True,
        )


def test_live_smoke_script_runs_when_invoked_as_file():
    result = subprocess.run(
        [
            sys.executable,
            "benchmark/live_smoke.py",
            "--skills",
            "missing-skill",
            "--output-dir",
            "/tmp/adr-live-smoke-test",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing-skill: not discovered" in result.stderr
    assert "ImportError" not in result.stderr
