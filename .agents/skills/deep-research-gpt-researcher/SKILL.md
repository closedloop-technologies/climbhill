---
name: deep-research-gpt-researcher
description: Run GPT Researcher as a self-hosted open-source deep research framework using an LLM plus a search provider. Use when a task needs inspectable local report generation, configurable retrievers, or comparison against commercial research APIs.
---

# GPT Researcher

Use this skill when you want a self-hosted report-writing agent rather than a
single commercial deep research API.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-gpt-researcher/scripts/run_research.py \
  --query "AI for Science agents: current systems and evidence" \
  --report-type research_report
```

Common 1Password-backed variables:

- `OPENAI_API_KEY` or another configured LLM key
- `TAVILY_API_KEY` or another configured search key

## Cost Controls

- Use `research_report` before `deep_research_report`.
- Configure a cheaper model for planner/retriever steps.
- Keep source count and max sections bounded in framework configuration.

## Source Link

- https://github.com/assafelovic/gpt-researcher
