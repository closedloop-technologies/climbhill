# Deep Research on Custom Data Sources

Custom-source deep research is different from open-web research. The agent must
prove where each claim came from, respect access boundaries, preserve document
identity, and avoid mixing private-source claims with public-source claims
without labeling them.

## Pipeline

Use the same pipeline regardless of source:

1. Scope: define the research question, allowed sources, forbidden sources, and
   time window.
2. Inventory: list source systems, owners, credentials, update cadence, and
   export limits.
3. Extract: pull source records into a local staging area without modifying the
   originals.
4. Normalize: convert documents, transcripts, objects, and papers into markdown
   or JSON with stable source metadata.
5. Index: chunk text with source IDs, timestamps, titles, and page/time/object
   offsets.
6. Research: run a planner/retriever/reader/synthesizer loop over the indexed
   corpus.
7. Cite: cite source IDs plus exact anchors such as page numbers, timestamps,
   S3 keys, Drive file IDs, or arXiv IDs.
8. Package: normalize the final report and evidence register into OKF.

## Source Patterns

| Source | Extraction Pattern | Required Citation Anchor |
| --- | --- | --- |
| Google Docs / Drive | Export Docs as Markdown, text, or PDF through Drive API or connector; preserve file ID and revision time. | Drive file ID, title, URL, revision timestamp, heading or paragraph quote |
| YouTube | Capture transcript, video metadata, channel, upload date, and URL. Use official captions where possible. | Video URL, channel, upload date, timestamp range |
| Local files | Walk allowed directories, hash files, convert supported formats, and record relative path. | File path, content hash, modified time, page/line/heading |
| S3 buckets | List scoped prefixes, copy read-only snapshots, record bucket/key/version/ETag. | `s3://bucket/key`, version ID when available, ETag, byte/page/row offset |
| arXiv | Use arXiv IDs, metadata, abstracts, PDFs, and version numbers. | arXiv ID, version, title, authors, PDF page or section |
| Databases / CSV | Export query text, schema, row counts, and sampled or aggregate evidence. | Database/table/query ID, row primary key or aggregate definition |
| Slack / email / tickets | Use approved exports or APIs; preserve message IDs, authors, timestamps, and thread IDs. | Message/thread ID, timestamp, channel/project, author when permitted |

## Manifest

Before indexing, create a manifest that names the corpus, research question,
allowed sources, and per-source citation anchors:

```json
{
  "corpus_id": "market-analysis-2026",
  "research_question": "What do our planning docs and source literature say about this market?",
  "allowed_sources": ["gdoc-product-plan", "youtube-interview-abc123", "arxiv-2401-01234v2"],
  "sources": [
    {
      "source_id": "gdoc-product-plan",
      "source_type": "google_drive",
      "title": "Product planning notes",
      "citation_anchor": "Drive file ID plus heading",
      "file_id": "1abc...",
      "web_url": "https://docs.google.com/document/d/1abc...",
      "modified_time": "2026-06-23T12:00:00Z"
    }
  ]
}
```

Validate the manifest before synthesis:

```bash
python .agents/skills/deep-research-custom-data/scripts/validate_manifest.py \
  staging/custom-corpus/manifest.json
```

The repository includes `docs/examples/custom-data-corpus.example.json` as a
minimal mixed-source manifest. The benchmark uses that fixture for the
zero-cost `deep-research-custom-data` validation smoke.

## Google Docs and Drive

For Google Docs, treat the Drive file ID as the canonical resource. Export each
document to a staging directory and write a sidecar metadata file:

```json
{
  "source_type": "google_drive",
  "file_id": "1abc...",
  "title": "Research notes",
  "mime_type": "application/vnd.google-apps.document",
  "web_url": "https://docs.google.com/document/d/1abc...",
  "modified_time": "2026-06-23T12:00:00Z",
  "export_format": "text/markdown"
}
```

When using the Google Drive connector, first search/read the candidate files,
then ask the research agent to cite file IDs and headings. Do not cite only
generic phrases such as "the document says"; cite the document title and stable
file ID.

## YouTube

Use transcripts as the research text and retain time ranges:

```json
{
  "source_type": "youtube",
  "video_id": "abc123",
  "url": "https://www.youtube.com/watch?v=abc123",
  "title": "Interview",
  "channel": "Example Channel",
  "published_at": "2026-01-01",
  "segments": [
    {"start": 83.2, "end": 101.4, "text": "Quoted transcript text"}
  ]
}
```

If automatic captions are used, mark them as machine-generated and lower the
confidence of exact wording claims.

## Local Files

Limit the crawler to explicit directories. Store a manifest before indexing:

```json
{
  "source_type": "local_file",
  "path": "docs/research/report.pdf",
  "sha256": "...",
  "modified_time": "2026-06-20T09:12:00Z",
  "converter": "pypdf"
}
```

Never let the agent traverse home directories or mounted drives without an
allowlist. For private files, keep raw extracts out of committed benchmark
results unless the repository is explicitly private and approved for that data.

## S3

Use read-only credentials and a prefix allowlist:

```bash
aws s3 sync s3://bucket/research-prefix/ staging/s3/research-prefix/ \
  --only-show-errors
aws s3api list-object-versions --bucket bucket --prefix research-prefix/ \
  > staging/s3/research-prefix/manifest.json
```

Record bucket, key, version ID, ETag, size, and last-modified time. For CSV,
Parquet, or JSONL objects, cite row keys or aggregate query definitions.

## arXiv

Use arXiv IDs as stable resources. Preserve title, authors, abstract, primary
category, version, submitted/updated timestamps, and PDF URL. When citing a
paper, cite the version that was read, for example `arXiv:2401.01234v2`.

## OKF Bundle Layout

Represent a custom corpus as an OKF bundle before running synthesis:

```text
custom-corpus-okf/
├── index.md
├── sources/
│   ├── google-drive-1abc.md
│   ├── youtube-abc123.md
│   ├── local-report.md
│   ├── s3-bucket-key.md
│   └── arxiv-2401-01234v2.md
├── claims/
│   └── claim-register.md
├── method.md
└── log.md
```

Suggested concept types:

| Concept | `type` |
| --- | --- |
| Google Doc | `Google Drive Document` |
| YouTube transcript | `YouTube Transcript` |
| Local file | `Local File Evidence` |
| S3 object | `S3 Object Evidence` |
| arXiv paper | `Scholarly Paper` |
| Claim register | `Evidence Claim Register` |
| Research method | `Research Method` |

## Research Prompt Template

```text
Research question:
<question>

Allowed corpus:
<list source bundle paths or source IDs>

Rules:
- Use only the allowed corpus unless public web supplementation is explicitly requested.
- Cite every factual claim with source ID plus page, heading, timestamp, row, or object key.
- Separate directly supported findings from inferences.
- Create an uncertainty register for missing, conflicting, stale, or low-confidence evidence.
- Return the report and evidence register in OKF-compatible markdown.
```

## Safety and Governance

- Confirm authorization before accessing private documents, buckets, channels,
  or local paths.
- Use read-only credentials and scoped prefixes/folders.
- Do not commit raw private source extracts unless approved.
- Keep secrets in 1Password or the relevant cloud secret manager.
- Redact personal data when the research question does not require it.
- Preserve source deletion or retention requirements in `method.md`.
