---
name: deep-research-gemini
description: Run Google Gemini deep research and search-grounded Gemini research tasks with bounded scope and captured outputs. Use when research should rely on Gemini, Google Search grounding, or Google-hosted document context.
---

# Gemini Deep Research

Use this skill for Gemini Deep Research Agent or Gemini search-grounded research
flows. Gemini Deep Research is useful when research should be grounded in Google
Search or uploaded documents.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-gemini/scripts/gemini_research.py \
  --prompt "Research current deep research APIs. Keep the answer concise and cite sources." \
  --mode grounded \
  --model gemini-3.5-flash
```

Required 1Password-backed variables:

- `GOOGLE_API_KEY`
- `GOOGLE_CLOUD_PROJECT` when project-scoped Gemini or Google Cloud APIs need a project resource name

## Cost Controls

- Use search grounding or Deep Research Agent only when fresh web/document
  research is required.
- Cap prompt scope and request concise reports.
- For benchmark parity, record whether the run used the Deep Research Agent,
  generateContent with grounding, or a manual two-step retrieval workflow.
- The benchmark command uses grounded Interactions API mode by default because
  Gemini Deep Research Agent tasks are documented as agentic workflows that can
  cost around or above the repository's `$1` per-call budget. Use
  `--mode deep-research-start` only for a deliberate live Deep Research Agent
  experiment.

## Current Source Links

- https://ai.google.dev/gemini-api/docs/interactions/deep-research
- https://ai.google.dev/gemini-api/docs/google-search
- https://gemini.google/overview/deep-research/
