# 2026 Deep Research API and Framework Landscape

Run folder: `research/2026-06-23-08-30-53-i62o`

Prompt:

> Deepresearch the 2026 latest and best deep research APIs, providers, open-source frameworks, tips, tricks, skills, best practices, benchmarks, concepts, and emerging patterns. Prioritize official provider docs, current benchmark leaderboards, and primary sources. Include actionable recommendations for this awesome-deep-researchers repository.

## Inputs

Raw provider outputs:

| Provider | Status | Duration | Output file |
| --- | --- | ---: | --- |
| Gemini grounded research | Success | 62.97s | `gemini-deep-research.response.txt` |
| Perplexity Sonar | Success | 59.71s | `perplexity-sonar.response.txt` |
| You.com Research | Success | 17.30s | `you-research.response.txt` |
| Tavily Search | Success | 2.83s | `tavily-search.response.txt` |
| Exa Search | Success | 2.17s | `exa-research.response.txt` |
| Jina Search | Success | 21.01s | `jina-ai.response.txt` |

External benchmark data:

- `deepresearch-bench-leaderboard.csv` fetched from https://huggingface.co/spaces/muset-ai/DeepResearch-Bench-Leaderboard
- `deepresearch-bench-leaderboard-gpt55.csv` fetched from the same Hugging Face Space.
- Full model inventory is normalized in `docs/deepresearch-bench-leaderboard.md`.

## Evidence Weighting

1. Official docs and provider source indexes are highest confidence.
2. DeepResearch Bench leaderboard CSVs are benchmark evidence for model ranking, but only for that benchmark's task distribution and judge setup.
3. Raw provider outputs are useful discovery material, but claims about unreleased or future products must be verified before entering README tables.
4. Blog posts and community comparisons are low-to-medium confidence unless they point to primary sources.

## 2026 Rubric

The repository should evaluate deep research systems on these dimensions:

| Dimension | Weight | What To Measure |
| --- | ---: | --- |
| Evidence quality | 25% | Citation accuracy, primary-source use, source diversity, stale-source handling |
| Research depth | 20% | Comprehensiveness, effective citations, ability to recurse into contradictions |
| Controllability | 15% | Planning controls, search/result caps, domain filters, source allowlists |
| Cost and latency | 15% | Under-$1 mode availability, actual cost metadata, run time |
| Integration surface | 15% | API availability, files/custom corpora, MCP/tool support, async/background jobs |
| Normalization fit | 10% | Ease of converting output to OKF findings, uncertainties, method metadata |

## Ranking For This Repository

This ranking combines repo fit, API availability, benchmark evidence, and the live fan-out run. It is not a universal product ranking.

| Rank | System | Why |
| ---: | --- | --- |
| 1 | Gemini Deep Research / grounded Gemini | Strong official Deep Research Agent docs, current API path, file/search/tool support, and successful local smoke. DeepResearch Bench also includes `gemini-2.5-pro-deepresearch` with high citation count in the main leaderboard. |
| 2 | OpenAI Deep Research | Strong native deep research product concept and API skill path. Needs a live repo smoke and cost-controlled run before ranking above Gemini locally. |
| 3 | Perplexity Sonar / Research | Best fit for fast source scouting and citation-heavy discovery. Local smoke succeeded cheaply; benchmark rows show strong citation accuracy for Perplexity research/search variants. |
| 4 | LangChain Open Deep Research | Best OSS graph workflow fit for inspectable planning, reflection, and custom tools. DeepResearch Bench includes LangChain GPT-5 variants, but local runs require a server/workflow setup. |
| 5 | Tavily Research/Search | Strong search/retrieval substrate and current benchmark row `tavily-research`. Local smoke is fast and cheap, but it is less of a full autonomous report writer than Gemini/OpenAI/Perplexity. |
| 6 | Exa Search/Research | Good semantic search and source discovery building block. Local smoke succeeded; use for retrieval-heavy pipelines rather than final report generation unless Exa Research mode is explicitly benchmarked. |
| 7 | Jina Reader/Search | Excellent content conversion and retrieval building block. Local run produced very large output; use caps and post-filtering before synthesis. |
| 8 | xAI Grok deeper search | DeepResearch Bench includes `grok-deeper-search`; repo skill exists, but local live smoke remains unverified. |
| 9 | GPT Researcher | Mature OSS report-oriented framework, useful when the repo needs self-hosted orchestration over search providers. Needs current local benchmark run with configured retriever/model. |
| 10 | Stanford STORM | Strong article-generation pattern and citations, but less aligned with API fan-out smoke tests; best kept as OSS framework benchmark. |
| 11 | Smolagents | Useful code-as-action research framework. Rank depends heavily on chosen model/search tool and sandboxing policy. |
| 12 | You.com Research / Finance Research | Local smoke succeeded and Finance Research is important for domain-specific evaluation. General research output was concise; finance mode should be separately benchmarked because its minimum effort/cost differs. |

## Best Practices To Encode In Skills

- Always capture raw provider output before summarization.
- Record provider, model, prompt, effort/depth settings, source caps, cost estimate, and timestamp in `method.md`.
- Normalize successful outputs into OKF bundles with separate `findings.md`, `uncertainties.md`, and `method.md`.
- Keep low-cost smoke commands separate from full deep-research modes.
- Prefer source allowlists for private or custom corpora.
- Add a "manual verification needed" section to every final report.
- Treat search APIs as retrieval components unless they provide planning, iterative reading, and synthesis.
- Benchmark citation accuracy and effective citations separately from prose quality.
- For domain-specific research, use domain indexes where available: finance, medicine/life sciences, legal/regulatory, standards, and internal corpora.

## Repo Actions

1. Keep `.agents/skills` as the supported skill root; do not add new benchmark dependencies on legacy skill roots.
2. Keep `scripts/run_api_fanout.py` for raw multi-provider collection.
3. Use `benchmark/live_smoke.py` for under-$1 controlled benchmark runs with OKF normalization.
4. Add future provider rows only when there is a source URL, an env field, and an under-$1 smoke plan.
5. Use `docs/deepresearch-bench-leaderboard.md` as the current model inventory for DeepResearch Bench.

## Caveats

- Provider outputs disagree about 2026 product names and benchmark leaders. Some claims in raw outputs are discovery leads, not accepted facts.
- The Jina run produced a broad search dump rather than a concise synthesized report; it is useful as retrieval evidence, not as final analysis.
- The fan-out run did not include OpenAI or xAI to avoid uncontrolled cost/dependency failures in this research capture; both remain in the skill set and should be live-smoked separately.
