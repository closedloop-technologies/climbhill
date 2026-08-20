# ClimbHill.ai

> Evidence-guided experiment selection under scoped authority.

ClimbHill is a local-first controlled optimizer for Git repositories. It helps a
human and coding agents determine what to improve next, gather evidence when the
answer is unclear, and change only the surfaces they are authorized to change.

## Core Model

The recursive engine has four concepts:

```text
Run -> Attempt -> Evaluation -> Decision
```

A Run is:

```text
immutable baseline + mutable focus + evaluation strategy + promotion target
```

Git owns content versioning. ClimbHill records Focus, evidence, policy,
authorization, semantic lineage, and promotion. Recursion emerges when an
authorized Decision creates a child Run; there is no separate Campaign or
recursive-revision graph.

Jobs are optional UX projections for grouping Runs and supplying defaults. A Run
is executable and auditable without loading a Job.

The complete contract is [docs/recursive-loops.md](docs/recursive-loops.md), the
target product requirements are [PRD.md](PRD.md), and canonical language is in
[CONTEXT-MAP.md](CONTEXT-MAP.md).

## Three Focuses

| Focus | What changes | What evaluates it |
| --- | --- | --- |
| Task | The artifact performing the user's job | Tests, benchmarks, rubrics, and human preference |
| Learning | The skill, tool, environment, context, or workflow producing Attempts | Frozen tasks and holdouts |
| Alignment | Evaluation definitions or judge configuration | Human judgments and held-out calibration evidence |

Every optimization has an evaluation surface outside the thing being optimized.
Failure against an evaluator is not evidence that the evaluator is wrong.

## Recursive Controller

The controller separates agentic analysis from deterministic authority:

```text
frozen evidence
  -> Continuation Analysis
  -> deterministic authorization and eligibility
  -> atomic consumption
  -> execution
```

Continuation Analysis may recommend exactly one of:

```text
attempt | evaluate | promote | spawn_run | stop
```

It cannot grant itself authority or execute the recommendation. Autonomy may
continue inside a bounded Authorization Envelope; changing the envelope requires
a Decision. Promotion remains human-approved in the MVP.

## Primary CLI

The intended human interface is small:

```bash
climbhill assess
climbhill run "Make this project easier for an agent to contribute to"
climbhill status
climbhill decide --promote <attempt-id>
```

Jobs are optional conveniences:

```bash
climbhill job create contributor-experience
climbhill run --job contributor-experience
climbhill job status contributor-experience
```

Advanced Focus selection remains available:

```bash
climbhill run --focus task "Improve release reliability"
climbhill run --focus learning:environment --from <run-id>
climbhill run --focus alignment --from <run-id>
```

Low-level Attempt, Evaluation, Decision, policy, and history operations are
agent-facing plumbing. Users should not need to manually operate the Run tree.

## Assessment And Execution

ClimbHill does not assume every repository is ready for recursive optimization.
`climbhill assess` combines deterministic probes with lightweight agentic skills
and reports individual capabilities, including install/build/test behavior,
external services, shared state, evaluator readiness, and isolation support.

Execution adapters include:

- worktree;
- isolated clone;
- container;
- sequential in-place execution with recovery;
- manual execution.

Worktrees are one option, not a prerequisite. A Run pins the assessment evidence
and selected adapter it relied upon.

## Edit Control

Repositories may define Gitignore-style write protection:

```text
.climbhillignore
.climbhillignore.task
.climbhillignore.learning
.climbhillignore.alignment
```

Global denies are monotonic. Loop-specific files may only add restrictions.
Intended paths are checked before execution and the actual Git diff is checked
afterward. The post-execution result is authoritative.

Read restrictions and hidden holdout access are separate from write protection.
Attempts and Continuation Policies never receive raw hidden holdouts.

## Research

ClimbHill also maintains a versioned research layer. The intended research flow
is:

```bash
climbhill add <url-or-file>
climbhill derive
climbhill graph build
climbhill research "What evidence would improve this repository?"
```

Research preserves immutable raw evidence and derives traceable Open Knowledge
Format concepts. A Run pins the exact Control commit and research paths it uses.
Research Execution is a separate context and does not overload recursive `Run`.

Existing deep-research provider skills, benchmark helpers, audit tools, and OKF
normalization code remain useful inputs to this research layer.

## Repository Roles

- **Target Repository:** product or executable behavior being improved.
- **Control Repository:** research, policies, evaluations, assessments, and Run
  history.

They may be different repositories or the same repository in Ouroboros mode.
Ordinary Git commits and branches represent both. Local worktree, clone, and
container locations are execution details rather than portable identity.

Canonical Control state is organized independently of Jobs:

```text
.climbhill/
├── jobs/
├── runs/
├── assessments/
├── evaluations/
├── policies/
├── research/
└── cache/registry.sqlite
```

YAML and Markdown are canonical. SQLite is ignored and rebuildable.

## Components

| Module | Purpose |
| --- | --- |
| CLI | Human interface over assessment, recursive orchestration, research, and Decisions |
| Recursive engine | Run creation, Attempts, Evaluations, Continuation Analysis, authority, eligibility, and promotion |
| Execution adapters | Worktree, clone, container, sequential, and manual isolation strategies |
| Research layer | Source ingestion, derivation, graph construction, and OKF persistence |
| Skills | Agent-readable assessment, execution, evaluation, and improvement procedures |
| MCP server | Agent-facing adapter over the same core interfaces |
| File-backed store | Canonical Run and research state with a rebuildable SQLite index |

Agentic prompts and structured outputs are defined in BAML. Generated TypeScript
and Python clients are build artifacts. The primary CLI target is distributed
through npm, skills through `npx skills`, and the website is implemented with
`remix@3.0.0-beta.10`.

## Current Implementation

The repository contains an npm CLI, file-backed YAML and Markdown state, source
adapters, BAML derivation and research clients, explicit graph construction, an
OKF validator, policy gates, a rebuildable SQLite index, recursive Runs and
Attempts, TypeScript tests, release workflows, and a Remix site. The Python CLI
and MCP server remain a transitional secondary surface.

The merged MVP now uses Attempt terminology throughout its npm and Python
interfaces without compatibility aliases. It still predates parts of the target
contract: initialization is Job-first, isolation is worktree-oriented, research
operations share the Run store, and assessment adapters, Focus resolution,
Authorization Envelopes, typed Continuation Analysis, and atomic recommendation
consumption remain implementation work.

## Local Development

Install and run the current checks:

```bash
node --version # Node 22.5 or newer
npm ci
npm run check
npm test
npm run baml:check
npm run okf:spec
npm run www:build
python -m pip install -e '.[dev]'
pytest
git diff --check
```

Run offline research environment checks before spending provider credits:

```bash
python -m climbhill.audit
python -m climbhill.op_env --template
python -m climbhill.source_refresh
```

### Research Drift Controls

Pricing and model availability change frequently. Refresh the mirrored provider
index at least monthly and verify its links with:

```bash
python -m climbhill.source_refresh --check-links
```

### Under-$1 Benchmark Stance

The default provider benchmark keeps each task below one US dollar. This is a
research-harness constraint, not a Run authorization or root budget.

## Distribution

The npm package exposes:

```bash
npm install --global climbhill
climbhill --help
```

Skills are distributed through:

```bash
npx skills
```

The local workflow spine remains open and account-free. Hosted workers, shared
workspace persistence, authenticated Decisions, expert review, and certification
may provide paid workload or trust value without gating local utility.
