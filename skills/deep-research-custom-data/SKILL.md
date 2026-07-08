---
name: deep-research-custom-data
description: Build and validate custom-corpus inputs for deep research from Google Docs, YouTube, local files, S3, arXiv, databases, Slack, email, tickets, and similar non-web sources. Use when preparing private or domain-specific source manifests, validating source safety, or turning custom data into cited research inputs.
---

# Custom Data Deep Research

Use this skill when the research corpus is not just the open web. The goal is to
turn private, semi-structured, or domain-specific sources into a cited corpus
that a deep research agent can inspect safely.

## Workflow

1. Define the research question and allowed sources.
2. Export or read sources with read-only credentials.
3. Convert each source into markdown or JSON plus metadata.
4. Build an evidence manifest with stable IDs and offsets.
5. Run the research agent over the allowed corpus.
6. Normalize the report, findings, uncertainties, and method into OKF.

## Source Guidance

| Source | How to Use | Citation Anchor |
| --- | --- | --- |
| Google Docs / Drive | Search/read Drive files, export Docs, preserve file IDs and revision times. | file ID, title, URL, heading, revision timestamp |
| YouTube | Pull transcript and metadata; prefer official captions. | video URL, channel, upload date, timestamp range |
| Local files | Crawl only allowlisted paths, hash files, convert PDFs/docs/text. | relative path, sha256, modified time, page/line/heading |
| S3 | Use read-only IAM, sync scoped prefixes, save object manifest. | `s3://bucket/key`, version ID, ETag, row/page/byte offset |
| arXiv | Fetch metadata and PDFs by arXiv ID and version. | arXiv ID/version, authors, section/page |
| Databases / CSV | Export query, schema, row counts, and sampled/aggregate evidence. | query ID, table, primary key, aggregate definition |

## Prompt Contract

```text
Research question:
<question>

Allowed corpus:
<source IDs or OKF bundle paths>

Rules:
- Use only allowed sources unless public web supplementation is explicitly requested.
- Cite source ID plus exact anchor for every factual claim.
- Separate directly supported findings from inferences.
- Record missing, conflicting, stale, or low-confidence evidence.
- Return an OKF-compatible report.
```

## Manifest Validation

Create a JSON manifest before indexing custom data. Validate it with:

```bash
python .agents/skills/deep-research-custom-data/scripts/validate_manifest.py \
  staging/custom-corpus/manifest.json
```

The validator checks corpus metadata, supported source types, stable source IDs,
and citation anchors before a research agent uses the corpus.

Use `docs/examples/custom-data-corpus.example.json` as the minimal fixture for
benchmark and CI validation.

## OKF Output

Use concept files for source records and research outputs:

- `sources/<source-id>.md` with type such as `Google Drive Document`,
  `YouTube Transcript`, `Local File Evidence`, `S3 Object Evidence`, or
  `Scholarly Paper`.
- `claims/claim-register.md` with type `Evidence Claim Register`.
- `method.md` with type `Research Method`.
- `report.md`, `findings.md`, and `uncertainties.md` for the final research
  output.

See `docs/custom-data-sources.md` for detailed extraction and governance
guidance.

## Safety

- Confirm authorization before accessing private data.
- Use read-only credentials and scoped folders, prefixes, or queries.
- Do not commit raw private extracts unless the repository is approved for that
  data.
- Preserve retention/deletion requirements in `method.md`.
