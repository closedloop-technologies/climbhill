# MCP Server

The MCP server exposes ClimbHill's core interfaces to coding agents. It is an
adapter, not the canonical product interface or source of truth.

The current Python entrypoint is:

```bash
python -m climbhill.mcp_server
```

## Responsibilities

- Assess repository and machine capabilities.
- Create and inspect standalone Runs.
- Create and attach Attempt artifacts.
- Record typed Evaluations and Decisions.
- Explain policy, authorization, and eligibility.
- Invoke Continuation Analysis at a frozen Evidence Snapshot.
- Search and add research resources.
- Generate derived reports.

## Persistence

The target server reads and writes canonical file-backed Run state and may use a
rebuildable SQLite cache. The transitional Python server currently uses SQLite
directly and is not the target persistence contract.

## Safety

MCP callers cannot self-assert human authority, widen Authorization Envelopes,
change the pinned evaluator, bypass post-diff checks, or promote an ineligible
Attempt.
