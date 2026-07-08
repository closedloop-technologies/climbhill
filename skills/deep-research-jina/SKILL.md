---
name: deep-research-jina
description: Use Jina Reader and Jina Search APIs for deep research retrieval, URL-to-markdown conversion, and markdown-oriented search results. Use when a workflow needs clean page extraction, search snippets, or reader output before synthesis.
---

# Jina AI

Use this skill as a reader/search component in a deep research workflow. Jina
Reader turns URLs into markdown; Jina Search returns markdown-oriented web
results.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-jina/scripts/jina_tools.py \
  search "deepresearch the deepresearchers"
```

Optional 1Password-backed variable:

- `JINA_API_KEY`

## Cost Controls

- Basic Reader usage is available without a key, but API keys improve limits.
- Use search for source discovery, then read only the URLs needed for evidence.
- Avoid treating Jina alone as a full deep research agent; pair it with a
  planner/synthesizer.

## Current Source Links

- https://jina.ai/reader/
- https://github.com/jina-ai/reader
