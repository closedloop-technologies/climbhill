---
name: deep-research-okf-normalize
description: Normalize raw deep research outputs into a compact Open Knowledge Format bundle with source, finding, uncertainty, method, index, and log concepts. Use after provider runs when reports need portable structured markdown and citation-preserving validation.
---

# OKF Normalize Research

Use this skill after a deep research agent returns a report. It turns a raw
report into a portable markdown bundle aligned with Google's Open Knowledge
Format draft: markdown files with YAML frontmatter, a required `type` field,
optional `index.md` and `log.md`, and citations preserved as links where
possible.

## Command

```bash
python .agents/skills/deep-research-okf-normalize/scripts/normalize_to_okf.py \
  --input benchmark/results/perplexity-sonar/meta/q1_output.txt \
  --bundle-dir benchmark/results/okf/perplexity-sonar-meta
```

For ad-hoc text:

```bash
python .agents/skills/deep-research-okf-normalize/scripts/normalize_to_okf.py \
  --title "Deepresearch the deepresearchers" \
  --text "Paste or pipe the report text here" \
  --bundle-dir outputs/okf/deepresearchers
```

## Bundle Shape

The generated bundle contains:

- `index.md` - progressive-disclosure entrypoint.
- `report.md` - the normalized source report concept.
- `findings.md` - extracted claim bullets and citation-bearing lines.
- `uncertainties.md` - caveats, conflicts, missing evidence, and stale-data
  risks.
- `method.md` - provider, prompt, timestamp, and normalization notes.
- `log.md` - update history.

## Validation

```bash
python .agents/skills/deep-research-okf-normalize/scripts/validate_okf.py \
  benchmark/results/okf/perplexity-sonar-meta
```

## Normalization Rules

- Preserve raw claims before improving prose.
- Keep citations as markdown links or source URLs.
- Mark assumptions separately from measurements or cited facts.
- Prefer concise concept files over one large report.
- Do not reject unknown frontmatter fields when consuming an OKF bundle.
