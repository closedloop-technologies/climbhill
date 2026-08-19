# ClimbHill.ai

> Controlled, measurable, recursive self-improvement loops for Git repositories and coding agents.

ClimbHill.ai helps a user create an agentic workflow that performs a job at a new quality and efficiency bar. It combines a version-controlled job workspace, evidence-first research, reusable skills and tools, policy gates, experiment history, evaluations, and human-visible promotion decisions.

The project is the renamed and narrowed successor to `awesome-llm-evolve` and this repository's earlier deep-research catalog work. It is now a local-first substrate for agentic codebase improvement.

## Goal

ClimbHill.ai helps coding agents run controlled, measurable, recursive self-improvement loops on a Git repository while preserving human control, repository safety, historical memory, and clear promotion paths.

The central thesis is simple: a codebase should learn from every attempted improvement, not only the patches that merge. Failed candidates still produce useful evidence about constraints, brittle tests, weak docs, bad hypotheses, missing policy, and repo areas that are difficult for agents to improve.

## Design Reference

The target implementation and current-to-target gap analysis are defined in [PRD.md](PRD.md).

ClimbHill.ai is aligned with Lilian Weng's ["Harness Engineering for Self-Improvement"](https://lilianweng.github.io/posts/2026-07-04-harness/) from July 4, 2026. The post frames a harness as the deployment system around a base model: workflow, tool use, context, persistent artifacts, permissions, and evaluation.

Key takeaways reflected in this repo:

- The harness is an optimization target, not just a prompt template.
- Long-horizon agent work needs durable file and database state instead of relying on transient chat context.
- Parallel candidate attempts should be explicit, inspectable, and recoverable through logs, patches, and status records.
- Context should be curated into structured memory over time, not appended endlessly.
- Self-improvement should use propose, evaluate, accept, and reject loops with regression checks and preserved failure records.
- Harness edits should remain bounded by policy, editable surfaces, passing behavior that must be preserved, and human-visible promotion gates.

## Boundary

ClimbHill.ai begins when a user identifies a job to be done in a Git repository. It gathers and structures relevant knowledge, creates a bounded agentic improvement loop, preserves each attempt, and ends when candidate improvements are evaluated, recorded, and promoted into a pull request, issue, plan, or follow-up loop.

ClimbHill.ai is:

- An npm CLI for versioned research and recursive repository-improvement workflows.
- A file-backed control plane on dedicated Git branches and worktrees.
- A Codex plugin and `npx skills` bundle for distributing repo-improvement procedures.
- A BAML-defined agent runtime with generated TypeScript and Python clients.
- A skill bundle under `.agent/skills` for recursive improvement workflows.
- An OKF v0.2 evidence workspace for sources, observations, graphs, and reports.
- A policy system for allowed, denied, and approval-required edits.
- A candidate-evolution system for parallel attempts, historical sampling, recombination, comparison, and promotion.
- A compatibility MCP and Python surface for the earlier workflow during migration.

ClimbHill.ai is not a hosted agent cloud, a model-training framework, an automatic merge system, or a tool that silently modifies tests to make candidates pass.

## Core Loop

```text
Repository + Job To Be Done
  -> Initialize Versioned Job Workspace
  -> Add Sources
  -> Derive Source-Local Knowledge
  -> Build Deduplicated Knowledge Graph
  -> Run Bounded Research
  -> Goal + Policy + Resources + Skills
  -> Candidate Run
  -> Candidate Attempts
  -> Policy Checks
  -> Tests and Evaluations
  -> Candidate Comparison
  -> Human Decision
  -> Promotion or Rejection
  -> Experiment Registry Update
  -> Meta-Analysis
  -> Issues, Resources, or Next Run
```

The loop is designed around repo safety, durable memory, evaluation before promotion, human control, readable skills, and a small local MVP that can expand later.

## Components

| Component | Purpose |
|-----------|---------|
| Landing page | Remix application under `www/`, statically built and deployed to GitHub Pages at `https://climbhill.ai/`. |
| Codex plugin | Packages workflows, MCP configuration, skills, policy templates, and install docs. |
| Compatibility MCP | Preserves the earlier Python agent-facing interface; canonical job state lives in files. |
| CLI | npm-distributed local CLI for job setup, source ingestion, derivation, graph construction, research, candidate runs, and reporting. |
| Skills | Agent-readable procedures for alignment, historical sampling, candidate evolution, protected editing, reporting, and promotion. |
| Resources | Versioned context with provenance, trust level, tags, summary, and reason for inclusion. |
| Experiment registry | Version-controlled run files for goals, candidates, evaluations, costs, decisions, reports, and lineage; SQLite is a rebuildable query cache. |
| Policy layer | Conservative defaults for allowed edits, denied edits, approval-required paths, budgets, commands, and promotion gates. |
| Research workspace | Immutable raw evidence plus a version-controlled OKF bundle of resources, claims, entities, relationships, topics, and reports. |

## Implementation Stack

Agentic workflows, structured model functions, prompts, and output schemas are defined in [BAML](https://github.com/BoundaryML/baml) from BoundaryML. BAML definitions are the source of truth for agent behavior. Its compiler generates the type-safe Python and TypeScript clients and types needed by the CLI, skills, MCP tools, and supporting workflows; generated clients are build artifacts and should not be edited by hand.

All frontend code uses [Remix](https://github.com/remix-run/remix), pinned to `remix@3.0.0-beta.10`. This includes the `www/` homepage and any future local or hosted interfaces. The exact beta version is pinned in package manifests rather than consumed through a moving prerelease tag.

## Repo Alignment

A repository is ClimbHill-aligned when it has enough structure for agents to improve it safely:

- `goal.md` describing the repo goal.
- `AGENTS.md` describing agent operating instructions.
- `README.md` describing setup and usage.
- `docs/architecture.md` or `ARCHITECTURE.md` describing design boundaries.
- `TESTING.md` describing test commands and expectations.
- `EVALS.md` describing evaluation strategy.
- `.climbhill/policy.yaml` defining edit and promotion policy.
- `.climbhill/eval.yaml` defining evaluation commands and rubrics.
- `.agent/skills/` for repo-local skills.
- `resources/` for research, context, and promoted learnings.
- Known install, lint, typecheck, test, and build commands when applicable.

ClimbHill should inspect a target repo, identify missing alignment pieces, and propose or create them without overwriting existing files unless a human approves.

## CLI Design

The ClimbHill CLI is organized around one job to be done targeting one Git repository. `climbhill init` creates a globally unique job ID from a human-readable slug plus a UUID-style suffix. The target repository is the code being improved; the control repository owns the accumulated research and recursive run history.

```text
<control-repository>/
└── .climbhill/
    └── <job-slug>-<uuid-suffix>/
        ├── job.yaml
        ├── research/
        │   ├── raw/              # immutable retrieved evidence
        │   └── okf/              # conformant OKF knowledge bundle
        │       ├── resources/
        │       ├── observations/
        │       ├── entities/
        │       ├── claims/
        │       ├── relationships/
        │       ├── topics/
        │       ├── reports/
        │       ├── index.md
        │       ├── log.md
        │       └── method.md
        ├── runs/                 # recursive plans, candidates, evaluations, decisions
        └── cache/
            └── registry.sqlite  # rebuildable local query cache
```

The control repository is version-controlled at its root. ClimbHill configures each job's `research/raw/**` for Git LFS when Git LFS is available. Otherwise it adds the raw directory to `.gitignore` and writes instructions for enabling Git LFS later. Derived OKF knowledge and run records remain version-controlled either way; SQLite is a rebuildable ignored cache.

Target and control support two persistence modes:

| Mode | Target | Control | Behavior |
| --- | --- | --- | --- |
| Split control | Different repositories | Dedicated control repository | Research and runs are versioned independently from the target code. |
| Ouroboros | Same repository | Target repository | ClimbHill stores its own control plane in the repository it is improving. |

In Ouroboros mode ClimbHill creates a long-lived `climbhill/<job-id>` branch in the shared repository and checks it out as a separate worktree under `--location`. This keeps control-plane commits isolated from the target's active implementation branch while storing both histories in the same Git repository.

### Primary Workflow

```text
climbhill init -> climbhill add -> climbhill derive -> climbhill graph build -> climbhill research
```

Initialize a job workspace for a repository:

```bash
climbhill init \
  --target /path/to/repo \
  --control /path/to/control-repo \
  --location "$HOME/.climbhill" \
  --job improve-release-reliability
```

Run ClimbHill against its own repository:

```bash
climbhill init \
  --target /path/to/climbhill \
  --control /path/to/climbhill \
  --location "$HOME/.climbhill" \
  --job sota-deep-research-agent
```

Retrieve one document and run its default enrichment:

```bash
climbhill add https://www.youtube.com/watch?v=VIDEO_ID
climbhill add https://arxiv.org/abs/2401.01234
climbhill add ./architecture-review.pdf
climbhill add https://example.com/article

# Preserve the source without deriving knowledge yet
climbhill add ./large-corpus.pdf --no-derive
```

`add` detects local files, PDFs, webpages, YouTube videos, and arXiv papers. Retrievers only acquire evidence and metadata: for example, YouTube stores the transcript and video metadata, while arXiv stores the original versioned PDF. Interpretation happens through the generic derivation workflow.

Derive source-local entities, claims, opinions, procedures, relationships, terminology, practices, and research gaps using the default Bloom-based profile:

```bash
climbhill derive
climbhill derive --resource RESOURCE_ID
climbhill derive --append-prompt "Prioritize deployment constraints."
climbhill derive --prompt-file ./custom-derivation-prompt.md
```

Derivation is idempotent for the same raw content and resolved profile. A changed prompt, model, or schema creates a distinct derivation without mutating the evidence or replacing earlier output.

Build the canonical knowledge graph explicitly:

```bash
climbhill graph build
climbhill graph inspect
```

Graph construction detects an ontology, resolves duplicate entities, normalizes relationships, and records ambiguity or conflicting claims while preserving every source and locator.

Run a bounded research loop:

```bash
climbhill research "What best practices would improve this repository's release reliability?"
climbhill research "What does the current corpus say?" --local-only
climbhill research --resume RESEARCH_RUN_ID --max-api-cost 2
```

Research inspects existing knowledge, identifies gaps, discovers new evidence when allowed, ingests it through `add`, derives source-local knowledge, and produces a cited answer. It persists its question, plan, searches, sources, derivations, answer, API cost, wall time, partial work, and stopping reason. API-cost and wall-time budgets stop cleanly without discarding progress. Graph reconciliation remains an explicit command.

### Improvement Loop

The existing candidate workflow remains the interface for comparing changes to the target repository:

```bash
# Classify target paths against the active job policy
climbhill policy check src/app.ts tests/app.test.ts .env

# Create a run, evaluate candidates, compare them, and record a human decision
climbhill run --goal "Improve setup docs" --candidates 2
climbhill evaluate --run RUN_ID --candidate CANDIDATE_ID --command "npm test"
climbhill compare --run RUN_ID
climbhill candidate attach-patch --run RUN_ID --candidate CANDIDATE_ID --patch ./candidate.patch
climbhill decision --run RUN_ID --candidate CANDIDATE_ID --decision promote --rationale "Best passing candidate" --approve
climbhill reflect --run RUN_ID --text "Record what the next run should preserve."
```

The npm CLI is the primary implementation. Install it with `npm install -g climbhill` or run it from a checkout with `npm install && npm run build`. The Python CLI remains available during the compatibility transition.

## MCP Servers

The primary MCP server is ClimbHill-focused:

```bash
pip install "climbhill-ai[mcp]"
climbhill-mcp
```

It exposes tools for repo inspection, alignment, policy checks, resource search, run creation, candidate registration, evaluation recording, comparison, history sampling, report generation, decisions, costs, lineage, and issue proposals.

The upstream deep-research provider fan-out MCP implementation is preserved in `climbhill.deep_research_mcp_server` for compatibility with the earlier repository direction.

## Distribution

ClimbHill has three distribution surfaces:

- **CLI:** published through npm and installed or executed with the standard npm toolchain.
- **Skills:** installable through `npx skills` so users can add the ClimbHill workflows independently of the CLI.
- **Website:** a Remix `3.0.0-beta.10` application under `www/`; its static build output is deployed through GitHub Pages at `https://climbhill.ai/`.

The website source layout is:

```text
www/
├── app/
│   └── home.tsx
├── build-static.tsx
├── package.json
└── tsconfig.json
```

The npm package will expose the `climbhill` executable:

```bash
npm install --global climbhill
climbhill --help
```

Skills will be discoverable and downloadable through:

```bash
npx skills
```

The release workflows publish the npm CLI with provenance, retain the Python compatibility package on PyPI, and deploy the statically rendered Remix output with the `climbhill.ai` CNAME.

## Legacy Deep-Research Assets

The upstream merge preserved the earlier deep-research skills, benchmark helpers, provider docs, audit tools, and OKF normalization assets under `.agents/skills/`, `skills/`, `benchmark/`, `docs/`, and `climbhill/`. They remain useful as research resources and compatibility tooling, but ClimbHill.ai is now the product direction.

Pricing and model availability change frequently. Use `skills/provider-source-index.md` and `python -m climbhill.source_refresh --check-links` before refreshing pricing or model guidance. The old provider tables used an "Under-$1 Benchmark Stance" column to keep live smoke tests bounded; keep that cost-control discipline when reusing those assets.

Run the offline repository and environment checks before spending API credits:

```bash
python -m climbhill.audit
python -m climbhill.op_env --template
python -m climbhill.source_refresh
```

## Status

The MVP implementation includes the npm CLI, split-control and Ouroboros persistence, five source adapters, BAML derivation and bounded research, explicit graph construction, recursive run records, policy gates, a rebuildable SQLite cache, validated OKF v0.2 bundles, installable skills, npm/PyPI release workflows, and the Remix-based `www/` site. The Python CLI and MCP remain compatibility surfaces; new durable job state is owned by the version-controlled filesystem model.
