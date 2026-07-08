---
name: deep-research-stanford-storm
description: Run Stanford STORM for perspective-driven, article-style deep research reports with retriever-backed citations. Use when a task needs Wikipedia-like synthesis, outline-driven research, or comparison against heavier open-source research frameworks.
---

# Stanford STORM

Use this skill for Wikipedia-style article generation and perspective-driven
research. STORM is usually slower and heavier than API search tools, so reserve
it for article synthesis benchmarks.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-stanford-storm/scripts/run_storm.py \
  --topic "AI for Science research agents" \
  --rm-name you \
  --fast-model gpt-4o-mini \
  --strong-model gpt-4o-mini
```

Common 1Password-backed variables:

- `OPENAI_API_KEY` or another LiteLLM-compatible model key
- `BING_SEARCH_API_KEY` or `YDC_API_KEY`

## Cost Controls

- Use the same economical model for fast and strong model settings in smoke
  tests.
- Prefer narrow topics.
- Watch intermediate output volume because STORM can generate many files.

## Source Link

- https://github.com/stanford-oval/storm
