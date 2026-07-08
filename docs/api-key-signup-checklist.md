# API Key Signup Checklist

Create accounts and API keys for the services below, then store each value in
the `awesome-deep-researchers` 1Password vault item named `api-keys`. The field
names must match `.env.adr.example`.

## Core Provider Keys

These unlock the main commercial API skills and the default live smoke flow.

| Priority | Service | Signup / Console | 1Password Field | Used By |
| --- | --- | --- | --- | --- |
| 1 | OpenAI Platform | https://platform.openai.com/api-keys | `OPENAI_API_KEY` | `deep-research-openai`, GPT Researcher, STORM, Smolagents |
| 2 | Google AI Studio / Gemini API | https://aistudio.google.com/apikey | `GOOGLE_API_KEY`, optional `GOOGLE_CLOUD_PROJECT` | `deep-research-gemini` |
| 3 | Perplexity API | https://docs.perplexity.ai/docs/getting-started | `PERPLEXITY_API_KEY` | `deep-research-perplexity` |
| 4 | Exa | https://dashboard.exa.ai/api-keys | `EXA_API_KEY` | `deep-research-exa` |
| 5 | Tavily | https://app.tavily.com/home | `TAVILY_API_KEY` | `deep-research-tavily`, GPT Researcher |
| 6 | Jina AI | https://jina.ai/reader/ | `JINA_API_KEY` | `deep-research-jina` |
| 7 | xAI Console | https://console.x.ai/ | `XAI_API_KEY` | `deep-research-xai-grok` |
| 8 | You.com API | https://api.you.com/ | `YOU_API_KEY` | `deep-research-you`, optional STORM retriever |

## Optional Framework Keys

These are useful when running open-source frameworks or alternate model/search
backends.

| Service | Signup / Console | 1Password Field | Used By |
| --- | --- | --- | --- |
| Hugging Face | https://huggingface.co/settings/tokens | `HF_TOKEN` | `deep-research-smolagents`, model downloads, hosted inference |
| Anthropic Console | https://console.anthropic.com/settings/keys | `ANTHROPIC_API_KEY` | LangChain or Smolagents with Claude models |
| SearchAPI.io or Bing-compatible Web Search | https://www.searchapi.io/ | `BING_SEARCH_API_KEY` | STORM retriever option |
| You.com Search API / YDC | https://api.you.com/ | `YDC_API_KEY` | STORM retriever option |

## 1Password Entry

After signup, create the vault if needed:

```bash
op vault create awesome-deep-researchers
```

Then create or update the item:

```bash
op item create \
  --vault awesome-deep-researchers \
  --category "API Credential" \
  --title api-keys \
  OPENAI_API_KEY= \
  PERPLEXITY_API_KEY= \
  EXA_API_KEY= \
  TAVILY_API_KEY= \
  JINA_API_KEY= \
  XAI_API_KEY= \
  YOU_API_KEY= \
  GOOGLE_API_KEY= \
  GOOGLE_CLOUD_PROJECT= \
  HF_TOKEN= \
  ANTHROPIC_API_KEY= \
  BING_SEARCH_API_KEY= \
  YDC_API_KEY=
```

Add real key values as you get them. Example for one field:

```bash
op item edit api-keys \
  --vault awesome-deep-researchers \
  OPENAI_API_KEY="paste-openai-key-here"
```

Repeat for the remaining fields. Leave unknown or not-yet-needed fields blank;
the live benchmark runner skips providers whose required key is not set unless
`--fail-missing-env` is used.

Verify without printing secrets:

```bash
python -m awesome_deep_research.op_env --env-file .env.adr --scope commercial
op run --env-file .env.adr -- python -m awesome_deep_research.op_env --live --scope commercial
```

Run the live smoke only after verification passes:

```bash
op run --env-file .env.adr -- python benchmark/live_smoke.py -v
```
