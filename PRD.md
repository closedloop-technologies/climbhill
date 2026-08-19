# ClimbHill Product Requirements Document

Status: Draft target implementation
Last updated: 2026-08-19
Primary interface: `climbhill` CLI
Distribution: npm, `npx skills`, and `climbhill.ai`

## 1. Executive Summary

ClimbHill is a local-first system for creating an agentic workflow that performs
a job at a new quality and efficiency bar. A user points ClimbHill at one Git
repository, defines a job to be done, gathers relevant evidence, derives
structured knowledge, runs bounded improvement attempts, evaluates candidates,
and preserves what was learned across recursive iterations.

The target product has three durable layers:

```text
research/       accumulated evidence and structured knowledge
runs/           recursive plans, candidates, evaluations, and decisions
target repo     promoted executable artifacts, including .agent/skills
```

The research layer follows Open Knowledge Format (OKF) v0.2. Agentic functions,
prompts, and structured outputs are defined in BAML. BAML generates the Python
and TypeScript clients required by the runtime. The primary CLI is distributed
through npm. Skills are distributed through `npx skills`. Frontend code uses
`remix@3.0.0-beta.10`, including the static GitHub Pages site under `www/`.

## 2. Problem

Coding agents can make useful one-off changes, but most repositories do not
provide the structure needed to improve repeatedly and safely. Agents commonly
lack:

- A stable job definition and success criteria.
- Relevant, cited, reusable background knowledge.
- Separation between raw evidence, source-local observations, and reconciled
  knowledge.
- Durable records of attempts, costs, failures, and decisions.
- A safe way to compare multiple candidates.
- A way to use lessons from one attempt in the next attempt.
- Explicit policy and budget controls.
- A clear promotion path from research to skills and code.

The result is opaque report generation, repeated research, lost failures,
untraceable claims, and agent behavior that does not improve with experience.

## 3. Job To Be Done

When I need a repository to perform a task at a materially higher quality and
efficiency bar, I want to create a version-controlled agentic workflow that
researches the problem, accumulates inspectable knowledge, tries bounded
solutions, evaluates them, and learns recursively, so that each iteration starts
from stronger evidence and history than the previous one.

## 4. Product Principles

1. **Local first.** The user owns the target repository, control repository,
   raw evidence, knowledge bundle, run history, and generated artifacts.
2. **Evidence before prose.** Research accumulates sources and structured
   knowledge; reports are derived views.
3. **Ingest, derive, reconcile.** Retrieval, source-local extraction, and graph
   construction are separate operations.
4. **Filesystem is canonical.** Version-controlled YAML and Markdown are the
   source of truth. SQLite is a rebuildable query cache.
5. **Provenance survives transformation.** Canonical entities and claims retain
   links to every contributing observation and exact source locator.
6. **Partial work is valuable.** Budget limits and failures stop cleanly and
   preserve all completed work.
7. **Skills are behavior, not memory.** `.agent/skills` contains executable
   procedures and supporting code. Research knowledge belongs in the control
   plane.
8. **Recursive, not autonomous by default.** ClimbHill preserves lineage and
   supports repeated improvement without silently merging or deploying changes.

## 5. Scope

### 5.1 In Scope

- One job targeting one Git repository.
- A separate or shared Git repository for control-plane persistence.
- Ouroboros mode, where target and control are the same repository.
- Source ingestion for local files, PDFs, webpages, YouTube, and arXiv.
- Bloom-based source enrichment through BAML.
- OKF v0.2 resources, observations, entities, claims, relationships, topics,
  and reports.
- Explicit ontology detection, entity resolution, and graph construction.
- Bounded web research and local-only research.
- Recursive candidate runs, evaluations, decisions, costs, and lineage.
- npm CLI distribution, `npx skills` distribution, and a Remix website.

### 5.2 Out of Scope For Initial Release

- Jobs spanning multiple target repositories.
- Mandatory human or machine verification of every concept.
- Automatic merge, deployment, or policy relaxation.
- A hosted agent cloud or hosted source-of-truth database.
- Real-time multi-user collaboration.
- Private SaaS connectors beyond the initial plugin interface.
- Deleting user data without an explicit user command.

## 6. Domain Model

| Term | Definition |
| --- | --- |
| Target repository | The Git repository ClimbHill is trying to improve. |
| Control repository | The Git repository that persists `.climbhill/<job-id>/`. |
| Location | Local base directory where the control branch worktree is checked out. It is not part of portable identity. |
| Job | One job to be done applied to one target repository. |
| Job ID | A human-readable slug with a UUID-style suffix that is globally unique. |
| Control branch | Long-lived `climbhill/<job-id>` branch containing versioned control-plane state. |
| Resource | An OKF concept describing one retrieved source and its raw artifact. |
| Observation | A source-local entity mention, claim, opinion, procedure, recommendation, relationship, term, or gap. |
| Graph concept | A canonical entity, claim, or relationship reconciled from one or more observations. |
| Run | A versioned execution record with inputs, outputs, costs, status, stopping reason, and optional parent lineage. |
| Candidate | One attempted change to the target repository within an improvement run. |
| Skill | Promoted executable agent behavior under `.agent/skills`. |

## 7. Persistence Model

The control repository owns the following structure:

```text
<control-repository>/
└── .climbhill/
    └── <job-slug>-<uuid-suffix>/
        ├── job.yaml
        ├── research/
        │   ├── raw/
        │   └── okf/
        │       ├── index.md
        │       ├── log.md
        │       ├── method.md
        │       ├── resources/
        │       ├── observations/
        │       ├── entities/
        │       ├── claims/
        │       ├── relationships/
        │       ├── topics/
        │       └── reports/
        ├── runs/
        │   ├── index.md
        │   └── <run-id>/
        │       ├── run.yaml
        │       ├── plan.md
        │       ├── research-delta.md
        │       ├── candidates/
        │       ├── evaluations/
        │       ├── decision.md
        │       └── reflection.md
        └── cache/
            └── registry.sqlite
```

The filesystem is canonical. `cache/registry.sqlite` is ignored and can be
rebuilt from `job.yaml`, OKF frontmatter, and run records.

Raw artifacts are immutable to derivation operations. If Git LFS is available,
`init` configures `.climbhill/<job-id>/research/raw/**` for LFS. Otherwise it
ignores the raw directory and writes visible instructions for enabling LFS.
Users may delete raw data; derived concepts then remain readable but their raw
evidence links may no longer resolve.

## 8. Persistence Modes

### 8.1 Split Control

The target and control repositories are different. The target contains code and
promoted skills. The control repository independently versions research and run
history.

### 8.2 Ouroboros

The target and control resolve to the same Git repository. ClimbHill creates
`climbhill/<job-id>` and checks it out as a separate worktree below `--location`.
The active target worktree remains on its implementation branch. Control-plane
commits and target implementation commits share the Git object database without
requiring the same checkout.

## 9. Primary CLI Interface

```text
climbhill init -> climbhill add -> climbhill derive -> climbhill graph build -> climbhill research
```

Existing candidate comparison and reporting commands remain available during
the migration and are adapted to the file-backed job model.

## 10. Functional Requirements

### FR-1: Initialize A Job

```text
climbhill init --target <repo> --control <repo> --location <path> --job <slug>
```

The command must:

1. Validate that target and control resolve to Git repositories.
2. Generate `<slug>-<uuid-suffix>` without colliding with an existing job.
3. Record target identity, control identity, objective, budgets, base commit,
   control branch, creation time, and schema versions in `job.yaml`.
4. Create `climbhill/<job-id>` and a separate control worktree at
   `<location>/<job-id>`.
5. Create `.climbhill/<job-id>/` in the control worktree.
6. Record a portable job pointer for discovery from the target repository
   without committing the absolute worktree path.
7. Configure Git LFS for raw artifacts when available.
8. Fall back to `.gitignore` plus a migration note when Git LFS is unavailable.
9. Refuse to overwrite or reuse an existing job unless an explicit recovery
   command is used.

Acceptance criteria:

- Split-control and Ouroboros integration tests create usable worktrees.
- Re-running the same invocation does not create a second ambiguous job.
- Moving the control worktree does not invalidate portable job identity.
- Target and control remain on their original active branches after init.

### FR-2: Add One Source

```text
climbhill add <url-or-file> [--type <type>] [--no-derive]
```

`add` retrieves exactly one logical source. It must:

1. Detect or accept an explicit source type.
2. Select a source adapter through a common interface.
3. Preserve the original bytes or text plus retrieval metadata under `raw/`.
4. Compute a content hash and stable resource identity.
5. Create or update an OKF resource concept with URL, author/publisher,
   publication time when known, retrieval time, raw path, content hash, and
   adapter metadata.
6. Run the default derivation unless `--no-derive` is present.
7. Preserve successful ingestion if derivation fails, mark the derivation
   failure, and exit nonzero.
8. Create a new immutable source version when the same logical source changes.

Initial adapters:

- Local file.
- PDF.
- Webpage.
- YouTube transcript and video metadata.
- arXiv metadata and original versioned PDF.

Acceptance criteria:

- Adding identical content twice does not duplicate raw bytes or concepts.
- A changed remote source creates a new version and does not mutate the old one.
- YouTube concepts include timestamp-addressable transcript evidence.
- PDF and arXiv concepts support page-addressable evidence.

### FR-3: Derive Source-Local Knowledge

```text
climbhill derive [--resource <id>] [--append-prompt <text>] [--prompt-file <path>]
```

Derivation must be implemented as typed BAML functions. The default profile
uses Bloom's revised cognitive lenses to extract:

- Named entities, dates, definitions, and directly stated facts.
- Attributed claims, opinions, explanations, and terminology.
- Procedures, workflows, prerequisites, and ordered steps.
- Source-local relationships, comparisons, assumptions, and causal claims.
- Expert recommendations, practices, tradeoffs, and limitations.
- Research gaps, follow-up questions, and synthesis candidates.

Every observation must retain the resource ID and an exact timestamp, page,
heading, or line locator when available. Derivation does not create canonical
graph entities.

The derivation identity must include:

```text
raw content hash + profile + resolved prompt + model + schema + chunking policy
```

`--append-prompt` extends the default prompt. `--prompt-file` replaces it with a
versioned custom prompt. An identical identity is a true cache hit and must not
change `generated.at`. A changed identity creates distinct output without
overwriting prior derivations.

Acceptance criteria:

- BAML generates working TypeScript and Python clients from the same functions.
- Structured output validates before it is written as OKF.
- Repeated identical derivation produces no Git diff.
- Model-generated output is unverified unless a separate verification event is
  recorded; verification is optional.

### FR-4: Build The Knowledge Graph

```text
climbhill graph build
climbhill graph inspect
```

Graph construction is explicit and must:

1. Detect or extend the job's ontology from source-local observations.
2. Resolve duplicate entity mentions into canonical entities.
3. Normalize relationship types and endpoints.
4. Reconcile matching, supporting, and conflicting claims.
5. Preserve links to every contributing observation and source locator.
6. Represent uncertain identity and contradictory evidence without forcing a
   merge.
7. Produce an inspectable summary of created, merged, unresolved, and
   superseded concepts.

Acceptance criteria:

- Rebuilding an unchanged graph is idempotent.
- Conflicting sources remain independently traceable.
- A user can inspect why two mentions were merged or kept separate.
- Graph construction never modifies raw evidence.

### FR-5: Run Bounded Research

```text
climbhill research <question> [--local-only] [budget options]
```

Research is a BAML-defined agentic loop. It must:

1. Inspect the existing OKF corpus before searching externally.
2. Create a plan and identify missing evidence.
3. In normal mode, use configured search/research skills to discover sources.
4. Ingest every relied-upon source through the same `add` interface.
5. Derive source-local observations through the same `derive` interface.
6. Produce an answer cited to local OKF concepts.
7. Persist the question, plan, searches, sources, derivations, answer, API cost,
   wall time, partial output, errors, and stopping reason.
8. Support `--local-only`, which prohibits external retrieval.
9. Stop cleanly when API-cost or wall-time budgets are reached.
10. Leave graph reconciliation explicit; `research` must not silently run
    `graph build`.

Acceptance criteria:

- A budget-limited run exits with a preserved, resumable partial state.
- Local-only mode performs no network retrieval.
- An answer cannot cite a transient web result that was not ingested locally.
- Cost and elapsed time are updated throughout execution, not only at the end.

### FR-6: Persist Recursive Runs

Every material operation creates or updates a file-backed run record. A run
must record:

- Run ID, kind, status, timestamps, and stopping reason.
- Target and control commits.
- Parent run and parent candidate when applicable.
- Research snapshot commit.
- Inputs, outputs, models, prompts, tool calls, costs, and wall time.
- Candidate branches, patches, evaluations, decisions, and reflections.

Runs use stable IDs in a flat directory. Recursive structure is expressed by
parent references and rendered in `runs/index.md`, avoiding unbounded path
nesting.

Acceptance criteria:

- The SQLite cache can be deleted and rebuilt without losing canonical state.
- Failed and rejected candidates remain queryable.
- A child run can cite the exact research and candidate state it inherited.

### FR-7: Promote Skills

`.agent/skills` is the canonical target-repository location for executable
agent behavior. Skills may include instructions, BAML definitions or generated
client usage, scripts, configuration, and tests. Volatile provider facts,
comparisons, and research reports must remain in the control plane.

Promoting a skill change must record which OKF concepts, runs, and evaluations
justify the change. Skills are distributed through `npx skills`.

### FR-8: Enforce Policy And Budgets

Policy must cover:

- Allowed, denied, and approval-required target paths.
- Maximum API cost per research and improvement run.
- Maximum wall time per run or candidate.
- Maximum candidate and research concurrency.
- Required evaluation commands before promotion.
- Human approval for promotion, policy relaxation, CI, infrastructure,
  security-sensitive changes, and deployment.

Budget termination must preserve work in progress. Budget increases and policy
relaxation must be explicit recorded decisions.

### FR-9: Conform To OKF v0.2

The complete upstream OKF v0.2 specification must be vendored under
`docs/specifications/` with its source URL, upstream commit, retrieval date,
checksum, and license. The vendored snapshot is the offline implementation
reference.

The `research/okf/` directory must be independently validatable. Every concept
except reserved `index.md` and `log.md` must be UTF-8 Markdown with YAML
frontmatter and a non-empty `type`. Consumers must preserve unknown fields.

### FR-10: Use BAML For Agentic Behavior

BAML definitions are canonical for prompts, structured model functions, and
agent output schemas. Generated Python and TypeScript clients are build
artifacts and are not edited manually. CI must fail when generated clients do
not match checked-in BAML definitions or when structured fixtures no longer
validate.

### FR-11: Distribute The Product

- Publish the primary CLI through npm and expose the `climbhill` executable.
- Make skills installable through `npx skills`.
- Implement frontend code in `www/` with `remix@3.0.0-beta.10` pinned exactly.
- Statically build and deploy `www/` to GitHub Pages at `climbhill.ai`.
- Preserve platform-independent local operation on supported Node runtimes.

## 11. Non-Functional Requirements

### Reproducibility

- Hash raw content and resolved derivation configuration.
- Record exact models, prompts, schema versions, tool versions, and commits.
- Avoid floating package or model aliases in persisted run metadata.

### Safety

- Never commit secrets or environment files.
- Use read-only source credentials wherever practical.
- Avoid automatic merge or deployment.
- Treat fetched content as untrusted input.
- Validate paths before writing outside a job's control directory.

### Recoverability

- Use atomic writes for canonical YAML and Markdown records.
- Preserve completed steps after failures and budget termination.
- Make interrupted operations resumable from their run record.
- Do not require SQLite recovery to inspect or resume a job.

### Portability

- Never persist an absolute control worktree path as job identity.
- Keep OKF concepts human-readable and Git-diffable.
- Generate both TypeScript and Python BAML clients where needed.

### Testability

- Interfaces accept filesystem, Git, clock, model, and source adapters rather
  than creating them internally.
- Tests exercise the same interfaces used by the CLI.
- Network and model calls have deterministic fakes.
- Split-control and Ouroboros flows have end-to-end fixtures.

## 12. Success Metrics

The initial release is successful when:

1. A new user can install the CLI from npm and initialize a job in under five
   minutes.
2. `init` succeeds in both split-control and Ouroboros modes without changing
   the active target branch.
3. Adding the same source twice produces no duplicate evidence.
4. Deriving the same source with the same profile produces no Git diff.
5. Every generated claim can resolve to a resource and evidence locator when
   the source format supports one.
6. A stopped research run preserves enough state to resume without repeating
   completed acquisitions.
7. The graph builder exposes unresolved identity and evidence conflicts.
8. The cache can be rebuilt entirely from version-controlled files.
9. ClimbHill can run the `sota-deep-research-agent` job against its own
   repository in Ouroboros mode.

## 13. Current State

The repository is a Python `0.1.0` alpha with a working but transitional CLI,
SQLite registry, policy checks, MCP tools, provider adapters, deep-research
skills, benchmark tooling, report-oriented OKF output, tests, and GitHub Pages
workflow.

Current strengths:

- Provider adapters and provider metadata already exist in `climbhill/`.
- Deep-research skill scripts and tests exist under `.agents/skills` and
  mirrored `skills/` directories.
- The registry already models runs, candidates, evaluations, costs, lineage,
  decisions, reports, and issue proposals.
- Policy templates already define cost, time, and candidate-count budgets.
- OKF utilities already preserve provider reports, findings, uncertainties,
  methods, raw paths, and metadata.
- The test suite covers CLI, registry-related flows, MCP tools, providers,
  auditing, source validation, and skill discovery.

Observed baseline on 2026-08-18: 202 tests passed and one audit test failed
because the provider source index exceeded its 30-day freshness limit. Package
building and metadata validation succeeded.

## 14. Gap Analysis

| Area | Current implementation | Target implementation | Gap and disposition | Priority |
| --- | --- | --- | --- | --- |
| Primary runtime | Python package `climbhill-ai` with argparse CLI | npm package exposing `climbhill` | Build TypeScript CLI; use Python modules as behavioral reference until parity | P0 |
| Init interface | `init --repo --registry --force` writes alignment files and SQLite into target | `init --target --control --location --job` creates job ID, control branch, worktree, and portable pointer | Replace interface and persistence behavior; retain conservative no-overwrite rules | P0 |
| Control persistence | Target-local `.climbhill/registry.local.sqlite` is operational source | Versioned `.climbhill/<job-id>/` filesystem in selected control repo | Build file-backed job store and make SQLite a rebuildable ignored cache | P0 |
| Ouroboros mode | No target/control distinction or worktree orchestration | Same Git repo, separate `climbhill/<job-id>` branch and worktree | Build Git repository identity checks, branch creation, and worktree management | P0 |
| Recursive history | SQLite rows for runs, candidates, lineage, costs, and decisions | Canonical `runs/<run-id>/` files with parent references and generated index | Design schemas, migration/export, atomic writer, and cache indexer | P0 |
| `add` | `resources add` writes a manually described Markdown resource | Top-level one-source retrieval with adapters, raw storage, hashing, OKF resource, and default derivation | Build common source interface; adapt reusable provider/custom-data scripts | P0 |
| Source adapters | Provider and custom-data scripts exist, but no unified ingestion contract | Local, PDF, web, YouTube, and arXiv adapters producing raw resource records | Extract a shared interface and add deterministic adapter fixtures | P0 |
| `derive` | Report normalizer heuristically extracts finding-like lines | BAML Bloom-based typed source-local observations with exact locators | Replace heuristic extraction for workspace derivation; retain normalizer for legacy imports | P0 |
| Derivation idempotency | No content-plus-profile derivation identity | Hash raw content, prompt, model, schema, profile, and chunking | Build derivation manifest, cache lookup, and no-diff tests | P0 |
| BAML | No BAML files or generated clients | BAML is source of truth; generated Python and TypeScript clients | Add `baml_src`, generator config, fixtures, CI drift check, and runtime adapters | P0 |
| Knowledge graph | No ontology, entity resolution, canonical graph, or conflict model | Explicit idempotent `graph build` and inspectable reconciliation | New module and schemas; reuse OKF links and provenance conventions | P1 |
| `research` | Legacy Claude run, provider fan-out, benchmarks, and MCP deep-research calls | Bounded BAML loop over local corpus with optional discovery and persistent partial state | Compose existing providers behind new research interface; add planner, budgets, and resume | P1 |
| Budget enforcement | Policy stores USD/time/candidate values; costs can be recorded manually | Continuous API-cost and wall-time enforcement with graceful partial completion | Add runtime budget meter and stopping contract | P1 |
| OKF | v0.2 is referenced; output is provider-report-oriented; upstream spec not vendored | Independently valid research bundle with resource, observation, entity, claim, and relationship concepts | Vendor spec, define producer types, expand validator, migrate legacy bundles | P0 |
| Skills location | New recursive skills in `.agent/skills`; deep-research skills duplicated under `.agents/skills` and `skills/` | `.agent/skills` is canonical executable behavior, distributed through `npx skills` | Migrate/package skills, remove mirror drift, keep research facts in control plane | P1 |
| Candidate workflow | CLI can create planned candidates and manually record evaluations and decisions | File-backed recursive execution integrated with research snapshots and provenance | Adapt current concepts; replace SQLite-only writes and add execution adapters | P1 |
| MCP | Python MCP servers expose ClimbHill and deep-research tools | Generated/runtime interfaces share job, research, graph, and run modules | Retain as adapter; update after core interfaces stabilize | P2 |
| Website | Root `index.html`, assets, and copy-based Pages workflow | `www/` Remix `3.0.0-beta.10` app with static Pages output | Build Remix app, migrate content/assets/domain files, update Pages workflow | P2 |
| Distribution | PyPI publish workflow and plugin folders | npm CLI, `npx skills`, static website | Add npm release pipeline; retire PyPI only after parity decision | P1 |
| CI | Python matrix, package build, plugin validation, CLI/MCP smoke | Node/TypeScript, BAML generation, Python generated client, OKF, Git/LFS fallback, Remix build, and integration matrices | Expand CI incrementally; repair current stale-source failure first | P0 |
| Documentation | README and design note describe target; architecture docs retain older assumptions | PRD, architecture, schemas, CLI reference, migration, and operator docs agree | Make PRD authoritative and update dependent docs alongside implementation | P1 |

## 15. Reuse, Migration, And Replacement Plan

### Reuse

- Provider specifications and adapters.
- Deep-research skill scripts and their tests where their behavior fits the new
  source or research interfaces.
- Policy concepts and conservative defaults.
- Run, candidate, evaluation, cost, lineage, decision, and report terminology.
- OKF frontmatter helpers and legacy bundle import logic.
- Source URL and manifest hardening tests.

### Migrate

- SQLite canonical records into version-controlled run files.
- Deep-research operational skills into canonical `.agent/skills` packages.
- Research facts embedded in skills into job research concepts.
- Root static site content and assets into `www/`.
- Python CLI behavioral tests into language-neutral interface fixtures and
  TypeScript CLI tests.

### Replace

- Target-local registry as canonical state.
- `init --repo` as the primary initialization interface.
- Report-line heuristics as the main derivation mechanism.
- Root-level copy-based Pages deployment.
- PyPI as the primary CLI distribution channel.

### Preserve During Transition

- Existing Python commands until npm equivalents reach tested parity.
- Legacy provider benchmark commands for comparison and regression testing.
- Existing OKF report bundles as importable historical evidence.
- PyPI and MCP workflows until an explicit compatibility decision is made.

## 16. Delivery Plan

### Phase 0: Contract And Baseline

- Vendor OKF v0.2 with provenance and license metadata.
- Define job, run, resource, observation, and graph schemas.
- Freeze CLI help text and exit-code conventions.
- Repair the stale provider-source audit.
- Add architecture decisions for control branches, worktrees, and cache status.

### Phase 1: npm CLI And Job Persistence

- Create npm package and TypeScript CLI skeleton.
- Implement `init` in split-control and Ouroboros modes.
- Implement file-backed job/run store and SQLite rebuild.
- Implement Git LFS detection and fallback note.
- Add end-to-end Git worktree tests.

### Phase 2: Ingestion And Derivation

- Define source adapter interface.
- Implement local, PDF, webpage, YouTube, and arXiv adapters.
- Add BAML project and default Bloom derivation profile.
- Generate TypeScript and Python clients.
- Implement idempotent `add` and `derive`.

### Phase 3: Graph

- Define ontology, identity-resolution, conflict, and provenance concepts.
- Implement idempotent `graph build` and `graph inspect`.
- Add reconciliation fixtures for aliases, ambiguous identities, supporting
  claims, and contradictions.

### Phase 4: Research And Recursive Improvement

- Implement bounded BAML research loop and local-only mode.
- Integrate source discovery with `add` and `derive`.
- Enforce live cost and wall-time budgets.
- Persist partial and resumable runs.
- Migrate candidate evaluation and reflection to the file-backed run model.

### Phase 5: Distribution And Dogfooding

- Publish the CLI through npm.
- Package canonical skills for `npx skills`.
- Build and deploy the Remix `www/` site.
- Run `sota-deep-research-agent` against ClimbHill in Ouroboros mode.
- Use the resulting research and evaluations to improve ClimbHill's own BAML
  research functions and skills.

## 17. Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Control branch and candidate branch operations interfere | Use separate worktrees, distinct branch namespaces, and integration tests against temporary repositories. |
| Generated knowledge loses evidence context | Require resource IDs and locators in BAML output; reject invalid observations before writing. |
| Entity resolution over-merges concepts | Preserve observations, confidence, rationale, and unresolved alternatives; never delete source-local evidence. |
| Paid research exceeds expectations | Enforce live cost and wall-time budgets and persist partial results. |
| Raw evidence makes Git repositories too large | Use Git LFS by default and documented ignore fallback. |
| BAML-generated clients drift | Pin generator versions and fail CI on generated diffs. |
| npm rewrite regresses working Python behavior | Keep language-neutral fixtures and retain Python implementation until tested parity. |
| OKF upstream changes | Vendor a pinned specification and make upgrades explicit migrations. |
| Self-improvement corrupts its own control state | Keep control and implementation worktrees separate; require policy and human promotion gates. |

## 18. Remaining Product Decisions

These decisions are not blockers for writing schemas and the Phase 1 skeleton,
but must be resolved before their affected phase ships:

- Exact npm package name and supported Node versions.
- Default model/provider resolution and credential configuration.
- Source adapter plugin manifest and third-party installation mechanism.
- Default API-cost and wall-time budget values.
- Run resume and cancellation commands.
- Control-branch retention, publication, and merge policy.
- Whether generated BAML clients are committed or generated only in package and
  CI builds.
- Minimum Git LFS version and large-file threshold.
- Exact ontology reconciliation model and user correction workflow.

## 19. MVP Release Criteria

The target MVP is complete when all of the following are true:

- The CLI installs from npm and exposes documented commands.
- `init` passes split-control and Ouroboros end-to-end tests.
- One source of each MVP type can be added and represented as an OKF resource.
- Default BAML derivation generates valid, cited, source-local observations.
- Identical derivations and graph builds are idempotent.
- The graph builder preserves deduplication rationale and conflicts.
- Research supports external discovery, local-only operation, live budgets, and
  resumable partial output.
- Recursive run history is inspectable without SQLite.
- Skills install through `npx skills` and live under `.agent/skills` in target
  repositories.
- The pinned Remix site builds from `www/` and deploys to `climbhill.ai`.
- ClimbHill successfully completes a bounded Ouroboros run against itself.
