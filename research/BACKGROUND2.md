# The State of Deep Research APIs: A Comprehensive Technical and Economic Analysis (2025)

## Executive Summary

The transition from Retrieval-Augmented Generation (RAG) to autonomous "Deep Research" marks a pivotal evolution in artificial intelligence, fundamentally altering how machines process information. We have moved beyond simple query-response paradigms into an era of agentic systems capable of recursive planning, multi-hop reasoning, and the autonomous synthesis of expert-level reports. This shift is driven by the emergence of "thinking models" and sophisticated agentic frameworks that do not merely retrieve data but actively reason about its validity, relevance, and interconnection over extended compute horizons.

This report provides an exhaustive analysis of the Deep Research landscape as of late 2025. It dissects the proprietary ecosystem dominated by hyperscalers like OpenAI, Google, and Perplexity, and contrasts it with the burgeoning open-source sector. We examine the intricate economics of token-based pricing versus search-query billing, the architectural divergences between graph-based and code-based agent orchestration, and the critical role of new benchmarks like Humanity's Last Exam (HLE) in measuring true progress. Furthermore, we explore the strategic implications for enterprises choosing between managed API services and self-hosted pipelines, analyzing trade-offs in data sovereignty, cost control, and reasoning fidelity.

## 1. The Paradigm Shift: From RAG to Deep Research

To understand the current API landscape, one must first appreciate the architectural divergence from traditional Large Language Model (LLM) applications. Standard RAG systems operate on a linear trajectory: retrieve documents based on semantic similarity, stuff context into a prompt, and generate an answer. This approach is brittle, often failing when the answer requires synthesizing information across disparate sources or when the initial retrieval misses the nuance of the query.

Deep Research agents, conversely, are designed for autonomy and persistence. They operate over minutes or hours (not milliseconds), can execute dozens of search queries, backtrack when hitting dead ends, and synthesize findings into structured reports. This is achieved through:

- **Thinking Models**: LLMs trained with reinforcement learning to "show their work" through extended chains-of-thought (e.g., OpenAI's o3, DeepSeek-R1).
- **Agentic Frameworks**: Orchestration layers that allow models to call tools (search, scraping, code execution) in multi-step loops, maintaining state across iterations (e.g., Perplexity's Sonar, LangGraph, Smolagents).
- **Strategic Planning**: The ability to decompose a vague user query into a research plan, dynamically revise it based on intermediate findings, and synthesize a coherent answer grounded in citations.

Lilian Weng's 2026 harness-engineering analysis sharpens this distinction: the competitive unit is not only the base model, but the full runtime around it. A research harness decides how the model plans, calls tools, manages context, stores artifacts, spawns subagents, and evaluates its own work. For deep research systems, this means persistent filesystem memory, explicit job orchestration, compact context construction, and regression-tested workflow changes are first-class architecture choices rather than implementation details.

The economic and technical implications of this shift are profound, as we will explore in the following sections.

## 2. The Proprietary Ecosystem: API Leaders and Their Architectures

### 2.1 OpenAI: o3 and Deep Research

**Model**: OpenAI's o3-series (launched late 2024) represents the cutting edge of "extended reasoning." Unlike the standard GPT-4o, which generates responses token-by-token, o3 models engage in explicit "thinking" before producing output. This is visible in the API as a "reasoning_tokens" field, which tracks the internal monologue the model uses to plan its answer.

**Deep Research Mode**: OpenAI offers a specialized "Deep Research" endpoint (o3-deep-research), which autonomously executes multi-step research plans. Users provide a broad question, and the API returns a comprehensive report after conducting web searches, reading documents, and synthesizing findings.

**Pricing**: This capability is expensive. The o3-deep-research endpoint costs approximately $10 per 1M input tokens and $40 per 1M output tokens—roughly 4x the cost of GPT-4o. However, for strategic planning or legal analysis where depth is critical, this premium is justified.

**Architecture**: OpenAI uses a combination of Reinforcement Learning with Expert Revision (RLAER) to train o3 models to optimize for "correctness" over extended tasks, as demonstrated by its performance on the ARC-AGI benchmark where it scored 87.5%, far exceeding prior models.

**Limitations**: Despite its power, o3-deep-research is a black box. The user has no control over which sources are queried, how many searches are performed, or the intermediate reasoning steps. This opacity is problematic for compliance-heavy sectors where audit trails are mandatory.

### 2.2 Perplexity: Sonar and Real-Time Web Intelligence

**Model**: Perplexity's Sonar API is purpose-built for information retrieval, not just reasoning. It blends a medium-sized LLM (reportedly based on fine-tuned Llama variants) with a proprietary real-time search engine that indexes billions of web pages and updates continuously.

**Unique Selling Point**: Unlike OpenAI, which browses the web as a secondary tool, Perplexity treats web retrieval as its core competency. Every query triggers live searches, and responses include explicit sentence-level citations linking back to the source URL. This is the "gold standard" for transparent sourcing in Deep Research.

**Pricing**: Perplexity charges on a dual model:

- **Tokens**: $2 per 1M input tokens, $8 per 1M output tokens (significantly cheaper than OpenAI).
- **Search Requests**: $0.005 per search query (capped at a few thousand per minute).

For research-heavy tasks, the search fee is often the dominant cost component. A typical "Deep Research" query might trigger 20-50 search requests, adding $0.10–$0.25 per task.

**Performance**: Perplexity excels at factual, breadth-oriented research. It is the preferred API for tasks like market research, news summarization, or competitive intelligence where fresh data and citation fidelity matter more than deep reasoning.

**Limitations**: Perplexity's reasoning depth is inferior to OpenAI's o3. It struggles with complex, multi-hop questions that require planning or logical inference across disparate sources. It is a "retrieval-first" system, not a "reasoning-first" system.

### 2.3 Google DeepMind: Gemini with Grounding

**Model**: Gemini 2.0 Pro (and its upcoming 3.0 variants) is Google's flagship multimodal model. While comparable to GPT-4o in reasoning, Gemini's advantage lies in its deep integration with Google's ecosystem.

**Grounding and Enterprise Context**: Gemini for Enterprise offers "Grounding," where the model can search over a company's internal Google Drive, Docs, Gmail, or custom data silos. This is the killer feature for large enterprises already entrenched in Google Workspace. A research agent can seamlessly blend public web data with internal corporate knowledge—something OpenAI and Perplexity cannot do without extensive custom integration.

**Pricing**: Gemini Pro's standard pricing is similar to GPT-4o ($2.50 per 1M input tokens, $10 per 1M output tokens), but the Grounding API incurs additional costs based on the volume of internal documents queried.

**Performance**: Gemini 3 Pro reportedly achieves a 45.8% score on Humanity's Last Exam (HLE), significantly higher than OpenAI's o3 (26-30%). This suggests that for domain-specific, fact-heavy tasks, Gemini's massive training corpus (including access to Google's proprietary data) gives it an edge.

**Limitations**: Gemini's API is less mature for agentic workflows. While it can call tools, the orchestration is still relatively basic compared to dedicated agent frameworks like LangGraph or Smolagents.

### 2.4 xAI: Grok and the Real-Time Advantage

**Model**: Grok, developed by Elon Musk's xAI, is differentiated by its privileged access to X (formerly Twitter). This gives Grok a unique edge in real-time sentiment analysis, crisis monitoring, and financial markets research where social signals are leading indicators.

**Pricing**: xAI charges $5 per 1M input tokens and $15 per 1M output tokens. The real-time X data is bundled without additional fees, making it a bargain for users who need social media intelligence.

**Use Cases**: Grok is ideal for:

- **Political Campaigns**: Real-time tracking of public sentiment.
- **Finance**: Monitoring stock-related chatter before news outlets report it.
- **Crisis Management**: Early detection of viral negative sentiment about a brand.

**Limitations**: Grok is less capable for traditional Deep Research (e.g., academic synthesis or legal analysis) compared to OpenAI or Google. Its reasoning depth is modest, and it lacks the breadth of web indexing that Perplexity offers.

### 2.5 Comparative Table: Proprietary APIs

| Feature | OpenAI (o3) | Perplexity (Sonar) | Google (Gemini) | xAI (Grok) |
|---------|-------------|-------------------|-----------------|------------|
| **Reasoning Depth** | Superior | Moderate | High | Moderate |
| **Web Freshness** | Good (via browsing) | Excellent (live index) | Excellent | Real-time (X data) |
| **Citations** | Implicit | Explicit (sentence-level) | Explicit | Medium |
| **Enterprise Integration** | Limited | API-only | Deep (Workspace) | API-only |
| **Cost per 1M Tokens (Input)** | $10 | $2 | $2.50 | $5 |
| **Cost per 1M Tokens (Output)** | $40 | $8 | $10 | $15 |
| **Best Use Case** | Strategic, Legal | Market Research | Corporate Intel | Social Sentiment |

## 3. The Open Source Frontier: Self-Hosted Deep Research

The proprietary APIs dominate the market, but the open-source ecosystem is rapidly closing the gap. This is crucial for organizations that prioritize data sovereignty, cost control at scale, or the ability to customize reasoning behavior.

### 3.1 The Economics of Self-Hosting

Self-hosting a Deep Research pipeline involves:

- **Compute**: Renting GPUs (e.g., AWS, Lambda Labs, RunPod). A single A100 GPU costs roughly $1.50–$2.50 per hour.
- **Search API**: External search providers like Tavily or SerpAPI charge $0.005 per query.
- **Storage**: Vector databases (Pinecone, ChromaDB) for context caching.

**Break-Even Analysis**: For low-volume use (<1,000 reports/month), managed APIs like Perplexity are cheaper. However, at high volumes (>10,000 reports/month), the fixed cost of GPU rental amortizes, and self-hosting becomes 50-70% cheaper.

### 3.2 Key Open Source Projects

#### 3.2.1 DR-Tulu (AllenAI)

**Description**: DR-Tulu is a fine-tuned LLM specifically optimized for deep research tasks. Built on the Tulu architecture (AllenAI's instruction-tuned variant of Llama), it is trained using Reinforcement Learning with Expert Revision (RLAER) to prioritize citation accuracy.

**Performance**: DR-Tulu outperforms OpenAI's GPT-4 on the ScholarQA benchmark, demonstrating superior ability to synthesize academic literature and correctly attribute claims to sources.

**License**: Permissive open-source, allowing commercial use.

#### 3.2.2 Smolagents (Hugging Face)

**Description**: Smolagents is Hugging Face's lightweight agent framework. Unlike traditional JSON-based tool-calling (used by OpenAI and LangChain), Smolagents uses Python code as the action representation. The agent generates executable Python snippets, which are then run in a sandboxed environment.

**Efficiency**: This "code-as-action" approach reduces token usage by approximately 30% compared to JSON schemas, directly cutting costs.

**Performance**: Smolagents achieves a 55.15% success rate on the GAIA benchmark, rivaling proprietary agents.

**License**: Apache 2.0, suitable for enterprise deployment.

#### 3.2.3 STORM (Stanford)

**Description**: STORM (Synthesis of Topic Outline through Retrieval and Multi-perspective question asking) is a collaborative research framework. It simulates a team of "expert agents," each with a different perspective, debating and synthesizing findings.

**Innovation**: This perspective-taking approach improves the diversity of sources consulted and reduces confirmation bias in research synthesis.

**License**: Research license, less permissive than Apache 2.0, ensuring freedom for modification and commercial use.

#### 3.2.4 AgentRxiv

**Description**: AgentRxiv explores the frontier of multi-agent collaboration. It is not just a search tool but a platform where agents can "publish" papers to a central repository, which other agents can then read and cite.

**Significance**: This points to a future of "Automated Science" where fleets of agents collaboratively solve problems over weeks or months.

**License**: MIT License.

### 3.3 Open Source Ecosystem Overview

| Project | Developer | License | Core Innovation | Benchmark Note |
|---------|-----------|---------|-----------------|----------------|
| DR-Tulu | AllenAI | Permissive | RLER Training, Citation focus | Beats OpenAI on ScholarQA |
| Smolagents | Hugging Face | Apache 2.0 | Code-as-Action, 30% efficiency gain | High GAIA scores |
| STORM | Stanford | Research | Perspective-Taking, Collaborative | - |
| DeepResearcher | GAIR-NLP | Apache 2.0 | Robust Web Navigation RL | - |
| AgentRxiv | Independent | MIT | Multi-Agent Knowledge Sharing | - |

## 5. Benchmarking: The New Litmus Tests for Intelligence

As Deep Research agents surpass human capability in speed and breadth, traditional benchmarks like MMLU (which test static knowledge) have become saturated and irrelevant. New benchmarks have emerged to measure the true reasoning and synthesis capabilities of these agents.

### 5.1 Humanity's Last Exam (HLE)

HLE is positioned as the final frontier for closed-ended academic testing. It consists of 2,500 questions across math, hard sciences, and humanities that are designed to be "Google-proof"—meaning the answer cannot be found by simple retrieval but requires deriving a solution from expert-level principles.

**Current Performance**: As of 2025, even the best models struggle. Gemini 3 Pro scores ~45.8%, while OpenAI's o3-series models hover around 26-30%.

**Implication**: This gap highlights that while agents are excellent at finding information, they are still far from expert-level synthesis and problem-solving in specialized domains. A score below 50% indicates that "Superintelligence" is not yet here for deep research tasks.

### 5.2 GAIA (General AI Assistants Benchmark)

GAIA evaluates an agent's ability to perform multi-step, real-world tasks (e.g., "Find the cheapest flight to Tokyo arriving before 5 PM next Tuesday and email the itinerary to Bob").

**Significance**: This measures "Agency"—the ability to use tools reliably. Open-source agents like Hugging Face's CodeAgent have achieved 55.15% on the validation set, showing that open architectures can rival proprietary ones in task execution reliability.

## 6. Strategic Analysis: Choosing the Right Path

The decision between proprietary APIs and self-hosted pipelines involves complex trade-offs.

### 6.1 The Cost of Depth Analysis

Enterprise decision-makers must look beyond the "per token" price and calculate the "Cost per Report."

**Assumptions**: A comprehensive research report involves reading 50 pages of content (approx. 25,000 tokens) and synthesizing a 3,000-word report (approx. 4,000 tokens).

**OpenAI o3-deep-research**:

- Input: 25k * $10/1M = $0.25
- Output: 4k * $40/1M = $0.16
- **Total: $0.41 per report**

**Perplexity Sonar**:

- Input: 25k * $2/1M = $0.05
- Output: 4k * $8/1M = $0.032
- Search: 20 queries * $0.005 = $0.10
- **Total: $0.18 per report**

**Self-Hosted (DR-Tulu on AWS)**:

- Inference: Negligible variable cost (mostly fixed GPU rental)
- Search API (Tavily/Serp): 20 queries * $0.005 = $0.10
- **Total: ~$0.11 per report** (plus fixed infrastructure overhead)

**Insight**: Perplexity offers a nearly 56% cost saving over OpenAI for standard reports. However, self-hosting is only cheaper at massive scale where the fixed cost of GPU rental is amortized over thousands of reports. For low-volume use, managed APIs are significantly more economical.

### 6.2 Domain Suitability Matrix

| Feature | OpenAI (o3) | Perplexity (Sonar) | Google (Gemini) | xAI (Grok) | Self-Hosted |
|---------|-------------|-------------------|-----------------|------------|-------------|
| **Reasoning** | Superior (Strategic planning) | Good (Retrieval-focused) | High (Multimodal) | High | Variable (Model dependent) |
| **Data Freshness** | Good (Browsing) | Excellent (Live Index) | Excellent (Live + Internal) | Real-Time (Social) | Excellent (Live Search API) |
| **Citations** | Implicit | Explicit (Sentence-level) | Explicit | Medium | High (Customizable) |
| **Privacy** | Standard | Standard | High (Enterprise Grounding) | Standard | Absolute (Sovereign) |
| **Best For** | Strategy, Legal, Complex Synthesis | Market Research, News, Summaries | Corporate Intelligence, Internal Data | Crisis Monitoring, Sentiment, Finance | Regulated Industries, High-Volume |

## 7. Implementation Guide for Self-Hosted Agents

For organizations opting for the self-hosted route, the architecture of late 2025 has converged on the Model Context Protocol (MCP) and modular components.

### 7.1 The "Bring Your Own Tools" (BYOT) Stack

**Reasoning Core**: DeepSeek-R1 or Qwen3-Thinking are the current state-of-the-art open weights for reasoning. They provide the necessary "thinking" capabilities to plan research steps.

**Orchestration**: Hugging Face Smolagents for Python-centric workflows. Its efficiency in token usage (30% less than JSON) directly translates to faster, cheaper research.

**Search Layer**: Tavily or SerpAPI. These are the "eyes" of the agent. Tavily is specifically optimized for LLMs, returning clean text rather than raw HTML.

**Browser**: A headless browser (e.g., Playwright) orchestrated by the agent is essential for scraping deep web content that is rendered via JavaScript and invisible to simple cURL requests.

**Memory**: ChromaDB or Redis for storing the "Research State"—the intermediate findings, visited URLs, and discarded hypotheses.

### 7.2 Harness Design Patterns for Deep Research

Recent harness-engineering work suggests several practical design constraints for deep research builders:

- **Treat the filesystem as durable memory**: Long-horizon research produces more material than can fit in context. Store search logs, source excerpts, extracted datasets, failed hypotheses, drafts, and citation maps as files so the agent can recover, audit, and selectively re-read its own history.
- **Make workflow loops explicit**: A robust research agent should expose a plan-execute-observe-improve loop, with clear checkpoints for source coverage, contradiction handling, and synthesis quality instead of relying on a single prompt template.
- **Use inspectable parallelism**: Subagents and backend jobs are useful for source discovery, perspective generation, and independent verification, but their outputs should land in durable logs or artifacts rather than transient chat context.
- **Engineer context, not just prompts**: Context construction should select, compress, and structure relevant evidence. The useful optimization target shifts from prompt wording to retrieval, filtering, formatting, and state-management code.
- **Gate self-improvement with evaluation**: Harness changes should be proposed from recurring verifier-grounded failure patterns, then accepted only after held-in and held-out regression checks preserve known good behavior.

These patterns are especially relevant to self-hosted systems because the harness is the part teams can actually modify. The model supplies reasoning ability, but the harness determines whether that ability is connected to the right tools, evidence, memory, and feedback loop.

### 7.3 Challenges of Self-Hosting

**Web Fragility**: The web is hostile to bots. Custom agents require constant maintenance to update scrapers as websites change their DOM structures or anti-bot protections (Cloudflare).

**Context Management**: Managing the context window is an art. Agents often fill their context with irrelevant boilerplate from websites (navbars, footers), degrading reasoning performance. Effective "chunking" and re-ranking strategies are required.

## 8. Future Outlook and Implications

The Deep Research landscape is evolving rapidly. We can anticipate several key trends heading into 2026.

### 8.1 The Commoditization of Logic

As open models like DeepSeek-R1 and Qwen3 close the gap with OpenAI's o3, the premium for "pure reasoning" will collapse. The value will shift to proprietary context. The most valuable agents will be those that have unique access to gated data—whether that's xAI's access to X, Google's access to your Drive, or a vertical agent's access to a Bloomberg terminal.

### 8.2 Statefulness and "Research Associates"

The "Cached Input" pricing models from OpenAI and Google signal a shift toward stateful interactions. We will move away from "one-shot" queries to persistent "Research Associates." An enterprise will load its entire strategic history into the model's cache, allowing the agent to perform research with deep historical context of the company's prior decisions.

### 8.3 The "Agentic Web"

As agents become the primary consumers of information, the web itself will adapt. We will likely see a rise in "Agent-First" web design—websites publishing content in clean Markdown or JSON-LD specifically to be consumed by Deep Research bots, bypassing the messy HTML meant for human eyes.

## Conclusion

The Deep Research ecosystem of 2025 is a diverse and maturing landscape. For pure reasoning power on complex, low-volume tasks, OpenAI's o3-deep-research remains the gold standard. For high-volume, fact-centric research, Perplexity Sonar offers an unbeatable value proposition. Google Gemini dominates the enterprise intranet, while xAI rules real-time social signals. However, for those who demand sovereignty, the open-source stack—led by tools like DR-Tulu and Smolagents—has finally reached a level of maturity where it is a viable, and often superior, alternative to the walled gardens. The choice is no longer about capability, but about control, cost, and the specific nature of the data being researched.

## References

- [O3-Deep-Research - Model - OpenAI API](https://platform.openai.com/docs/models/o3-deep-research)
- [A Developer's Guide to the OpenAI Deep Research API - Apidog](https://apidog.com/blog/openai-deep-research-api/)
- [Pricing - OpenAI API](https://platform.openai.com/docs/pricing)
- [Rate limits - OpenAI API](https://platform.openai.com/docs/guides/rate-limits)
- [Sonar deep research - Perplexity](https://docs.perplexity.ai/getting-started/models/models/sonar-deep-research)
- [Pricing - Perplexity](https://docs.perplexity.ai/getting-started/pricing)
- [Gemini Enterprise release notes - Google Cloud Documentation](https://docs.cloud.google.com/gemini/enterprise/docs/release-notes)
- [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 3 Pro Costs & Gemini 3 API Costs: Latest Insights for 2025 - GlobalGPT](https://www.glbgpt.com/hub/gemini-3-pro-costs-gemini-3-api-costs-latest-insights-for-2025/)
- [A new era of intelligence with Gemini 3 - Google Blog](https://blog.google/products/gemini/gemini-3/)
- [An unofficial (self-hosted) API tunnel that provides access to Grok3 through a simple REST interface - GitHub](https://github.com/TheSethRose/Grok3-Tunnel)
- [Models and Pricing - xAI API](https://docs.x.ai/docs/models)
- [xAI pricing explained: A complete guide for 2025 - eesel AI](https://www.eesel.ai/blog/xai-pricing)
- [Introducing Claude Opus 4.5](https://www.anthropic.com/news/claude-opus-4-5)
- [Getting Started with the Manus Agent API (Full Code, Tips & Costing) - Md Mazaharul Huq](https://jewelhuq.medium.com/getting-started-with-the-manus-agent-api-full-code-tips-costing-eef90bacd06c)
- [Manus AI Pricing: A Detailed Breakdown of Each Plan - Lindy](https://www.lindy.ai/blog/manus-ai-pricing)
- [LangChain - GitHub](https://github.com/langchain-ai)
- [langchain-ai/langgraph: Build resilient language agents as graphs - GitHub](https://github.com/langchain-ai/langgraph)
- [langchain-ai/open_deep_research - GitHub](https://github.com/langchain-ai/open_deep_research)
- [Open-source DeepResearch – Freeing our search agents](https://huggingface.co/blog/open-deep-research)
- [Manus API: Overview](https://open.manus.ai/docs)
- [Allen Institute for AI (AI2) Releases DR Tulu: Fully Open Source AI Agent for Expert Level Deep Research - Reddit](https://www.reddit.com/r/aicuriosity/comments/1p1dxpv/allen_institute_for_ai_ai2_releases_dr_tulu_fully/)
- [DR Tulu: An open, end-to-end training recipe for long-form deep research](https://allenai.org/blog/dr-tulu)
- [DR Tulu: Open models + training recipe for long-form deep research agents - Reddit](https://www.reddit.com/r/allenai/comments/1p0fb25/dr_tulu_open_models_training_recipe_for_longform/)
- [stanford-oval/storm: An LLM-powered knowledge curation system that researches a topic and generates a full-length report with citations - GitHub](https://github.com/stanford-oval/storm)
- [Releases · stanford-oval/storm - GitHub](https://github.com/stanford-oval/storm/releases)
- [STORM - Stanford University](https://storm.genie.stanford.edu/)
- [DeepResearcher: Scaling Deep Research via Reinforcement Learning in Real-world Environments - arXiv](https://arxiv.org/pdf/2504.03160)
- [Alibaba-NLP/DeepResearch: Tongyi Deep Research, the Leading Open-source Deep Research Agent - GitHub](https://github.com/Alibaba-NLP/DeepResearch)
- [GAIR-NLP repositories - GitHub](https://github.com/orgs/GAIR-NLP/repositories)
- [AgentRxiv](https://agentrxiv.github.io/)
- [AgentRxiv: Towards Collaborative Autonomous Research - arXiv](https://arxiv.org/html/2503.18102v1)
- [SamuelSchmidgall/AgentLaboratory: Agent Laboratory is an end-to-end autonomous research workflow meant to assist you as the human researcher toward implementing your research ideas - GitHub](https://github.com/SamuelSchmidgall/AgentLaboratory)
- [Humanity's Last Exam - arXiv](https://arxiv.org/abs/2501.14249)
- [Humanity's Last Exam - Scale AI](https://scale.com/leaderboard/humanitys_last_exam)
- [LLM Leaderboard 2025 - Vellum AI](https://www.vellum.ai/llm-leaderboard)
- [Deep Research model achieves 26.6% on Humanity's Last Exam! - Reddit](https://www.reddit.com/r/singularity/comments/1igbvp7/deep_research_model_achieves_266_on_humanitys/)
- [Ultimate Guide - The Best Open Source LLM for Deep Research in 2025 - SiliconFlow](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-deep-research)
- [Harness Engineering for Self-Improvement - Lilian Weng](https://lilianweng.github.io/posts/2026-07-04-harness/)

