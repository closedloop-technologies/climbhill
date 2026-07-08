import re
from pathlib import Path

import pytest

from awesome_deep_research.alignment import inspect_repo
from awesome_deep_research import cli
from awesome_deep_research.cli import PromptExample
from awesome_deep_research.policy import check_paths, load_policy
from awesome_deep_research.policy import paths_from_patch
from awesome_deep_research.registry import Registry
from awesome_deep_research.resources import add_resource, search_resources


def test_load_prompt_examples_contains_expected_ids():
    prompts = cli.load_prompt_examples()
    assert prompts, "Expected at least one prompt example from taxonomy file"

    prompt_ids = {prompt.identifier for prompt in prompts}
    assert "domain-mapping-01" in prompt_ids
    assert "source-retrieval-01" in prompt_ids


def test_next_output_path_increments(tmp_path: Path):
    first = cli.next_output_path(tmp_path, "perplexity-sonar")
    assert first.name == "OUTPUT-PERPLEXITY-SONAR-0001.md"
    first.write_text("dummy", encoding="utf-8")

    second = cli.next_output_path(tmp_path, "perplexity-sonar")
    assert second.name == "OUTPUT-PERPLEXITY-SONAR-0002.md"


def test_build_user_prompt_includes_extra_instructions():
    prompt = PromptExample(identifier="custom", category="Domain Mapping", text="Analyze the domain.")
    extra = "Prioritize regulatory perspectives."

    user_prompt = cli.build_user_prompt(prompt, extra)

    assert "## Additional Instructions" in user_prompt
    assert extra in user_prompt
    assert re.search(r"Domain Mapping", user_prompt)


@pytest.mark.parametrize("mode", ["default", "relative", "absolute"])
def test_ensure_output_dir_creates_directories(tmp_path: Path, monkeypatch, mode: str):
    monkeypatch.setattr(cli, "DEFAULT_OUTPUT_DIR", tmp_path / "default")

    if mode == "default":
        requested = None
    elif mode == "relative":
        requested = str(Path("outputs-test"))
    else:
        requested = str((tmp_path / "absolute").resolve())

    output_dir = cli.ensure_output_dir(requested)
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_init_creates_alignment_files_and_registry(tmp_path: Path):
    result = cli.main(["init", "--repo", str(tmp_path)])

    assert result == 0
    assert (tmp_path / "goal.md").exists()
    assert (tmp_path / ".climbhill" / "policy.yaml").exists()
    assert (tmp_path / ".climbhill" / "eval.yaml").exists()
    assert (tmp_path / ".climbhill" / "registry.local.sqlite").exists()
    assert (tmp_path / ".github" / "pull_request_template.md").exists()
    assert (tmp_path / "resources" / "postmortems").is_dir()

    report = inspect_repo(tmp_path)
    assert "goal.md" in report.present
    assert ".climbhill/policy.yaml" in report.present


def test_policy_check_classifies_allowed_denied_and_approval_paths(tmp_path: Path):
    cli.main(["init", "--repo", str(tmp_path)])
    policy = load_policy(tmp_path / ".climbhill" / "policy.yaml")

    results = check_paths(["src/app.py", "tests/test_app.py", ".env"], policy)

    assert [result.classification for result in results] == [
        "allowed",
        "requires_approval",
        "denied",
    ]


def test_policy_check_accepts_patch_files(tmp_path: Path):
    cli.main(["init", "--repo", str(tmp_path)])
    patch = tmp_path / "candidate.patch"
    patch.write_text(
        "\n".join(
            [
                "diff --git a/src/app.py b/src/app.py",
                "--- a/src/app.py",
                "+++ b/src/app.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "diff --git a/.env b/.env",
                "--- a/.env",
                "+++ b/.env",
            ]
        ),
        encoding="utf-8",
    )

    assert paths_from_patch(patch.read_text(encoding="utf-8")) == ["src/app.py", ".env"]
    assert cli.main(["policy", "check", "--repo", str(tmp_path), "--patch-file", str(patch)]) == 3


def test_registry_and_report_flow(tmp_path: Path):
    cli.main(["init", "--repo", str(tmp_path)])

    assert cli.main(["registry", "--repo", str(tmp_path), "create-run", "--goal", "Improve docs"]) == 0
    assert (
        cli.main(
            [
                "registry",
                "--repo",
                str(tmp_path),
                "register-candidate",
                "--run-id",
                "1",
                "--summary",
                "Documented setup",
                "--branch",
                "climbhill/run-1/candidate-1",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "registry",
                "--repo",
                str(tmp_path),
                "record-evaluation",
                "--candidate-id",
                "1",
                "--type",
                "test",
                "--status",
                "passed",
                "--command",
                "pytest",
            ]
        )
        == 0
    )

    report_path = tmp_path / ".climbhill" / "reports" / "run-1.md"
    assert cli.main(["report", "--repo", str(tmp_path), "--run-id", "1"]) == 0
    report = report_path.read_text(encoding="utf-8")
    assert "# ClimbHill Run 1 Report" in report
    assert "Improve docs" in report
    assert "Documented setup" in report
    assert "pytest" in report


def test_run_compare_cost_lineage_decision_and_reflect_flow(tmp_path: Path):
    cli.main(["init", "--repo", str(tmp_path)])

    assert (
        cli.main(
            [
                "run",
                "--repo",
                str(tmp_path),
                "--goal",
                "Improve policy docs",
                "--candidates",
                "2",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "registry",
                "--repo",
                str(tmp_path),
                "record-evaluation",
                "--candidate-id",
                "1",
                "--type",
                "test",
                "--status",
                "failed",
                "--failure-reason",
                "Missing policy tests",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "registry",
                "--repo",
                str(tmp_path),
                "record-evaluation",
                "--candidate-id",
                "2",
                "--type",
                "test",
                "--status",
                "passed",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "registry",
                "--repo",
                str(tmp_path),
                "record-cost",
                "--run-id",
                "1",
                "--agent",
                "codex",
                "--model",
                "gpt-5",
                "--input-tokens",
                "100",
                "--output-tokens",
                "50",
                "--estimated-usd",
                "0.03",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "registry",
                "--repo",
                str(tmp_path),
                "record-lineage",
                "--candidate-id",
                "2",
                "--relationship",
                "inspired_by",
                "--related-candidate-id",
                "1",
                "--note",
                "Kept docs idea but fixed test gap.",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "decision",
                "--repo",
                str(tmp_path),
                "--run-id",
                "1",
                "--candidate-id",
                "2",
                "--type",
                "promote",
                "--rationale",
                "Only passing candidate.",
                "--actor",
                "maintainer",
            ]
        )
        == 0
    )

    assert cli.main(["compare", "--repo", str(tmp_path), "--run-id", "1"]) == 0
    assert cli.main(["history", "--repo", str(tmp_path), "sample", "--query", "policy"]) == 0
    assert cli.main(["reflect", "--repo", str(tmp_path), "--run-id", "1"]) == 0
    assert cli.main(["report", "--repo", str(tmp_path), "--run-id", "1"]) == 0

    issue_files = list((tmp_path / ".climbhill" / "issue-proposals").glob("issue-*.md"))
    assert issue_files
    report = (tmp_path / ".climbhill" / "reports" / "run-1.md").read_text(encoding="utf-8")
    assert "## Costs" in report
    assert "## Candidate Lineage" in report
    assert "## Human Decisions" in report
    assert "Candidate 2" in report


def test_resource_add_and_search(tmp_path: Path):
    path = add_resource(
        tmp_path,
        "Useful Failure Pattern",
        summary="Candidates repeatedly forgot policy checks before editing tests.",
        source="run report",
        author="Maintainer",
        date="2026-07-08",
        path_or_url="reports/run-1.md",
        tags="policy,tests",
        reason="Prevent repeated unsafe edits.",
    )

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "- Author: Maintainer" in content
    assert "- Date: 2026-07-08" in content
    assert "- Path or URL: reports/run-1.md" in content
    matches = search_resources(tmp_path, "policy")
    assert len(matches) == 1
    assert matches[0].title == "Useful Failure Pattern"


def test_registry_records_decisions_and_issue_proposals(tmp_path: Path):
    registry = Registry(tmp_path / ".climbhill" / "registry.local.sqlite")
    try:
        run_id = registry.create_run("Improve safety docs", tmp_path)
        candidate_id = registry.register_candidate(run_id, "Add policy examples")
        lineage_id = registry.record_lineage(
            candidate_id,
            "inspired_by",
            note="Based on a prior failed candidate.",
        )
        cost_id = registry.record_cost(
            run_id=run_id,
            candidate_id=candidate_id,
            agent="codex",
            model="gpt-5",
            estimated_usd=0.01,
        )
        decision_id = registry.record_decision(
            run_id,
            "reject",
            candidate_id=candidate_id,
            rationale="Needs stronger tests.",
            actor="maintainer",
        )
        issue_id = registry.propose_issue(
            "Add policy matcher tests",
            "Policy matching needs more edge-case coverage.",
            labels="testing,policy",
            priority="high",
            evidence="candidate failed due to missing path coverage",
            source_run_ids=str(run_id),
            source_candidate_ids=str(candidate_id),
        )
    finally:
        registry.close()

    assert lineage_id == 1
    assert cost_id == 1
    assert decision_id == 1
    assert issue_id == 1


def test_mcp_tool_surface_when_sdk_is_available():
    pytest.importorskip("mcp")
    import anyio
    import awesome_deep_research.mcp_server as server

    async def check_tools():
        tools = await server.mcp.list_tools()
        names = {tool.name for tool in tools}
        required = {
            "climbhill.repo.inspect",
            "climbhill.repo.align",
            "climbhill.policy.read",
            "climbhill.policy.check_patch",
            "climbhill.resources.search",
            "climbhill.resources.add",
            "climbhill.runs.create",
            "climbhill.runs.get",
            "climbhill.runs.list",
            "climbhill.candidates.register",
            "climbhill.candidates.attach_patch",
            "climbhill.candidates.evaluate",
            "climbhill.candidates.compare",
            "climbhill.candidates.record_lineage",
            "climbhill.costs.record",
            "climbhill.history.sample",
            "climbhill.reports.generate",
            "climbhill.decisions.record",
            "climbhill.issues.propose",
        }
        assert required <= names
        _, structured = await server.mcp.call_tool("climbhill.repo.inspect", {"repo": "."})
        assert structured["result"]["aligned"] is True

    anyio.run(check_tools)
