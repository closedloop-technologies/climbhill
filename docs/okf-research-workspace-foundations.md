# OKF Research Workspace Foundations

This note records the source constraints for a future `climbhill research`
workspace. It is a design reference, not a replacement for the upstream OKF
specification.

## Normative Source: Open Knowledge Format

The upstream [Open Knowledge Format (OKF) v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
defines a knowledge bundle as a directory tree of UTF-8 Markdown documents
with YAML frontmatter. Every non-reserved Markdown file is a concept and must
have a non-empty `type`; `index.md` and `log.md` are reserved filenames.

For a research workspace, keep the conformant OKF bundle separate from its
non-OKF control artifacts. The selected control repository owns the job data:

```text
<control-repository>/
└── .climbhill/
    └── <job-slug>-<uuid-suffix>/
        ├── job.yaml             # target, control, objective, and budgets
        ├── research/
        │   ├── raw/             # immutable evidence; not an OKF bundle
        │   └── okf/             # conformant, versionable knowledge bundle
        │       ├── index.md
        │       ├── log.md
        │       ├── resources/
        │       ├── observations/
        │       ├── entities/
        │       ├── claims/
        │       ├── relationships/
        │       ├── topics/
        │       ├── reports/
        │       └── method.md
        ├── runs/                # recursive plans, candidates, and decisions
        └── cache/
            └── registry.sqlite  # rebuildable query cache; not canonical
```

`raw/` is deliberately immutable evidence, rather than an OKF concept tree:
store the original PDF, transcript, downloaded HTML, and retrieval metadata
there. Each item in `okf/resources/` is the OKF concept that describes and
links to the corresponding raw artifact. This preserves exact retrieval
evidence while keeping the knowledge graph readable and versionable.

Every derived concept should use the upstream provenance and lifecycle fields:

```yaml
---
type: Research Claim
title: Model X action-policy rate
resource: ../../raw/arxiv/2401.01234v2/paper.pdf
sources:
  - id: paper-p7
    resource: /resources/arxiv-2401-01234v2.md
    title: "Paper source and page 7 locator"
generated:
  by: climbhill-derive/<model-and-prompt-version>
  at: 2026-08-19T00:00:00Z
status: draft
---
```

The body attributes individual statements with a Markdown footnote keyed to
`sources[].id`, as specified by OKF. A resource concept in turn records the
external URL, bundle-relative raw path, author/publisher where available, and
retrieval metadata. Store hashes and retrieval-specific fields as producer
extensions: OKF allows unknown frontmatter keys and requires consumers to
preserve them.

## Job and CLI Contract

`climbhill init` initializes one globally unique job for one target Git
repository. The human-readable job slug receives a UUID-style suffix. Its
storage interface is:

```text
climbhill init --target <repo> --control <repo> --location <worktree-base> --job <slug>
```

`--target` selects the repository being improved. `--control` selects the Git
repository that persists `.climbhill/<job-id>/`. `--location` selects the local
base directory for the control worktree and is not committed as part of the
portable job identity.

When target and control are different repositories, the second repository is
the independent control plane. When they resolve to the same Git repository,
ClimbHill operates in recursive self-control (Ouroboros) mode: it creates the
long-lived branch `climbhill/<job-id>` and checks it out in a separate worktree
under `<location>/<job-id>/`. Research, runs, and other control state are committed
on that branch under `.climbhill/<job-id>/`, while the primary target worktree
remains on its implementation branch. The target records the portable job ID,
control repository identity, and control branch, never the absolute worktree
path.

The version-controlled filesystem is canonical. `cache/registry.sqlite` is a
rebuildable local index and should be ignored by Git rather than treated as the
source of truth for recursive history.

The primary workflow is deliberately explicit:

```text
climbhill init -> climbhill add -> climbhill derive -> climbhill graph build -> climbhill research
```

- `climbhill add <url-or-file>` retrieves one source, stores its immutable raw
  representation, creates its resource concept, and runs the default
  derivation. `--no-derive` performs ingestion only.
- `climbhill derive` enriches one or more raw resources. `--append-prompt TEXT`
  extends the default Bloom-based prompt; `--prompt-file PATH` replaces the
  default extraction prompt with a versioned file. The resolved prompt is part
  of the derivation identity.
- `climbhill graph build` explicitly performs ontology detection, entity
  resolution, deduplication, relationship normalization, and confusion or
  contradiction recording while preserving every source-local observation.
  `climbhill research` does not run graph reconciliation implicitly.
- `climbhill research QUESTION` is the bounded agentic discovery loop. It
  persists the question, plan, searches, newly acquired sources, derivations,
  answer, costs, partial work, and stopping reason. `--local-only` prohibits
  new retrieval. API-cost and wall-time budgets stop cleanly rather than
  discarding work in progress.

The control repository configures `.climbhill/<job-id>/research/raw/**` for Git
LFS when Git LFS is available. When it is unavailable, initialization adds the
raw directory to `.gitignore` and writes a visible note explaining that raw
evidence is local only and how to switch to Git LFS later. Users may delete
raw artifacts; any derived concepts that reference them then remain readable but no longer
resolvable to their original evidence.

Implementation consequences:

- `climbhill add` is ingestion of one source: select a retriever by input
  type, write immutable raw bytes/text and retrieval metadata, create or
  update the resource concept, then invoke the default derivation.
- A YouTube retriever stores the transcript as raw evidence plus retrieval
  metadata such as canonical URL, video ID, title, channel, publication date,
  and retrieval time. The transcript is not itself interpreted by the
  retriever.
- An arXiv retriever stores the versioned source identity and original PDF;
  `derive` may later extract text, page locators, entities, and claims without
  replacing the PDF.
- `climbhill derive` must be idempotent for an identical raw-artifact hash and
  derivation configuration: a cache hit makes no semantic change, including
  no change to `generated.at`. A changed prompt/model/schema creates a
  distinct derivation identity and updates `generated`, rather than mutating
  raw evidence.
- `index.md` is generated for progressive disclosure and `log.md` records
  chronological additions, derivations, supersessions, and failures.

## Derivation Profiles

A derivation profile is the versioned recipe that turns raw evidence into
source-local observations. It records the model selection, extraction prompt,
Bloom-based output policy, concept schema version, chunking behavior, and
source-locator requirements. Each run also records the concrete provider and
model resolved from any configured default.

The derivation identity is computed from the raw content hash and the resolved
profile, including its prompt, model, and schema. An identical identity is a
cache hit. A changed prompt, model, or schema produces a distinct derivation
without overwriting the earlier output.

Derivation does not create canonical graph entities. It emits source-local
entity mentions, attributed claims and opinions, procedures, recommendations,
relationships, terminology, and research gaps with exact locators. The
explicit graph-building step reconciles those observations into a deduplicated
ontology while retaining provenance and unresolved ambiguity.

OKF does not prescribe a fixed ontology, a storage system, an agent runtime,
or a plugin interface. `Research Resource`, `Research Claim`, `Entity`, and
`Relationship` are therefore ClimbHill producer-defined `type` values and
must remain understandable to consumers that do not know them.

## Bloom-Based Enrichment Policy

Bloom's taxonomy is an instructional framework, not an evidence schema. The
revised cognitive-process ordering commonly used in teaching is **remember,
understand, apply, analyze, evaluate, create**. The original source is Bloom,
Englehart, Furst, Hill, and Krathwohl (1956), *Taxonomy of Educational
Objectives: Handbook I: Cognitive Domain*; the revision is Anderson and
Krathwohl (2001), *A Taxonomy for Learning, Teaching, and Assessing*. The supplied
[Intentional College Teaching article](https://intentionalcollegeteaching.org/2021/04/30/blooms-taxonomy-benefits-and-limitations/)
is a secondary source that usefully emphasizes both its planning value and its
limitations; the supplied [Wikipedia overview](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy)
is background only. Treat the primary OKF spec as authoritative for file
format behavior.

For transcript and document derivation, use Bloom to select *derived outputs*,
not to inflate the confidence of a statement:

| Bloom lens | ClimbHill output | Evidence rule |
| --- | --- | --- |
| Remember | named entities, dates, definitions, direct factual statements | include source locator |
| Understand | speaker's claims, opinions, explanations, terminology | label speaker assertion or interpretation |
| Apply | procedures, workflows, implementation steps | preserve ordering and prerequisites |
| Analyze | relationships, comparisons, assumptions, causal claims | represent links to supporting claims separately |
| Evaluate | tips, best practices, tradeoffs, limitations | retain attribution; do not promote advice to fact |
| Create | research gaps, follow-up questions, synthesis/report candidates | mark as agent-derived and cite the supporting concepts |

This turns the existing YouTube instruction into an OKF-compatible contract:
extract entities and relationships; key facts and opinions; procedural
knowledge and workflows; and expert tips, tricks, and best practices. Each
output is a typed concept or a section of a typed resource concept, carries
its source concept and precise timestamp/page/heading locator, and records
the derivation actor, timestamp, and prompt/version.

## Design Guardrails

- Never overwrite downloaded evidence during derivation; retrieve a new raw
  version when the source changes and link/supersede at the resource layer.
- Keep asserted facts, opinions, inference, and unanswered questions in
  distinct claim statuses or concept types.
- `research` may acquire novel web evidence, but it must ingest it through the
  same `add` path before relying on it, then cite local resource/claim
  concepts in its answer.
- `research` loops must be bounded and log each query, retrieval, derivation,
  and stopping reason in the workspace.
- Use `verified` only for actual machine or human verification events. A
  model-generated extraction without verification is an unverified OKF
  concept, regardless of how plausible it reads. Verification is optional.

## Vendored Specification

ClimbHill should vendor the complete upstream OKF v0.2 specification under
`docs/specifications/` and record its canonical URL, upstream commit, retrieval
date, checksum, and license beside it. The vendored snapshot is the offline
implementation reference; the upstream URL remains the authority used to
detect newer versions.

## Sources

- **Normative format:** [Open Knowledge Format specification, v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- **Bloom framework, secondary:** [Benefits and limitations of Bloom's Taxonomy](https://intentionalcollegeteaching.org/2021/04/30/blooms-taxonomy-benefits-and-limitations/)
- **Bloom background, secondary:** [Bloom's taxonomy](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy)
