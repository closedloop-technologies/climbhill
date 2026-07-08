---
name: deep-research-you
description: Run You.com Research API or You.com MCP-backed deep research with explicit research_effort and cost controls. Use when a task needs You.com research, ARI-style workflows, finance research options, or benchmark comparison.
---

# You.com Research

Use this skill for You.com's Research API, ARI-style research workflows, or the
You.com MCP tools. The Research API exposes effort tiers; choose the smallest
tier that can answer the benchmark prompt.

## Environment

```bash
op run --env-file .env.adr -- python - <<'PY'
import os, requests

response = requests.post(
    "https://api.you.com/v1/research",
    headers={"X-API-Key": os.environ["YOU_API_KEY"]},
    json={
        "input": "deepresearch the deepresearchers",
        "research_effort": "lite",
    },
    timeout=300,
)
response.raise_for_status()
print(response.text)
PY
```

Required 1Password-backed variable:

- `YOU_API_KEY`

## Cost Controls

- Use `research_effort: lite` for smoke tests.
- Use `standard`, `deep`, `exhaustive`, or `frontier` only when the benchmark
  explicitly needs that depth and still stays below `$1`.
- Keep one provider or one research question per call.

## Current Source Links

- https://you.com/docs/welcome
- https://you.com/docs/api-reference/research/v1-research
- https://you.com/pricing

## Benchmark Command

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-you/scripts/you_research.py \
  --prompt "deepresearch the deepresearchers" \
  --research-effort lite
```

## Finance Research

You.com also exposes a domain-specific Finance Research API. Use it when the
question should search a finance-optimized index rather than the open web:
company fundamentals, equity and commodity prices, macro indicators, SEC
filings, earnings transcripts, analyst coverage, and financial news.

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-you/scripts/you_research.py \
  --api finance \
  --prompt "Compare the gross margins of Apple, Microsoft, and Google over the past three fiscal years." \
  --research-effort deep
```

Finance Research supports `deep` and `exhaustive`; it does not support `lite`.
Keep prompts scoped and verify cost before adding finance runs to the under-`$1`
benchmark suite.

See `docs/domain-specific-deep-research.md` for domain categorization.
