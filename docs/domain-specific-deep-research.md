# Domain-Specific Deep Research Tools

Deep research systems should be categorized by both workflow pattern and domain
index. A tool that searches the open web is different from a tool that searches
financial filings, clinical literature, legal sources, or private enterprise
documents. Domain-specific tools can improve retrieval quality, but they also
raise the bar for citation verification and cost control.

## Categories

| Domain | What the Index Should Cover | Good Fit | Verification Requirements |
| --- | --- | --- | --- |
| General web research | Open web pages, news, documentation, product pages, public reports | Provider landscape scans, current-event summaries, broad explainers | Source dates, publisher quality, conflicting claims |
| Finance | SEC filings, earnings transcripts, fundamentals, price data, macro indicators, financial news | Earnings summaries, due diligence, competitor benchmarking, macro research | Primary filings, exact period/ticker, compliance-sensitive caveats |
| Medicine and life sciences | PubMed/clinical literature, guidelines, trial registries, drug labels, regulatory updates | Literature surveys, trial landscape maps, evidence summaries | No medical advice, evidence grade, date/guideline version, primary source links |
| AI for science | Papers, benchmarks, datasets, lab/project pages, code repositories | Agent/system comparisons, scientific workflow mapping, validated-use scans | Distinguish demos from validated systems, cite papers and benchmark versions |
| Legal and regulatory | Statutes, regulations, agency guidance, case law, standards, filings | Revision status, obligations mapping, policy analysis | Jurisdiction, effective date, authoritative source, non-legal-advice caveat |
| Enterprise/internal data | Google Docs, local files, S3, tickets, Slack, databases, PDFs | Company-specific synthesis, incident retrospectives, internal decision support | Allowlisted corpus, stable IDs, access authorization, source manifest |
| Social/news/market sentiment | News feeds, social posts, X/Twitter, community discussions | Crisis monitoring, sentiment briefs, rumor tracking | Time windows, source volatility, bot/spam risk, quote preservation |

## You.com Finance Research

You.com Finance Research is a domain-specific deep research API. It uses the
same request/response shape as the general Research API, but searches a
finance-optimized index rather than the open web. The documented index includes
company fundamentals, equity and commodity prices, private company metrics,
alternative signals, macroeconomic indicators, SEC filings, earnings
transcripts, analyst coverage, and financial news.

Use cases:

- earnings analysis;
- competitive benchmarking;
- due diligence research;
- macroeconomic research;
- regulatory and filing analysis.

Command:

```bash
op run --env-file .env.adr -- python .agents/skills/deep-research-you/scripts/you_research.py \
  --api finance \
  --prompt "Compare the gross margins of Apple, Microsoft, and Google over the past three fiscal years." \
  --research-effort deep
```

Endpoint: `https://api.you.com/v1/finance_research`.

Cost note: You.com Finance Research starts at `deep`, not `lite`, and is priced
by effort tier. Keep finance prompts scoped, run one question at a time, and
verify the reported or estimated cost before adding it to the under-`$1`
benchmark suite.

## Benchmark Guidance

Use the general benchmark categories for cross-provider comparison, and add
domain-specific categories only when the provider exposes a domain index or the
task requires domain-specialized sources.

Recommended domain benchmark prompts:

- Finance: `Use finance-specific sources to summarize the latest reported
  drivers of NVIDIA data center revenue growth.`
- Medicine: `Survey recent guideline-backed evidence for one named clinical
  intervention, with trial and guideline citations.`
- AI for science: `Compare two AI-for-science agents or systems and separate
  validated scientific use from demonstrations.`
- Regulatory: `Find the current authoritative revision of one named technical
  standard and summarize what changed.`
- Enterprise/internal: `Using only the provided source manifest, identify the
  main unresolved decisions and cite source IDs.`

Normalize domain-specific outputs to OKF with domain-specific source concepts,
such as `SEC Filing`, `Clinical Guideline`, `Research Paper`, `Regulatory
Standard`, or `Internal Document`. Keep assumptions and compliance caveats in
`uncertainties.md`.
