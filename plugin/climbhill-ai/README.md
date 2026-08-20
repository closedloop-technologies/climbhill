# ClimbHill.ai Codex Plugin

This plugin packages ClimbHill.ai workflows for Codex.

Current status: local MVP. The manifest, skill path, MCP config path, and Python MCP server entrypoint are present.

## Provides

- Plugin metadata for Codex.
- MCP configuration at `.mcp.json` that launches `python -m climbhill.mcp_server`.
- A `skills/` directory for plugin-distributed agent procedures.

## Intended Workflows

- Align a repository for recursive self-improvement.
- Read and check ClimbHill policy.
- Register Attempts.
- Record evaluations and costs.
- Compare attempts.
- Generate Markdown reports.
- Record human decisions.
- Propose GitHub issues from meta-analysis.
