# Normalizing Deep Research Outputs with OKF

This repository uses Google's Open Knowledge Format draft as the target shape
for normalized deep research outputs. OKF v0.1 is intentionally small: a bundle
is a directory of markdown concept files with YAML frontmatter, and every
non-reserved concept file has a non-empty `type` field.

## Why OKF Fits Deep Research

Deep research outputs are hard to compare when each provider returns a different
report shape. OKF gives the benchmark a stable interchange layer:

- markdown remains readable in git diffs and code review;
- frontmatter lets tools route concepts by `type`;
- `index.md` gives humans and agents a quick map;
- `log.md` records refreshes of time-sensitive research;
- citations remain plain markdown links.

## Repository Bundle Convention

Each benchmark run can be normalized into:

```text
benchmark/results/okf/<skill>/<task>/
├── index.md
├── report.md
├── findings.md
├── uncertainties.md
├── method.md
└── log.md
```

Concept types used by this repo:

| File | `type` | Purpose |
| --- | --- | --- |
| `report.md` | `Research Report` | Raw or lightly normalized provider output |
| `findings.md` | `Research Findings` | Claim-like findings and citation-bearing lines |
| `uncertainties.md` | `Uncertainty Register` | Caveats, conflicting claims, assumptions, stale-data risks |
| `method.md` | `Research Method` | Prompt, provider, cost controls, and run metadata |

## Minimum Conformance Check

A normalized bundle is acceptable when:

1. every concept file except `index.md` and `log.md` starts with YAML
   frontmatter;
2. every frontmatter block includes a non-empty `type`;
3. citations or source URLs from the provider output are preserved;
4. assumptions and uncertainty language are not mixed into findings as if they
   were verified facts;
5. `method.md` records the provider, prompt, and cost-control assumptions.

Validate a bundle with:

```bash
python .agents/skills/deep-research-okf-normalize/scripts/validate_okf.py \
  benchmark/results/okf/<skill>/<task>
```

## Sources

- [Open Knowledge Format specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [Google Cloud: How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
