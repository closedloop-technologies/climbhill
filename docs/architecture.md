# Architecture

ClimbHill.ai is a local-first system for controlled research and recursive improvement of Git repositories by coding agents. Durable state is readable, reviewable files on a dedicated Git branch; derived indexes are disposable.

## Runtime Layers

- **npm CLI**: `climbhill` commands initialize jobs, ingest and derive sources, build graphs, run bounded research, manage recursive candidates, enforce policy, and validate OKF bundles.
- **Git control topology**: every job owns either a split control branch or a separate Ouroboros clone/worktree. The target repository stores only a portable pointer; machine-local checkout locations live in Git's common directory.
- **File-backed run store**: YAML, Markdown, JSON, JSONL, patches, and raw artifacts are the system of record under the job root. Atomic writes and append-only event files make interrupted operations recoverable.
- **BAML clients**: checked-in TypeScript and Python clients provide typed derivation, planning, and synthesis calls against an exact OpenAI model snapshot.
- **Source adapters**: local files, PDFs, webpages, YouTube transcripts, and arXiv papers are normalized into content-addressed raw artifacts and versioned source manifests.
- **Evidence graph**: observations are converted into canonical concepts and relationships with resource, observation, and locator provenance. Conflicts remain explicit instead of being silently collapsed.
- **Bounded research**: local evidence is searched first. Optional web search obeys query, page-read, wall-clock, token, and dollar budgets; partial progress can resume without repeating completed searches.
- **Recursive improvement**: flat run IDs record lineage, plans, candidates, patches, evaluations, decisions, reflections, costs, and skill provenance. Promotion remains a human decision.
- **Policy layer**: allowed, denied, and approval-required paths plus evaluation commands and budgets constrain candidate work and policy changes.
- **OKF v0.2**: validated concept bundles preserve source and finding provenance. The upstream specification and license are vendored with hashes and provenance metadata.
- **Skills**: procedures under `.agent/skills` are installable through the `skills` CLI and can be promoted only with run and evaluation evidence.
- **Remix site**: a static Remix 3 beta site documents the product and is deployable through GitHub Pages.

## Git Topology

```text
target checkout
  .climbhill/jobs/<job-id>.yaml       portable repository IDs + control branch

git common directory
  climbhill/locators/<job-id>.yaml    machine-local control checkout location

control branch/worktree
  job.yaml
  policy.yaml
  sources/
  observations/
  graph/
  research/
  runs/
  okf/
  events/
  cache/registry.sqlite               ignored, rebuildable index only
```

Split mode creates a sibling worktree on an orphan control branch. Ouroboros mode creates an isolated sibling clone and worktree. Existing branches are never repurposed, and `climbhill recover` repairs a missing local locator explicitly.

## Evidence Flow

```text
Source URI
  -> immutable raw artifact + versioned source manifest
  -> typed BAML derivation + observations
  -> deterministic graph build
  -> bounded local/web research
  -> cited synthesis + OKF bundle
  -> recursive candidate/evaluation/decision records
```

Every derivation identity includes the raw hash, profile, resolved prompt, model, schema, and chunking configuration. A derivation manifest is committed only after all observation files exist, so interrupted work cannot be mistaken for a cache hit.

## Safety Boundaries

Human approval is required for promotion, changes to approval-required paths, budget increases, and policy relaxation. Merge, deployment, external publication, and credential provisioning stay outside the autonomous runtime. Failed and rejected candidates remain queryable evidence, while rebuildable SQLite cache files never become canonical state.
