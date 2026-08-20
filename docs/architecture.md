# Architecture

ClimbHill is a local-first controlled optimizer over Git repositories. The CLI is
the primary human interface; MCP is an agent-facing adapter over the same core
modules.

## Module Map

- **Run engine**: resolves Baseline, Focus, Evaluation Strategy, Promotion Target,
  budgets, policy, and Authorization Envelope.
- **Attempt engine**: generates and records alternative mutations within one Run
  contract.
- **Evaluation engine**: executes pinned evaluators and separates execution state
  from quality verdict.
- **Continuation controller**: converts frozen typed evidence into a typed
  recommendation.
- **Deterministic control**: resolves Focus paths, authorization, eligibility,
  budgets, state transitions, freshness, and atomic consumption.
- **Execution adapters**: worktree, isolated clone, container, sequential
  in-place, and manual operation.
- **Assessment module**: deterministic probes plus lightweight agentic skills that
  produce capability findings.
- **File-backed store**: canonical YAML, Markdown, JSONL, and artifacts with a
  rebuildable SQLite index.
- **Research module**: source ingestion, derivation, graph construction, and OKF
  evidence persistence.
- **CLI**: deep human interface over orchestration.
- **MCP server**: agent-readable adapter over core module interfaces.

## Recursive Flow

```text
Objective
  -> Resolve standalone Run contract
  -> Generate Attempts within the authorization envelope
  -> Evaluate with the pinned external strategy
  -> Freeze an Evidence Snapshot
  -> Produce Continuation Analysis
  -> Check authorization and execution eligibility
  -> Add Attempt, gather evidence, recommend promotion, spawn child Run, or stop
  -> Record human Decision before promotion
```

Task, learning, and alignment are different Focuses over this same flow. A child
Run is created only when useful work requires a different Focus or authorization
envelope.

## Core Interfaces

The external interfaces remain small:

```text
Assessment.assess(repositories, machine) -> AssessmentRecord
RunEngine.create(RunRequest) -> Run
RunEngine.status(run_id) -> RunStatusView
ContinuationPolicy.evaluate(ContinuationInput) -> ContinuationAnalysis
DecisionEngine.record(DecisionRequest) -> Decision
```

Internal adapters satisfy interfaces for Git, filesystem, clocks, models,
evidence readers, evaluators, policy, authorization, budget accounting, and
execution environments. Tests cross the same seams as the CLI.

## Trust And Authority

The agentic Continuation Policy receives typed evidence from controlled readers.
It does not receive raw hidden holdouts, secrets, or unrestricted repository
access. It recommends but cannot authorize or execute.

Deterministic control computes:

```text
recommendation
  -> authorization
  -> execution eligibility
  -> atomic consumption
  -> adapter execution
```

Authority and eligibility are distinct. An authorized action may be ineligible
because of stale evidence, exhausted budget, invalid Focus, or failed preflight.

## Persistence

Canonical state lives under `.climbhill/runs`, independently of optional Jobs.
Git commits provide content identity and ancestry. Semantic Attempt relationships
remain metadata. SQLite is an ignored, rebuildable query cache.

The detailed schema and invariants are defined in
[recursive-loops.md](recursive-loops.md).

## Implemented Substrate

The npm MVP already provides file-backed YAML/Markdown records, atomic writes,
source adapters, BAML clients, research workflows, graph construction, policy
checks, OKF validation, a rebuildable SQLite index, and the Remix site. Its
recursive implementation persists Attempts, Evaluations, and Decisions under a
Run directory.

Some modules still reflect the implementation that preceded this contract:
`init` creates a Job-owned control checkout, worktree isolation is assumed, and
research operations use the Run store. Those are migration constraints, not
architectural invariants. New recursive-engine work targets the interfaces and
repository layout above.
