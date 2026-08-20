# MCP Tool Surface

The MCP server is an agent-facing adapter over the same interfaces as the CLI.
The target tool surface is:

- `climbhill.assess`
- `climbhill.runs.create`
- `climbhill.runs.get`
- `climbhill.runs.list`
- `climbhill.runs.status`
- `climbhill.attempts.create`
- `climbhill.attempts.attach_patch`
- `climbhill.attempts.record_lineage`
- `climbhill.evaluations.record`
- `climbhill.continuation.analyze`
- `climbhill.decisions.record`
- `climbhill.policy.explain`
- `climbhill.reports.generate`
- `climbhill.resources.search`
- `climbhill.resources.add`

The engine, not the calling agent, resolves writable paths, computes promotion
eligibility, intersects authorization, checks freshness, and consumes
recommendations. Tool inputs never grant authority merely by requesting a path,
Focus, evaluator, or budget.
