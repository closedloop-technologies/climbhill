import importlib.util
import json
import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_api_fanout.py"


def load_fanout_module():
    spec = importlib.util.spec_from_file_location("run_api_fanout", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fanout_writes_response_files_and_summary(monkeypatch, tmp_path):
    fanout = load_fanout_module()
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily")
    monkeypatch.setenv("EXA_API_KEY", "test-exa")

    def fake_run(argv, **kwargs):
        provider = "unknown"
        if "tavily_search.py" in " ".join(argv):
            provider = "tavily"
        if "exa_tools.py" in " ".join(argv):
            provider = "exa"
        return CompletedProcess(argv, 0, stdout=f"{provider} response", stderr=f"{provider} stderr")

    monkeypatch.setattr(fanout.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_api_fanout.py",
            "--output-dir",
            str(tmp_path),
            "--providers",
            "deep-research-tavily,deep-research-exa",
            "compare deep research providers",
        ],
    )

    assert fanout.main() == 0

    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert (run_dir / "deep-research-tavily.response.txt").read_text(encoding="utf-8") == "tavily response"
    assert (run_dir / "deep-research-exa.response.txt").read_text(encoding="utf-8") == "exa response"

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["prompt"] == "compare deep research providers"
    assert {result["provider"] for result in summary["results"]} == {"deep-research-tavily", "deep-research-exa"}
    assert all(result["returncode"] == 0 for result in summary["results"])


def test_fanout_skips_missing_env_without_running_provider(monkeypatch, tmp_path):
    fanout = load_fanout_module()
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

    def fake_run(*args, **kwargs):
        raise AssertionError("provider command should not run when env is missing")

    monkeypatch.setattr(fanout.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_api_fanout.py",
            "--output-dir",
            str(tmp_path),
            "--providers",
            "deep-research-perplexity",
            "test prompt",
        ],
    )

    assert fanout.main() == 0

    run_dir = next(tmp_path.iterdir())
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["results"][0]["provider"] == "deep-research-perplexity"
    assert summary["results"][0]["skipped"] is True
    assert "PERPLEXITY_API_KEY" in (run_dir / "deep-research-perplexity.stderr.txt").read_text(encoding="utf-8")


def test_parse_providers_rejects_duplicates():
    fanout = load_fanout_module()

    with pytest.raises(ValueError, match="duplicate providers: deep-research-tavily"):
        fanout.parse_providers(["deep-research-tavily,deep-research-exa", "deep-research-tavily"])
