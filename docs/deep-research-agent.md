# What Is a Deep Research Agent?

A deep research agent is an agentic research system that plans an investigation,
retrieves information from multiple sources, evaluates and reconciles evidence,
and synthesizes a traceable report. It differs from a single search or chat
completion because the system usually performs multiple search/read/reason loops
and exposes citations, source lists, or intermediate traces.

## Core Capabilities

| Capability | What to Look For |
| --- | --- |
| Planning | Turns the user prompt into subquestions, source strategy, or a research plan |
| Retrieval | Searches web, private documents, scholarly indexes, APIs, or databases |
| Reading | Opens and extracts source content rather than only using snippets |
| Cross-checking | Compares sources, dates, definitions, and conflicting claims |
| Synthesis | Produces a structured report with conclusions, caveats, and next questions |
| Traceability | Preserves citations, URLs, source IDs, and enough metadata to audit claims |
| Cost control | Supports effort levels, source caps, token caps, search-depth controls, or model choice |

## Build Your Own

A minimal self-hosted deep research agent has these components:

1. Planner: decompose the prompt into research questions and success criteria.
2. Retriever: search web or private indexes with bounded result counts.
3. Reader: fetch primary sources and convert them to clean text or markdown.
4. Evidence store: save source URL, title, timestamp, snippets, and extracted claims.
5. Synthesizer: write the answer with explicit citations and uncertainty.
6. Normalizer: convert raw output into an OKF bundle for comparison and refresh.

Use established frameworks when possible:

- GPT Researcher for report-oriented autonomous research.
- LangChain Open Deep Research or LangGraph when you need inspectable workflows.
- Stanford STORM for article-style synthesis.
- Smolagents when code-as-action and tool composition are useful.

For private or domain-specific corpora, build a source manifest before
synthesis. Guidance for Google Docs, YouTube, local files, S3, arXiv, databases,
Slack, email, and tickets is in `docs/custom-data-sources.md`.

## Access Modes

Deep research systems should be labeled by deployment mode before comparing
quality or cost:

| Access Mode | Operational Boundary |
| --- | --- |
| Hosted API/Web | The provider owns the agent loop and exposes a hosted API or web UI. The local repo only submits prompts and captures outputs. |
| API component | The provider exposes search, retrieval, reading, or model calls that a separate agent loop uses as tools. These are not full report-writing systems by themselves. |
| Self-hosted library/framework | The agent loop runs locally or in our container. It may still call hosted LLM/search APIs, but orchestration, prompts, logs, and failure modes are under our control. |

Deep Research Comparator uses a similar serving split: open-source agents are
served from Dockerized agent services, while closed-source agents are reached
through proxy pods that call external APIs. Its Simple Deepresearch baseline is
a prompt-based scaffold that can wrap different LLMs through an OpenAI-compatible
API.

## Call a Third-Party API

Third-party APIs are better when the task needs fresh web data, citation
handling, provider-maintained browsing, or a quick benchmark across systems.
Use `.agents/skills/<skill-name>/SKILL.md` for exact command and environment
details. Store secrets in 1Password and run commands with `op run`:

```bash
op run --env-file .env.adr -- python benchmark/run_benchmark.py \
  --skills deep-research-perplexity \
  --categories "Source Retrieval" \
  --max-questions 1 \
  -v
```

## Output Standard

Raw reports are not enough for comparison. Normalize each run to an OKF-style
bundle with:

- `report.md` for raw or lightly normalized output;
- `findings.md` for claim-like findings;
- `uncertainties.md` for caveats, conflicts, assumptions, and stale-data risks;
- `method.md` for provider, prompt, model, effort, cost controls, and timestamp.

See `docs/okf-normalization.md`.
