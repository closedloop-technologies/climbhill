---
name: deep-research-tavily
description: Use Tavily Search API for bounded deep research retrieval, RAG-ready snippets, and low-cost web search. Use when a workflow needs search grounding, source discovery, or benchmarkable retrieval rather than full report-writing.
---

# Tavily Search

Use this skill for low-cost search/retrieval steps inside a deep research
workflow. Tavily is usually a retriever, not a full report-writing agent.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-tavily/scripts/tavily_search.py \
  --query "deepresearch the deepresearchers" \
  --search-depth basic \
  --max-results 5
```

Required 1Password-backed variable:

- `TAVILY_API_KEY`

## Cost Controls

- Use `basic`, `fast`, or `ultra-fast` search depth for benchmark tasks.
- Use `advanced` only when the task explicitly needs deeper retrieval.
- Keep `max_results` small and avoid raw content unless needed.

## Current Source Links

- https://docs.tavily.com/documentation/api-reference/endpoint/search
- https://docs.tavily.com/documentation/api-credits
