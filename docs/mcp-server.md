# MCP Server

The MCP server is the agent-facing runtime and system of record.

It should be usable by Codex and other MCP-capable coding agents.

The current local entrypoint is:

```bash
python -m awesome_deep_research.mcp_server
```

## Responsibilities

- Inspect repo alignment.
- Read and check policy.
- Search and add resources.
- Create runs.
- Register candidates.
- Attach code pointers and patches.
- Record evaluations.
- Track costs.
- Sample from history.
- Compare candidates.
- Generate reports.
- Record human decisions.
- Propose GitHub issues.

## MVP Storage

The MVP should use SQLite and local file storage. Future versions may support Postgres and object storage.
