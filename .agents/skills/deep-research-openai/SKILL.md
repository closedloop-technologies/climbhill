---
name: deep-research-openai
description: Run OpenAI deep research models through the Responses API with explicit effort, model, cost, and output controls. Use when launching citation-backed OpenAI research runs, smoke-testing OpenAI provider behavior, or capturing reproducible benchmark output.
---

# OpenAI Deep Research

Use this skill for autonomous, citation-backed research through OpenAI's Deep
Research models. Prefer `o4-mini-deep-research` for benchmark calls because the
repo target is less than `$1` per task.

## Environment

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-openai/scripts/run_deep_research.py \
  --prompt "deepresearch the deepresearchers" \
  --model o4-mini-deep-research \
  --effort low
```

Required 1Password-backed variable:

- `OPENAI_API_KEY`

## Cost Controls

- Use `o4-mini-deep-research` before `o3-deep-research`.
- Use `--effort low` for benchmark smoke tasks.
- Keep prompts narrow and request concise reports.
- Save raw output, then normalize it with `deep-research-okf-normalize`.

## Current Source Links

- https://platform.openai.com/docs
- https://platform.openai.com/docs/guides/deep-research
