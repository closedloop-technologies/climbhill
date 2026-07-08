import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.benchmark import BenchmarkRunner
from benchmark.tracker import BenchmarkMetrics


def test_extract_cost_from_output_detects_provider_cost():
    assert BenchmarkMetrics.extract_cost_from_output("total_cost: $0.42") == 0.42
    assert BenchmarkMetrics.extract_cost_from_output("Cost: $1.23") == 1.23


def test_run_skill_fails_when_provider_reported_cost_exceeds_budget(tmp_path: Path):
    script = tmp_path / "expensive_skill.py"
    script.write_text("print('total_cost: $1.25\\nreport')\n", encoding="utf-8")

    runner = BenchmarkRunner(output_dir=tmp_path / "results")
    metrics = runner.run_skill(
        {
            "name": "expensive-test-skill",
            "script_path": str(script),
            "command": "python {script}",
        },
        "Test prompt",
        "Budget",
    )

    assert metrics.success is False
    assert "Cost budget exceeded" in metrics.error
    assert metrics.metadata["within_cost_budget"] is False


def test_run_skill_can_record_over_budget_when_allowed(tmp_path: Path):
    script = tmp_path / "expensive_skill.py"
    script.write_text("print('actual_cost = 1.25')\n", encoding="utf-8")

    runner = BenchmarkRunner(output_dir=tmp_path / "results", enforce_cost_budget=False)
    metrics = runner.run_skill(
        {
            "name": "expensive-test-skill",
            "script_path": str(script),
            "command": "python {script}",
        },
        "Test prompt",
        "Budget",
    )

    assert metrics.success is True
    assert metrics.estimated_cost_usd == 1.25
    assert metrics.metadata["within_cost_budget"] is False


def test_save_individual_result_creates_valid_okf_bundle(tmp_path: Path):
    runner = BenchmarkRunner(output_dir=tmp_path / "results")
    metrics = runner.tracker.create_run(
        skill_name="sample-skill",
        category="Repository Refresh & Meta Research",
        question="Deepresearch the deepresearchers"
    )
    metrics.start()
    metrics.set_output("- Finding with source https://example.com\n- This may be stale.")
    metrics.add_metadata("provider", "sample")
    metrics.add_metadata("model", "sample-model")
    metrics.end()

    runner.save_individual_result(metrics, "sample-skill", "Repository Refresh & Meta Research", 0)

    okf_bundle = Path(metrics.metadata["okf_bundle_dir"])
    assert metrics.metadata["okf_valid"] is True
    assert (okf_bundle / "report.md").exists()
    assert (okf_bundle / "findings.md").exists()
    assert (okf_bundle / "uncertainties.md").exists()
