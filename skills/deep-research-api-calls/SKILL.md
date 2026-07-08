---
name: deep-research-api-calls
description: Prepare and run bounded calls across deep research provider APIs with explicit cost limits, API-key sources, benchmark prompts, and output capture. Use when comparing providers, creating reproducible API commands, or normalizing raw provider outputs after a research run.
---

# Deep Research API Calls

Use this skill when you need to call a third-party deep research agent or create
a reproducible command for one. Prefer the repository benchmark runner when
comparing providers; use direct calls only for focused experiments.

## Cost Rule

Every benchmark call must target a maximum expected cost below `$1`. If a
provider exposes effort, search count, source count, reasoning token, or max
output controls, set the lowest mode that can still answer the prompt. Record
actual cost metadata when the provider returns it; otherwise record the pricing
assumption and measured token/search counts.

## API Keys

Load keys from 1Password with `op run` rather than hard-coding secrets:

```bash
op run --env-file .env.adr -- python benchmark/run_benchmark.py --max-questions 1 -v
```

Expected environment names:

| Provider | Environment Variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| Perplexity | `PERPLEXITY_API_KEY` |
| Exa | `EXA_API_KEY` |
| Tavily | `TAVILY_API_KEY` |
| Jina AI | `JINA_API_KEY` |
| xAI | `XAI_API_KEY` |
| You.com | `YOU_API_KEY` |
| Google Gemini | `GOOGLE_API_KEY` |

## Provider Call Patterns

| Provider | Typical Command | Budget Controls |
| --- | --- | --- |
| OpenAI Deep Research | `python .agents/skills/deep-research-openai/scripts/run_deep_research.py --prompt "$PROMPT"` | prefer mini/deep-research model, cap output, short prompt |
| Perplexity Sonar Deep Research | `python .agents/skills/deep-research-perplexity/scripts/ask.py --prompt "$PROMPT"` | use low search/context mode where available |
| Exa Research | `python .agents/skills/deep-research-exa/scripts/exa_tools.py search "$PROMPT" --num-results 5 --highlights` | use search for benchmark smokes; reserve research mode for deeper runs |
| Tavily Search | `python .agents/skills/deep-research-tavily/scripts/tavily_search.py --query "$PROMPT"` | cap results and include answer mode only when needed |
| Jina AI | `python .agents/skills/deep-research-jina/scripts/jina_tools.py search "$PROMPT"` | cap result count and fetched pages |
| xAI Grok | `python .agents/skills/deep-research-xai-grok/scripts/grok_research.py --query "$PROMPT"` | use economical model and cap output |
| You.com ARI | provider-specific ARI endpoint wrapper | avoid high-cost professional report mode for benchmark calls |
| Google Gemini Deep Research | Gemini API or UI workflow where available | cap grounding/search effort and output tokens |

## Benchmark Prompts

Use short prompts that still exercise multi-step behavior:

- `deepresearch the deepresearchers`: identify current deep research providers,
  APIs, cost controls, and citation behavior.
- `AI for Science`: compare two AI-for-science agent systems with primary
  sources and uncertainty notes.
- `standards trace`: find the current source of truth for a technical standard
  and summarize revision status.

## Output Contract

Save raw provider output first. Then normalize it with `deep-research-okf-normalize`
so reports can be compared as markdown concepts with citations.
