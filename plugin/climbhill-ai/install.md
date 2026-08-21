# Install

This is a repository-local plugin package.

1. Install the ClimbHill.ai plugin in Codex.
2. Start the local ClimbHill MCP server.
3. Run `climbhill init` in a target repository.
4. Use the provided skills to run bounded attempt improvement loops.

The plugin MCP config launches:

```bash
python -m climbhill.mcp_server
```

The MCP server requires the stable v1 Python MCP SDK dependency declared by this package: `mcp[cli]>=1.27,<2`.
