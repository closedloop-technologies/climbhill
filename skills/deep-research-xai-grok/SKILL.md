---
name: deep-research-xai-grok
description: Run xAI Grok research with optional web and X search tools for current-event, social, market, or news-oriented research. Use when a task needs Grok-backed synthesis, X-aware source discovery, or provider comparison.
---

# xAI Grok

Use this skill when the task benefits from Grok's current web or X search tools,
especially for social, market, or news-oriented research.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-xai-grok/scripts/grok_research.py \
  --query "deepresearch the deepresearchers" \
  --model grok-4.3 \
  --web-search
```

Required 1Password-backed variable:

- `XAI_API_KEY`

## Cost Controls

- Use the lowest-cost current Grok model that supports the needed tools.
- Enable `--x-search` only when X/Twitter evidence is central to the task.
- Prefer batch pricing only for non-interactive refresh jobs.

## Current Source Links

- https://docs.x.ai/overview
- https://docs.x.ai/developers/models
- https://docs.x.ai/developers/pricing
