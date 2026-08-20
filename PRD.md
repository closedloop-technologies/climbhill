# ClimbHill Product Requirements Document

Status: Draft target implementation
Last updated: 2026-08-19
Primary interface: `climbhill` CLI
Distribution: npm, `npx skills`, and `climbhill.ai`

## 1. Executive Summary

ClimbHill is a local-first controlled optimizer for Git repositories. A user
states an outcome; ClimbHill gathers evidence, generates alternative Attempts,
evaluates them, and determines what to improve next while changing only surfaces
for which it has authority.

The recursive engine is centered on:

```text
Run -> Attempt -> Evaluation -> Decision
```

A Run freezes the Target and Control commits, declares one writable Focus, pins
an external Evaluation Strategy, and identifies a Promotion Target. Task,
learning, and alignment work use the same engine with different Focuses.
Recursion emerges when an authorized Decision creates a child Run.

Jobs are optional UX projections that group Runs and supply defaults. They are
not required engine state. Git owns content versioning; ClimbHill does not create
a second revision system.

The canonical recursive contract is [docs/recursive-loops.md](docs/recursive-loops.md).
Canonical terminology is mapped in [CONTEXT-MAP.md](CONTEXT-MAP.md). The rationale
for the Run-centered model is recorded in
[ADR 0001](docs/adr/0001-run-centered-recursive-optimization.md).

## 2. Product Definition

Recursive self-improvement is evidence-guided experiment selection under scoped
authority. ClimbHill separates:

1. Diagnosis: what might explain insufficient progress?
2. Experiment selection: what action would discriminate between explanations?
3. Authority: what may the system inspect, change, or promote?
4. Optimization: what Attempt should replace the baseline within the selected
   Focus?

The controller may recommend actions. Deterministic policy and Decisions control
whether those actions can execute.

## 3. Job To Be Done

When I need a Git-backed artifact or agentic workflow to perform a job at a
materially higher quality and efficiency bar, I want ClimbHill to gather relevant
evidence, try bounded alternatives, determine which problem-solving surface needs
attention, and preserve every result, so progress compounds without silently
changing my evaluator, policy, or deployment state.

## 4. Product Principles

1. **Run-centered engine.** A standalone Run is executable and auditable without
   loading a Job.
2. **Git owns revisions.** Commits and branches represent content history;
   ClimbHill stores semantic lineage as metadata.
3. **One primary Focus.** A Run changes one declared surface with a resolved
   writable scope.
4. **External evaluation.** Every optimization is judged by evidence outside the
   surface being optimized.
5. **Scoped autonomy.** Work may continue within an Authorization Envelope;
   widening the envelope requires authority.
6. **Recommendation is not authority.** Agentic Continuation Analysis cannot
   authorize or execute itself.
7. **Least change first.** Prefer lower-scope diagnostic or optimization actions
   when they can produce useful evidence.
8. **Failure is not evaluator error.** Alignment requires evidence outside the
   evaluator being challenged.
9. **Filesystem is canonical.** Version-controlled YAML and Markdown are the
   source of truth; SQLite is a rebuildable cache.
10. **Partial work remains evidence.** Failure, cancellation, budget termination,
    and stale reasoning remain inspectable.
11. **Local utility requires no account.** Accounts may add identity,
    collaboration, persistence, hosted execution, or trust services, but not gate
    the open workflow spine.

## 5. Scope

### 5.1 In Scope

- One Run optimizing one primary Focus in one Target or Control Repository.
- Parent-linked Run trees pursuing a root objective.
- Optional Jobs for grouping and reusable defaults.
- Task, learning, and alignment Focuses.
- Learning subtypes `skill`, `tool`, `environment`, `context`, and `workflow`.
- Capability-specific repository and machine assessment.
- Worktree, isolated-clone, container, sequential in-place, and manual execution
  adapters.
- Typed Attempts, Evaluations, Decisions, Continuation Analyses, and consumption
  receipts persisted as files.
- Human preference, calibration, and hidden holdout evidence.
- Source ingestion, typed derivation, OKF research storage, graph construction,
  and bounded research.
- Split-control and Ouroboros repository modes.
- npm CLI distribution, `npx skills` distribution, and a Remix website.

### 5.2 Out Of Scope For Initial Release

- A bespoke recursive revision graph or custom Git ref namespace.
- Campaign, Proposal, Judgment, Hypothesis, or ContinuationAnalysis aggregate
  roots.
- Automatic merge, deployment, evaluator adoption, or promotion.
- Mandatory worktrees.
- Jobs spanning multiple Target Repositories.
- A hosted agent cloud or hosted source-of-truth database.
- Real-time multi-user collaboration.
- Deleting user data without an explicit command.

## 6. Domain Model

### 6.1 Recursive Optimization

| Term | Definition |
| --- | --- |
| Run | One bounded optimization pass with an immutable Baseline, one Focus, an external Evaluation Strategy, an Authorization Envelope, and a Promotion Target. |
| Attempt | One proposed mutation of the Run's Focus, represented by a Git commit or pre-promotion patch. |
| Evaluation | A versioned measurement or judgment of an Attempt under the evaluator pinned by its Run. |
| Decision | A recorded assertion of authority to authorize, promote, reject, continue, stop, or override. |

These are the recursive engine's only first-class concepts.

### 6.2 UX And Supporting Records

| Term | Definition |
| --- | --- |
| Job | Optional human-facing grouping and defaults copied into new Runs. |
| Assessment Finding | Timestamped evidence about a repository or machine capability. |
| Continuation Analysis | Immutable synthesis of hypotheses, evidence, and one typed recommendation at an Evidence Snapshot. |
| Authorization Envelope | Bounded grant for Attempts, diagnostics, child Focuses, cost, runtime, and depth. |
| Execution Eligibility | Current deterministic result of policy, authority, budget, freshness, and Focus checks. |

These are typed files or value objects. They do not own independent lifecycles in
the MVP.

### 6.3 Research

Research retains its own concepts: Resource, Observation, canonical graph Entity,
Claim, Relationship, Topic, and OKF Bundle. A recursive Run pins research by
Control commit and path rather than owning or duplicating it.

## 7. Loop Model

All loop kinds share one controller:

```text
Loop = immutable baseline + mutable focus + evaluation strategy + promotion target
```

| Run kind | Mutable Focus | Evaluation outside the Focus | Promotion Target |
| --- | --- | --- | --- |
| `task` | Artifact performing the user's job | Tests, benchmarks, rubrics, human preference | Product/task artifact |
| `learning` | Harness producing Attempts | Frozen tasks and holdout benchmarks | Skill, tool, environment, context, or workflow |
| `alignment` | Evaluation definition or judge configuration | Human judgments and held-out calibration data | Evaluation Strategy |

An Attempt may not change the evaluator that scores it. Alignment Runs pin a
separate meta-evaluator outside their proposed evaluator paths.

## 8. Persistence Model

The Control Repository owns canonical state:

```text
<control-repository>/
└── .climbhill/
    ├── config.yaml
    ├── jobs/
    │   └── <job-id>.yaml
    ├── runs/
    │   └── <run-id>/
    │       ├── run.yaml
    │       ├── attempts/
    │       ├── evaluations/
    │       ├── decisions/
    │       ├── continuation/
    │       ├── artifacts/
    │       └── events.jsonl
    ├── assessments/
    ├── evaluations/
    ├── policies/
    ├── research/
    │   ├── raw/
    │   └── okf/
    └── cache/
        └── registry.sqlite
```

Runs are not nested beneath Jobs. Run identity survives Job rename or deletion.
SQLite is ignored and rebuildable from canonical files.

Raw research artifacts are immutable to derivation. Git LFS is used when
available; otherwise raw bytes are ignored with visible migration instructions.
Derived research and Run records remain version-controlled.

## 9. Repository Modes

### 9.1 Split Control

Target and Control are different Git repositories. The Target contains product
state and promoted executable behavior. The Control Repository versions research,
policies, evaluations, and Run trees.

### 9.2 Ouroboros

Target and Control resolve to the same Git repository. Their commits may be equal
or different, but a Run always records both roles explicitly. A worktree is one
possible adapter, not an identity or initialization prerequisite. Assessment may
select an isolated clone, container, sequential in-place execution, manual
execution, or declare a capability unsupported.

## 10. Primary CLI Interface

The human interface is intentionally small:

```bash
climbhill assess
climbhill run "Improve release reliability"
climbhill status
climbhill decide --promote <attempt-id>
```

Jobs remain optional conveniences:

```bash
climbhill job create release-reliability
climbhill run --job release-reliability
climbhill job status release-reliability
```

Advanced Run creation remains secondary:

```bash
climbhill run --focus task "Improve release reliability"
climbhill run --focus learning:environment --from <run-id>
climbhill run --focus alignment --from <run-id>
```

Low-level Attempt, Evaluation, Decision, policy, and history commands may exist as
agent-facing plumbing. Humans do not manually operate recursion in the ordinary
workflow.

Research commands remain composable:

```text
climbhill add -> climbhill derive -> climbhill graph build -> climbhill research
```

## 11. Functional Requirements

### FR-1: Initialize Repositories

```bash
climbhill init --target <repo> [--control <repo>]
```

The command must validate Target and Control repositories, default Control to
Target for Ouroboros operation, create canonical Control directories without a
Job, record portable repository identities, preserve active branches, configure
Git LFS or an explicit fallback, create conservative policy/evaluation/ignore
templates, and avoid creating a worktree until assessment selects that adapter.

Acceptance criteria:

- Split-control and Ouroboros initialization preserve active branches.
- A standalone Run can be created immediately without a Job.
- Re-running init is idempotent and does not create ambiguous state.

### FR-2: Assess Capabilities

```bash
climbhill assess [--target <repo>] [--control <repo>]
```

Assessment combines deterministic probes with lightweight agentic skills. It
must probe install/build/test/cleanup, credentials, services, ports, shared state,
Git behavior, and evaluator availability; report individual capabilities; assess
all supported execution adapters; persist evidence, timestamp, commits, and
machine fingerprint; recommend an adapter without granting authority; and expose
missing or unaligned evaluation criteria.

A Run pins the assessment path and content hash it relied upon. Git-versioned
environment definitions do not prove that the current machine satisfies them.

### FR-3: Add One Source

```bash
climbhill add <url-or-file> [--type <type>] [--no-derive]
```

`add` retrieves one logical source, selects a source adapter, preserves original
bytes and metadata, hashes content, creates or updates an OKF Resource, runs
default derivation unless disabled, preserves ingestion when derivation fails,
and creates an immutable source version when content changes.

Initial adapters are local file, PDF, webpage, YouTube, and arXiv. Identical
content must not duplicate bytes or concepts. Evidence locators must be
timestamp-addressable for transcripts and page-addressable for PDFs.

### FR-4: Derive Source-Local Knowledge

```bash
climbhill derive [--resource <id>] [--append-prompt <text>] [--prompt-file <path>]
```

Typed BAML functions derive source-local entities, claims, opinions, procedures,
relationships, terminology, practices, and research gaps. Every Observation
retains Resource identity and the best available exact locator.

Derivation identity includes raw content hash, profile, resolved prompt, model,
schema, and chunking policy. Identical identity is a true cache hit; changed
identity creates distinct output without overwriting prior derivations.

### FR-5: Build The Knowledge Graph

```bash
climbhill graph build
climbhill graph inspect
```

Graph construction explicitly detects ontology, resolves duplicate entities,
normalizes relationships, reconciles supporting and conflicting claims, preserves
all contributing Observations, and exposes uncertainty without forcing merges.
Rebuilding unchanged inputs must be idempotent.

### FR-6: Run Bounded Research

```bash
climbhill research <question> [--local-only] [budget options]
```

Research is a bounded BAML-defined Research Execution, not a recursive Run. It
must inspect local evidence first, plan gaps, discover sources when permitted,
ingest relied-upon sources through `add`, derive through `derive`, cite local OKF
concepts, and persist plan, searches, sources, costs, time, errors, partial work,
and stopping reason. Graph reconciliation remains explicit.

### FR-7: Create A Run

```bash
climbhill run <objective> [--focus <kind>] [--from <run-id>] [--job <job-id>]
```

Before the first Attempt, Run creation must:

1. Resolve and pin Target and Control commits.
2. Resolve one semantic Focus to one repository and writable path set.
3. Pin Evaluation Strategy, policy, ignore fingerprint, assessment, Continuation
   Policy, budgets, Promotion Target, and Authorization Envelope.
4. Verify that the evaluator is outside the mutable Focus.
5. Copy optional Job defaults so execution no longer depends on the Job.
6. Record parent Run, spawning Decision, and explicitly inherited outputs.
7. Reject missing commits, unresolved paths, stale required assessment, and
   unauthorized Focus before execution.

Schemas and validation rules are normative in
[docs/recursive-loops.md](docs/recursive-loops.md).

### FR-8: Execute Attempts

Within one Run, the engine may create multiple Attempts without another authority
gate while baseline, Focus, evaluator, Promotion Target, and Authorization
Envelope remain unchanged.

Each Attempt records strategy, agent/model configuration, repository, base
commit, branch or patch, result commit when available, adapter, timestamps,
actual changed paths, diff hash, cost, policy verification, and semantic lineage.

Pre-execution path checks constrain tools. Post-execution verification against the
actual Git diff is authoritative. A promotable Attempt requires a Git commit.

### FR-9: Evaluate Attempts

Every Evaluation records evaluator commit, path, hash, capability, execution
status, verdict, requiredness, criteria, trusted evidence summary, raw artifacts,
and environment fingerprint.

Execution status and verdict are separate. Pending, running, errored, cancelled,
inconclusive, and skipped results are not ordinary failures. Results from
different evaluator versions or cohorts must never be aggregated as equivalent.

Learning Evaluations run proposed harnesses against frozen task suites and
holdouts. Alignment Evaluations compare proposed evaluators against human
preference, false-positive/negative cases, ranking stability, variance, cost,
criterion redundancy, and hidden holdouts.

### FR-10: Analyze Continuation

At a quiescent Evidence Snapshot, the pinned Continuation Policy receives typed,
controlled evidence and returns an immutable Continuation Analysis. It must not
receive arbitrary raw artifacts, repository access, secrets, or hidden holdouts.

The recommendation action is exactly one of:

```text
attempt | evaluate | promote | spawn_run | stop
```

Each action has a typed payload sufficient for deterministic validation. Prose is
never parsed for executable scope. Hypothesis status and confidence are relative
to the analysis snapshot.

The policy must prefer diagnostic evidence when competing explanations cannot be
distinguished. It may recommend another Attempt in the current Focus or a child
Run with a different Focus, but it grants neither authority nor eligibility.

### FR-11: Enforce Authority And Eligibility

Deterministic control separately computes authorization (`allowed`,
`requires_decision`, or `denied`) and execution eligibility at the current state.
Effective execution permission intersects the Authorization Envelope, repository
policy, loop-scoped ignore rules, remaining budgets, evidence freshness, and
resolved Focus.

A child inherits an equal or narrower envelope. Widening Focus, depth, cost,
runtime, tools, or paths requires a new Decision. Alignment is unavailable unless
explicitly granted.

Each recommendation has an atomic consumption key. Before claiming it, the engine
revalidates baseline, Evidence Snapshot, authority, eligibility, and budget.
Retries must not create duplicate Attempts or child Runs.

### FR-12: Decide And Promote

```bash
climbhill decide --promote <attempt-id>
```

A Decision records actor assertion, rationale, Evidence Snapshot, action, and the
authorization or eligibility facts it relied upon. Local identity is an explicit
human assertion; shared environments may attach authenticated evidence.

Promotion eligibility is computed, not stored as Attempt state. Eligibility
requires a promotable commit, Focus-compliant diff, successful post-execution
policy verification, all required passing Evaluations under the pinned evaluator,
current baseline/budget/target, and no unresolved approvals.

Promotion advances `task_artifact`, `harness`, or `evaluation_strategy` in the
declared repository, ref, and paths. Human approval is required in the MVP.

### FR-13: Continue And Stop

Changing Focus or widening the Authorization Envelope creates a child Run through
a Decision. Parent links provide recursion; no Campaign entity is introduced.

Every Run has local budgets. Descendants consume their root Run's remaining cost,
runtime, and depth budgets. The controller recognizes repetition, Focus cycling,
and diffusion without measurable progress. It stops on success, budget, risk, no
progress, insufficient evidence, authority, or unsupported operation while
preserving resumable state.

### FR-14: Enforce Edit Policy

Repositories may contain:

```text
.climbhillignore
.climbhillignore.task
.climbhillignore.learning
.climbhillignore.alignment
```

Global denies are monotonic. Loop-specific files add restrictions and cannot
negate a global deny. Files use Gitignore syntax relative to their repository.
Read restrictions and context exclusion remain separate from write protection.

Policy relaxation, budget increase, protected paths, CI, infrastructure,
security-sensitive changes, and deployment require explicit Decisions.

### FR-15: Promote Skills And Harness State

`.agent/skills` is the canonical Target location for executable agent behavior.
Promoting harness changes records the Control evidence, parent Run, Attempt,
Evaluations, Decision, and Promotion Target. Research facts remain in the Control
Repository rather than being embedded as volatile skill instructions.

### FR-16: Conform To OKF v0.2

The upstream OKF v0.2 specification must be vendored with source URL, commit,
retrieval date, checksum, and license. The research bundle must be independently
validatable, UTF-8, frontmatter-bearing, and tolerant of unknown fields.

### FR-17: Use BAML For Agentic Behavior

BAML definitions are canonical for prompts, typed model functions, Continuation
Policy outputs, derivation outputs, and agentic assessment outputs. Generated
Python and TypeScript clients are build artifacts. CI fails on generated-client
drift or invalid structured fixtures.

### FR-18: Distribute The Product

- Publish the CLI through npm with the `climbhill` executable.
- Publish installable skills through `npx skills`.
- Implement frontend code under `www/` using exactly `remix@3.0.0-beta.10`.
- Statically deploy the website to `climbhill.ai`.
- Preserve account-free local operation on supported platforms.

## 12. State Models

Run lifecycle:

```text
created -> running -> awaiting_decision -> completed
                  \-> failed
                  \-> cancelled
```

Attempt lifecycle:

```text
created -> running -> completed
                  \-> failed
                  \-> cancelled
```

Evaluation execution state:

```text
pending | running | completed | errored | cancelled
```

Evaluation verdict:

```text
passed | failed | inconclusive | skipped
```

Recommendation consumption:

```text
unconsumed -> claimed -> executed
                     \-> failed
```

All transitions are validated. Status, verdict, Decision action, Run kind,
learning subtype, recommendation action, and lineage relationship are closed
enums rather than arbitrary strings.

## 13. Non-Functional Requirements

### Reproducibility

- Pin commits, paths, content hashes, schemas, prompts, models, tools, and
  configuration.
- Distinguish unique analysis identity from an input fingerprint.
- Preserve stale Continuation Analyses as valid historical reasoning.
- Avoid floating model or package aliases in canonical records.

### Safety

- Never commit secrets or environment files.
- Treat source, repository, model, and tool output as untrusted.
- Pass untrusted artifacts through controlled readers before agentic analysis.
- Keep hidden holdouts outside Attempt and Continuation Policy context.
- Never allow an Attempt to change its own evaluator or policy.
- Avoid automatic merge, deployment, evaluator adoption, or promotion.

### Recoverability

- Use atomic writes for canonical records and compare-and-set for recommendation
  consumption.
- Preserve completed work after failures, cancellation, and budget termination.
- Resume from Run files without SQLite.
- Never rely on transient chat context as canonical state.

### Portability

- Use repository identities and commits rather than absolute local paths.
- Treat worktree/clone/container locations as adapter state, not identity.
- Keep canonical records human-readable and Git-diffable.

### Testability

- Interfaces accept filesystem, Git, clock, model, evidence-reader, evaluator,
  policy, and execution adapters.
- Tests exercise the same interfaces as CLI commands.
- Network and model calls have deterministic fakes.
- Integration fixtures cover split-control, Ouroboros, every adapter, stale
  evidence, authorization, and atomic consumption.

## 14. Adversarial Acceptance Scenarios

The target implementation must pass at least these scenarios:

1. A task Attempt edits its evaluator; post-execution policy rejects it.
2. Assessment finds worktrees unsafe and the Run succeeds with an isolated clone.
3. Evaluator V2 reverses V1's ranking; both result sets remain distinguishable and
   adoption requires a human alignment Decision.
4. A learning Attempt improves calibration but regresses hidden holdouts; it is
   ineligible without an explicit override.
5. A Continuation Policy recommends replacing itself; the old pinned policy and
   external historical-run evaluation remain authoritative.
6. New evidence arrives after analysis; the analysis remains historical but its
   recommendation cannot be consumed.
7. A recommendation is authorized but root budget is exhausted; authorization
   remains allowed while execution eligibility is denied.
8. A retried consumption does not create duplicate Attempts or child Runs.

## 15. Success Metrics

The initial product succeeds when:

1. A user can initialize repositories, assess capabilities, and start a standalone
   Run without creating a Job.
2. A single `climbhill run` invocation can continue automatically within a bounded
   Authorization Envelope and pause cleanly at an authority boundary.
3. Every Attempt is reproducible from its Run Baseline, Focus, adapter, and model
   metadata.
4. Every Evaluation identifies its evaluator and distinguishes execution state
   from verdict.
5. Every promotion is traceable to an eligible Attempt and human Decision.
6. Task failure alone cannot trigger evaluator modification.
7. Root-tree cost, runtime, depth, Focus transitions, and no-progress signals are
   derivable without a Campaign entity.
8. The SQLite cache can be deleted and rebuilt from canonical files.
9. Research remains cited, versioned, and reusable by later Runs.
10. ClimbHill completes a bounded Ouroboros Run against itself without assuming a
    worktree.

## 16. Current State And Gap Analysis

The repository contains an npm MVP with file-backed state, source adapters, BAML
research, graph construction, OKF validation, policy gates, recursive
Run/Attempt records, a rebuildable SQLite index, and a Remix site. A transitional
Python CLI and MCP server remain as secondary surfaces.

| Area | Current implementation | Target gap | Priority |
| --- | --- | --- | --- |
| Recursive model | File-backed Runs, Attempts, Evaluations, lineage, costs, and human Decisions | Add closed states, Focus, baseline, evaluator/policy/assessment pins, Promotion Target, and Continuation Analysis | P0 |
| Job | npm initialization and discovery require a Job-owned control checkout | Make Job optional UX and make standalone Runs canonical | P0 |
| Assessment | File-presence and provider-secret checks | Add capability findings, agentic assessment skills, and adapter selection | P0 |
| Execution | Job setup creates worktree-oriented control isolation | Add assessed worktree, clone, container, sequential, and manual adapters | P1 |
| Evaluation | Manually recorded free-form result rows | Enforce pinned strategies, state/verdict split, partitions, provenance, and eligibility | P0 |
| Continuation | Canned reflection and issue proposals | Add typed Continuation Input/Analysis, recommendations, hypotheses, freshness, and consumption | P0 |
| Authority | Advisory path checks and free-form Decisions | Add envelopes, deterministic intersection, child inheritance, and human promotion gate | P0 |
| Persistence | Files are canonical and SQLite is rebuildable under the Job workspace | Move Run identity outside Job ownership and preserve cache rebuild guarantees | P0 |
| Research | Unified ingestion, BAML derivation, explicit graph, and bounded local-first execution | Separate Research Execution records from recursive optimization Runs | P1 |
| CLI | Manual low-level orchestration | Implement deep `assess`, `run`, `status`, and `decide` modules | P0 |
| Skills | `.agent`, `.agents`, and top-level skill locations coexist | Make `.agent/skills` canonical for promoted Target behavior | P1 |
| Distribution | npm CLI, Python package, Codex plugin, release workflows, and Remix site | Make npm the complete primary interface and retire transitional Python orchestration | P1 |

## 17. Delivery Plan

### Phase 0: Contract And Terminology

- Adopt the recursive-loop contract, context map, and ADR.
- Use Attempt terminology exclusively, without aliases.
- Define language-neutral schemas and fixtures for Run, Attempt, Evaluation,
  Decision, Continuation Analysis, assessment, and consumption.
- Freeze closed enums, CLI help, exit codes, and policy precedence.

### Phase 1: File-Backed Run Engine

- Implement standalone Run storage and optional Job projections.
- Implement Baseline, Focus, evaluator, policy, assessment, budget, authorization,
  and Promotion Target resolution.
- Implement SQLite cache rebuild from canonical files.
- Implement validated state transitions and atomic writes.

### Phase 2: Assessment And Execution

- Implement deterministic probes and agentic assessment skills.
- Implement execution adapters and environment verification.
- Implement pre-execution constraints and authoritative post-diff checks.

### Phase 3: Evaluation And Decisions

- Implement pinned evaluator loading and typed Evaluation records.
- Implement eligibility computation, human preference, calibration, and holdouts.
- Implement typed Decisions and explicit surface promotion.

### Phase 4: Continuation Controller

- Implement typed Continuation Input and BAML output.
- Implement hypotheses, closed recommendations, focus resolution, authorization,
  eligibility, freshness, and atomic consumption.
- Implement child Runs, root budgets, repetition, cycling, and diffusion detection.
- Evaluate Continuation Policies on frozen historical Run trees.

### Phase 5: Research And Knowledge

- Implement unified source adapters, derivation identity, and BAML clients.
- Implement explicit knowledge graph construction and bounded Research Execution.
- Pin research evidence into Runs by Control commit and path.

### Phase 6: Distribution And Dogfooding

- Publish the npm CLI and skills.
- Build and deploy the Remix website.
- Run ClimbHill against itself across task, learning, and alignment Focuses.
- Use historical Run trees to improve the Continuation Policy through a
  `learning:workflow` Run.

## 18. Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Attempt changes its evaluator or authority | Pin evaluator/policy outside Focus and verify the actual diff after execution. |
| Agentic recommendation smuggles scope | Resolve semantic Focus and executable paths deterministically. |
| Authorized action is stale or unaffordable | Compute execution eligibility separately immediately before atomic claim. |
| Continuation Policy cycles or diffuses | Track tree-level progress, repetition, cycling, diffusion, depth, cost, and runtime. |
| Alignment rewards evaluator gaming | Require external human and hidden holdout evidence; prohibit self-evaluation. |
| Hidden holdouts leak into optimization | Expose typed results through evaluator adapters, never raw cases. |
| Worktree assumptions break repositories | Assess capabilities and select among multiple execution adapters. |
| Duplicate side effects after retry | Use immutable consumption keys and compare-and-set claims. |
| Control state becomes a second VCS | Use ordinary Git commits/branches and semantic metadata only. |
| Optional Job becomes hidden engine state | Copy defaults into Run and require standalone Run audit tests. |
| Paid work exceeds expectations | Enforce local and root budgets continuously while preserving partial state. |
| Generated clients drift | Pin generators and fail CI on generated output mismatch. |

## 19. Remaining Product Decisions

- Exact npm package name and supported Node versions.
- Default model/provider resolution and credential configuration.
- Source adapter plugin manifest and installation mechanism.
- Default cost, runtime, depth, and Attempt budgets.
- Exact machine-fingerprint fields and assessment freshness rules.
- Control ref retention and publication policy.
- Whether generated BAML clients are committed or produced during package/CI
  builds.
- Exact ontology reconciliation and user correction workflow.
- Authenticated Decision evidence for shared or hosted workspaces.

## 20. MVP Release Criteria

The MVP is complete only when:

- The CLI installs from npm and exposes `assess`, `run`, `status`, and `decide`.
- A standalone Run works without a Job in split-control and Ouroboros modes.
- The four engine concepts have validated file-backed schemas and state machines.
- Task, every learning subtype, and alignment use the same controller contract.
- Assessment selects a safe execution adapter without assuming worktrees.
- Evaluation Strategies are pinned and cannot overlap mutable Focus paths.
- Continuation recommendations use the closed typed action union.
- Authorization and execution eligibility are independently inspectable.
- Recommendation consumption is stale-safe and at-most-once.
- Promotion is human-approved and advances an explicit surface.
- All adversarial acceptance scenarios pass.
- Research ingestion, derivation, graph construction, and bounded execution produce
  cited, reusable Control Repository evidence.
- Canonical state remains inspectable and resumable without SQLite.
- ClimbHill completes a bounded self-improvement Run against its own repository.
