from __future__ import annotations

from pathlib import Path

from .registry import Registry


def generate_markdown_report(registry: Registry, run_id: int, output_path: Path) -> str:
    run = registry.get_run(run_id)
    if run is None:
        raise KeyError(f"Run {run_id} was not found.")

    candidates = registry.list_candidates(run_id)
    evaluations = registry.list_evaluations_for_candidates(candidate.id for candidate in candidates)
    costs = registry.list_costs(run_id)
    decisions = registry.list_decisions(run_id)
    lineage = registry.list_lineage(run_id)
    comparison = registry.compare_candidates(run_id)

    lines = [
        f"# ClimbHill Run {run.id} Report",
        "",
        "## Goal",
        "",
        run.goal,
        "",
        "## Repo State",
        "",
        f"- Repository path: `{run.repo_path}`",
        f"- Base commit: `{run.base_commit or 'unknown'}`",
        f"- Run status: `{run.status}`",
        f"- Created: `{run.created_at}`",
        "",
        "## Policy Summary",
        "",
        "- Protected files require policy checks before promotion.",
        "- Tests, evals, CI workflows, infrastructure, security-sensitive code, and policy relaxation require human approval by default.",
        "- A candidate is not promotion-ready until required checks pass and a human decision is recorded.",
        "",
        "## Candidates",
        "",
    ]

    if candidates:
        lines.extend(
            [
                "| Candidate | Status | Branch | Head Commit | Summary |",
                "|-----------|--------|--------|-------------|---------|",
            ]
        )
        for candidate in candidates:
            lines.append(
                "| "
                f"{candidate.id} | {candidate.status} | {candidate.branch or '-'} | "
                f"{candidate.head_commit or '-'} | {candidate.summary} |"
            )
    else:
        lines.append("No candidates were registered.")

    lines.extend(["", "## Evaluations", ""])
    if evaluations:
        lines.extend(
            [
                "| Candidate | Type | Status | Score | Command | Failure Reason |",
                "|-----------|------|--------|-------|---------|----------------|",
            ]
        )
        for evaluation in evaluations:
            score = "" if evaluation["score"] is None else str(evaluation["score"])
            lines.append(
                "| "
                f"{evaluation['candidate_id']} | {evaluation['type']} | {evaluation['status']} | "
                f"{score or '-'} | {evaluation['command'] or '-'} | {evaluation['failure_reason'] or '-'} |"
            )
    else:
        lines.append("No evaluations were recorded.")

    lines.extend(["", "## Candidate Comparison", ""])
    if comparison:
        lines.extend(
            [
                "| Rank | Candidate | Passing Evaluations | Failing Evaluations | Summary |",
                "|------|-----------|---------------------|---------------------|---------|",
            ]
        )
        for index, candidate in enumerate(comparison, start=1):
            lines.append(
                "| "
                f"{index} | {candidate['id']} | {candidate['passing_evaluations']} | "
                f"{candidate['failing_evaluations']} | {candidate['summary']} |"
            )
    else:
        lines.append("No candidates are available to compare.")

    lines.extend(["", "## Costs", ""])
    if costs:
        lines.extend(
            [
                "| Scope | Agent | Model | Input Tokens | Output Tokens | Tool Calls | Wall Time | Estimated USD |",
                "|-------|-------|-------|--------------|---------------|------------|-----------|---------------|",
            ]
        )
        for cost in costs:
            scope = f"candidate {cost.candidate_id}" if cost.candidate_id else f"run {cost.run_id}"
            lines.append(
                "| "
                f"{scope} | {cost.agent or '-'} | {cost.model or '-'} | "
                f"{cost.input_tokens if cost.input_tokens is not None else '-'} | "
                f"{cost.output_tokens if cost.output_tokens is not None else '-'} | "
                f"{cost.tool_calls if cost.tool_calls is not None else '-'} | "
                f"{cost.wall_clock_seconds if cost.wall_clock_seconds is not None else '-'} | "
                f"{cost.estimated_usd if cost.estimated_usd is not None else '-'} |"
            )
    else:
        lines.append("No costs were recorded.")

    lines.extend(["", "## Candidate Lineage", ""])
    if lineage:
        lines.extend(
            [
                "| Candidate | Relationship | Related Candidate | Note |",
                "|-----------|--------------|-------------------|------|",
            ]
        )
        for item in lineage:
            lines.append(
                "| "
                f"{item.candidate_id} | {item.relationship} | {item.related_candidate_id or '-'} | "
                f"{item.note or '-'} |"
            )
    else:
        lines.append("No candidate lineage was recorded.")

    lines.extend(["", "## Human Decisions", ""])
    if decisions:
        lines.extend(
            [
                "| Decision | Candidate | Actor | Rationale | Created |",
                "|----------|-----------|-------|-----------|---------|",
            ]
        )
        for decision in decisions:
            lines.append(
                "| "
                f"{decision.decision_type} | {decision.candidate_id or '-'} | "
                f"{decision.actor or '-'} | {decision.rationale or '-'} | {decision.created_at} |"
            )
    else:
        lines.append("No human decisions were recorded.")

    recommendation = "Review candidates and record a human promotion or rejection decision."
    if comparison:
        best = comparison[0]
        if best["failing_evaluations"] == 0 and best["passing_evaluations"] > 0:
            recommendation = f"Candidate {best['id']} is the highest-ranked candidate without recorded failing evaluations."
        else:
            recommendation = "No candidate is ready for promotion; all evaluated candidates have failures."

    lines.extend(
        [
            "",
            "## Risks",
            "",
            "- Confirm protected paths were not edited without approval.",
            "- Confirm tests and evals were not modified to mask regressions.",
            "- Confirm costs and tool usage were recorded when available.",
            "- Confirm a human decision exists before PR promotion, merge, or deployment.",
            "",
            "## Recommendation",
            "",
            recommendation,
            "",
            "## Next Actions",
            "",
            "- Record a human decision.",
            "- Promote the chosen candidate to a PR-ready branch or reject all candidates with reasons.",
            "- Run meta-analysis if repeated failures reveal missing docs, weak tests, or policy gaps.",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    registry.record_report(run_id, output_path, summary=run.goal, recommendation=recommendation)
    return content
