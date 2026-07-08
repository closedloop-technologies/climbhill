# MCP Tool Surface

The initial MCP server should expose a small, understandable set of tools:

- `climbhill.repo.inspect`
- `climbhill.repo.align`
- `climbhill.policy.read`
- `climbhill.policy.check_patch`
- `climbhill.resources.search`
- `climbhill.resources.add`
- `climbhill.runs.create`
- `climbhill.runs.get`
- `climbhill.runs.list`
- `climbhill.candidates.register`
- `climbhill.candidates.attach_patch`
- `climbhill.candidates.evaluate`
- `climbhill.candidates.compare`
- `climbhill.candidates.record_lineage`
- `climbhill.costs.record`
- `climbhill.history.sample`
- `climbhill.reports.generate`
- `climbhill.decisions.record`
- `climbhill.issues.propose`

The tool surface should remain small enough for agents to understand but complete enough to support the full improvement loop.
