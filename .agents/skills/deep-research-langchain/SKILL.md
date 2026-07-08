---
name: deep-research-langchain
description: Run LangChain Open Deep Research or LangGraph-based iterative research workflows with configurable retrieval, reflection, and server-backed execution. Use when a benchmark or task needs inspectable graph orchestration rather than a single hosted research API.
---

# LangChain Open Deep Research

Use this skill when you need an inspectable graph workflow with iterative
research, reflection, and configurable retrieval.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-langchain/scripts/research.py \
  --query "AI for Science agents: current systems and evidence" \
  --max-iterations 2
```

Common 1Password-backed variables:

- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `TAVILY_API_KEY`

## Cost Controls

- Keep `--max-iterations` at 1 or 2 for benchmark tasks.
- Use a low-cost model for reflection and summarization.
- Skip this benchmark when the local LangGraph server is not running.

## Source Link

- https://github.com/langchain-ai/open_deep_research
