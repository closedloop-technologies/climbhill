from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .preparedness import initialize_repo, inspect_preparedness
from .cli import current_commit, registry_path
from .policy import check_paths, load_policy, policy_allows_promotion
from .registry import Registry
from .reports import generate_markdown_report
from .resources import add_resource, search_resources
from .deep_research_mcp_server import (
    build_fastmcp_server,
    deep_research,
    forward_event_to_context,
    list_providers,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - depends on optional runtime install
    raise SystemExit(
        "The ClimbHill MCP server requires the Python MCP SDK. "
        'Install with: pip install "mcp[cli]>=1.27,<2"'
    ) from exc


mcp = FastMCP("climbhill-ai", json_response=True)


def _repo(repo: str) -> Path:
    return Path(repo).resolve()


@mcp.tool(name="climbhill.repo.prepare")
def repo_prepare(repo: str = ".", apply: bool = False) -> Dict[str, Any]:
    """Report or create missing ClimbHill repository support files."""
    repo_path = _repo(repo)
    before = inspect_preparedness(repo_path)
    created: List[str] = []
    if apply and before.missing:
        created = [str(path.relative_to(repo_path)) for path in initialize_repo(repo_path)]
    after = inspect_preparedness(repo_path)
    return {
        "repo_path": str(repo_path),
        "applied": apply,
        "created": created,
        "prepared": after.is_prepared,
        "present": after.present,
        "missing": after.missing,
        "git_remote": after.git_remote,
        "current_commit": after.current_commit,
    }


@mcp.tool(name="climbhill.policy.read")
def policy_read(repo: str = ".") -> Dict[str, Any]:
    """Read the active ClimbHill policy."""
    repo_path = _repo(repo)
    policy_path = repo_path / ".climbhill" / "policy.yaml"
    return {"path": str(policy_path), "policy": load_policy(policy_path)}


@mcp.tool(name="climbhill.policy.check_patch")
def policy_check_patch(paths: List[str], repo: str = ".") -> Dict[str, Any]:
    """Classify changed paths against the active ClimbHill policy."""
    repo_path = _repo(repo)
    policy = load_policy(repo_path / ".climbhill" / "policy.yaml")
    results = check_paths(paths, policy)
    return {
        "allowed_for_promotion": policy_allows_promotion(results),
        "results": [
            {
                "path": result.path,
                "classification": result.classification,
                "matched_pattern": result.matched_pattern,
            }
            for result in results
        ],
    }


@mcp.tool(name="climbhill.runs.create")
def runs_create(goal: str, repo: str = ".", registry: Optional[str] = None) -> Dict[str, Any]:
    """Create a bounded improvement run in the local registry."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        run_id = store.create_run(goal, repo_path, base_commit=current_commit(repo_path))
        return {"run_id": run_id, "registry": str(database)}
    finally:
        store.close()


@mcp.tool(name="climbhill.runs.list")
def runs_list(repo: str = ".", registry: Optional[str] = None) -> Dict[str, Any]:
    """List recorded ClimbHill runs."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        return {
            "registry": str(database),
            "runs": [run.__dict__ for run in store.list_runs()],
        }
    finally:
        store.close()


@mcp.tool(name="climbhill.runs.get")
def runs_get(run_id: int, repo: str = ".", registry: Optional[str] = None) -> Dict[str, Any]:
    """Get a recorded ClimbHill run."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        run = store.get_run(run_id)
        return {"registry": str(database), "run": run.__dict__ if run else None}
    finally:
        store.close()


@mcp.tool(name="climbhill.attempts.register")
def attempts_register(
    run_id: int,
    summary: str,
    repo: str = ".",
    registry: Optional[str] = None,
    branch: str = "",
    base_commit: str = "",
    head_commit: str = "",
    patch_path: str = "",
    status: str = "registered",
) -> Dict[str, Any]:
    """Register an improvement Attempt."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        attempt_id = store.register_attempt(
            run_id,
            summary,
            branch=branch,
            base_commit=base_commit,
            head_commit=head_commit,
            patch_path=patch_path,
            status=status,
        )
        return {"attempt_id": attempt_id, "registry": str(database)}
    finally:
        store.close()


@mcp.tool(name="climbhill.attempts.attach_patch")
def attempts_attach_patch(
    attempt_id: int,
    patch_path: str,
    repo: str = ".",
    registry: Optional[str] = None,
    head_commit: str = "",
    status: str = "patched",
) -> Dict[str, Any]:
    """Attach a patch path and optional head commit to an Attempt."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        store.attach_attempt_patch(
            attempt_id,
            patch_path=patch_path,
            head_commit=head_commit,
            status=status,
        )
        return {"attempt_id": attempt_id, "registry": str(database), "patch_path": patch_path}
    finally:
        store.close()


@mcp.tool(name="climbhill.attempts.evaluate")
def attempts_evaluate(
    attempt_id: int,
    evaluation_type: str,
    status: str,
    repo: str = ".",
    registry: Optional[str] = None,
    command: str = "",
    score: Optional[float] = None,
    logs_path: str = "",
    failure_reason: str = "",
) -> Dict[str, Any]:
    """Record an Attempt evaluation result."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        evaluation_id = store.record_evaluation(
            attempt_id,
            evaluation_type,
            status,
            command=command,
            score=score,
            logs_path=logs_path,
            failure_reason=failure_reason,
        )
        return {"evaluation_id": evaluation_id, "registry": str(database)}
    finally:
        store.close()


@mcp.tool(name="climbhill.attempts.record_lineage")
def attempts_record_lineage(
    attempt_id: int,
    relationship: str,
    repo: str = ".",
    registry: Optional[str] = None,
    related_attempt_id: Optional[int] = None,
    note: str = "",
) -> Dict[str, Any]:
    """Record an explicit attempt lineage relationship."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        lineage_id = store.record_lineage(
            attempt_id,
            relationship,
            related_attempt_id=related_attempt_id,
            note=note,
        )
        return {"lineage_id": lineage_id, "registry": str(database)}
    finally:
        store.close()


@mcp.tool(name="climbhill.costs.record")
def costs_record(
    repo: str = ".",
    registry: Optional[str] = None,
    run_id: Optional[int] = None,
    attempt_id: Optional[int] = None,
    agent: str = "",
    model: str = "",
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    tool_calls: Optional[int] = None,
    wall_clock_seconds: Optional[float] = None,
    estimated_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Record run or attempt cost information."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        cost_id = store.record_cost(
            run_id=run_id,
            attempt_id=attempt_id,
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_calls=tool_calls,
            wall_clock_seconds=wall_clock_seconds,
            estimated_usd=estimated_usd,
        )
        return {"cost_id": cost_id, "registry": str(database)}
    finally:
        store.close()


@mcp.tool(name="climbhill.attempts.compare")
def attempts_compare(run_id: int, repo: str = ".", registry: Optional[str] = None) -> Dict[str, Any]:
    """Compare Attempts in a Run using recorded evaluation outcomes."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        ranked = store.compare_attempts(run_id)
        return {
            "registry": str(database),
            "attempts": ranked,
            "recommended_attempt_id": ranked[0]["id"] if ranked else None,
        }
    finally:
        store.close()


@mcp.tool(name="climbhill.history.sample")
def history_sample(query: str = "", repo: str = ".", registry: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """Sample recent historical attempts, optionally filtered by summary text."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        matches = []
        query_lower = query.lower()
        for run in store.list_runs():
            for attempt in store.list_attempts(run.id):
                if query_lower and query_lower not in attempt.summary.lower() and query_lower not in run.goal.lower():
                    continue
                matches.append({"run": run.__dict__, "attempt": attempt.__dict__})
                if len(matches) >= limit:
                    return {"registry": str(database), "matches": matches}
        return {"registry": str(database), "matches": matches}
    finally:
        store.close()


@mcp.tool(name="climbhill.resources.search")
def resources_search(query: str, repo: str = ".", limit: int = 10) -> Dict[str, Any]:
    """Search ClimbHill resource markdown files."""
    repo_path = _repo(repo)
    return {
        "matches": [match.__dict__ for match in search_resources(repo_path, query, limit=limit)]
    }


@mcp.tool(name="climbhill.resources.add")
def resources_add(
    title: str,
    summary: str,
    repo: str = ".",
    source: str = "",
    author: str = "",
    date: str = "",
    path_or_url: str = "",
    resource_type: str = "user-guidance",
    trust_level: str = "experimental",
    tags: str = "",
    reason: str = "",
) -> Dict[str, Any]:
    """Add a metadata-rich markdown resource."""
    repo_path = _repo(repo)
    path = add_resource(
        repo_path,
        title,
        summary=summary,
        source=source,
        author=author,
        date=date,
        path_or_url=path_or_url,
        resource_type=resource_type,
        trust_level=trust_level,
        tags=tags,
        reason=reason,
    )
    return {"path": str(path.relative_to(repo_path))}


@mcp.tool(name="climbhill.reports.generate")
def reports_generate(
    run_id: int,
    repo: str = ".",
    registry: Optional[str] = None,
    output: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a Markdown report for a ClimbHill run."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    output_path = Path(output) if output else repo_path / ".climbhill" / "reports" / f"run-{run_id}.md"
    if not output_path.is_absolute():
        output_path = repo_path / output_path
    store = Registry(database)
    try:
        content = generate_markdown_report(store, run_id, output_path)
        return {"path": str(output_path), "bytes": len(content.encode("utf-8"))}
    finally:
        store.close()


@mcp.tool(name="climbhill.decisions.record")
def decisions_record(
    run_id: int,
    decision_type: str,
    repo: str = ".",
    registry: Optional[str] = None,
    attempt_id: Optional[int] = None,
    rationale: str = "",
    actor: str = "",
) -> Dict[str, Any]:
    """Record an explicit human or maintainer decision."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        decision_id = store.record_decision(
            run_id,
            decision_type,
            attempt_id=attempt_id,
            rationale=rationale,
            actor=actor,
        )
        return {"decision_id": decision_id, "registry": str(database)}
    finally:
        store.close()


@mcp.tool(name="climbhill.issues.propose")
def issues_propose(
    title: str,
    body: str,
    repo: str = ".",
    registry: Optional[str] = None,
    labels: str = "",
    priority: str = "",
    evidence: str = "",
    source_run_ids: str = "",
    source_attempt_ids: str = "",
) -> Dict[str, Any]:
    """Store a GitHub issue proposal from meta-analysis."""
    repo_path = _repo(repo)
    database = registry_path(repo_path, registry)
    store = Registry(database)
    try:
        issue_id = store.propose_issue(
            title,
            body,
            labels=labels,
            priority=priority,
            evidence=evidence,
            source_run_ids=source_run_ids,
            source_attempt_ids=source_attempt_ids,
        )
        return {"issue_proposal_id": issue_id, "registry": str(database)}
    finally:
        store.close()


def main() -> None:
    mcp.run()


def smoke_main() -> int:
    report = repo_prepare(".")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
