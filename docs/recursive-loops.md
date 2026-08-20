# Recursive Loop Contract

This document defines the target contract for ClimbHill's recursive improvement
engine. Git owns content versioning. ClimbHill owns the writable focus, the
evaluation strategy, authority, evidence, and promotion decision.

The central abstraction is:

```text
Loop = immutable baseline + mutable focus + evaluation strategy + promotion target
```

Recursive self-improvement is evidence-guided experiment selection under scoped
authority. Recursion is not a separate engine primitive. A Run may recommend and,
when authorized, create a child Run with a different focus.

## Scope

The recursive engine has four fundamental concepts:

```text
Run -> Attempt -> Evaluation -> Decision
```

`Job` is optional UX metadata that groups Runs and supplies defaults. Research
concepts such as Resource and Observation belong to the research context, not the
recursive engine model.

Supporting records such as assessments, hypotheses, continuation analyses,
authorization envelopes, and consumption receipts remain typed files or values
inside the Run tree. They are not independent aggregate roots in the MVP.

## Principles

1. A Run is executable and auditable without loading a Job.
2. A Run pins target and control commits before creating an Attempt.
3. A Run declares one primary focus and a resolved writable scope.
4. Every optimization is evaluated by a strategy outside its mutable focus.
5. Actual changed paths must fit both the focus and resolved policy.
6. Agentic analysis may recommend; deterministic control grants no authority.
7. Autonomy may continue within an authorization envelope. Changing the envelope
   requires authority.
8. Promotion advances an explicit target surface and requires a human Decision in
   the MVP.
9. Historical reasoning remains valid for its evidence snapshot even after it is
   stale for execution.
10. Git ancestry records content ancestry only. Semantic relationships remain
    metadata.

## Repository Roles

The Target Repository contains the product or executable behavior being improved.
The Control Repository contains research, Run records, evaluation definitions,
calibration evidence, policies, and orchestration history. They may be different
repositories or the same repository in Ouroboros mode.

Ordinary Git commits and branches represent baselines and Attempts. ClimbHill does
not introduce a second revision graph, custom ref namespace, or synthetic merge
ancestry.

Canonical control state uses this layout:

```text
.climbhill/
├── jobs/                         # optional UX projections
│   └── <job-id>.yaml
├── runs/
│   └── <run-id>/
│       ├── run.yaml
│       ├── attempts/
│       │   └── <attempt-id>.yaml
│       ├── evaluations/
│       │   └── <evaluation-id>.yaml
│       ├── decisions/
│       │   └── <decision-id>.yaml
│       ├── continuation/
│       │   ├── <analysis-id>.yaml
│       │   └── consumptions/
│       ├── artifacts/
│       └── events.jsonl
├── assessments/
├── evaluations/
├── research/
└── cache/
    └── registry.sqlite          # rebuildable, never canonical
```

Runs live outside Job directories. Renaming, splitting, or deleting a Job does not
move or invalidate a Run.

## Job

A Job is an optional saved view over an objective and related Runs. It may provide
defaults, but Run creation resolves and copies those defaults into `run.yaml`.
Changing a Job never changes an existing Run.

```yaml
schema_version: 1
id: release-reliability
name: Release reliability
objective: Improve release reliability without increasing operator toil.

defaults:
  target_repository: https://example.com/acme/product.git
  control_repository: https://example.com/acme/climbhill-control.git
  research_paths:
    - .climbhill/research/release-reliability/**
  evaluation_path: .climbhill/evaluations/release-reliability.yaml
  budgets:
    cost_usd: 20
    runtime_seconds: 7200

created_at: 2026-08-19T18:00:00Z
```

Required fields are `schema_version`, `id`, `name`, `objective`, and `created_at`.
`defaults` is optional. Run membership is derived from each Run's optional
`job` reference rather than duplicated as a mutable list in the Job.

## Run

A Run is one bounded optimization pass over `task`, `learning`, or `alignment`
focus. It is the fundamental engine unit.

```yaml
schema_version: 1
id: run-42
job: release-reliability          # optional UX grouping only
parent_run: run-39                # optional
parent_decision: decision-17      # required when a Decision spawned this Run

kind: task                        # task | learning | alignment
objective: Make the release command recover cleanly after upload failure.

baseline:
  target:
    repository: https://example.com/acme/product.git
    commit: 8b29f9a
  control:
    repository: https://example.com/acme/climbhill-control.git
    commit: a64c212

inherits:
  accepted_attempts:
    - run: run-39
      attempt: attempt-2
  research:
    commit: a64c212
    paths:
      - .climbhill/research/release-reliability/**

focus:
  kind: task
  repository: target
  requested_paths:
    - src/release/**
    - tests/release/**
  resolved_writable_paths:
    - src/release/**
    - tests/release/**

evaluation_strategy:
  repository: control
  commit: a64c212
  path: .climbhill/evaluations/release-reliability.yaml
  content_hash: sha256:2b7d...

promotion_target:
  surface: task_artifact          # task_artifact | harness | evaluation_strategy
  repository: target
  base_ref: main
  paths:
    - src/release/**
    - tests/release/**

policy_snapshot:
  repository: control
  commit: a64c212
  path: .climbhill/policy.yaml
  content_hash: sha256:76ea...
  ignore_fingerprint: sha256:918c...

assessment:
  path: .climbhill/assessments/assessment-20260819T174500Z.yaml
  content_hash: sha256:814a...
  selected_adapter: isolated_clone
  verified_at: 2026-08-19T17:45:00Z

continuation_policy:
  repository: control
  commit: a64c212
  path: .climbhill/policies/continuation/default.yaml
  content_hash: sha256:502a...

authorization:
  source_decision: decision-1
  allow:
    attempts: true
    diagnostic_evaluations: true
    child_runs:
      task: true
      learning:
        - context
        - skill
  limits:
    child_depth: 3
    attempts: 8
    cost_usd: 20
    runtime_seconds: 7200
  promotion:
    automatic: false

budgets:
  local:
    attempts: 3
    cost_usd: 8
    runtime_seconds: 2400
  root:
    run: run-39
    remaining_cost_usd_at_start: 17.40
    remaining_runtime_seconds_at_start: 6100

status: running
created_at: 2026-08-19T18:02:00Z
started_at: 2026-08-19T18:02:04Z
finished_at: null
stopping_reason: null
```

Required Run fields are `schema_version`, `id`, `kind`, `objective`, `baseline`,
`focus`, `evaluation_strategy`, `promotion_target`, `policy_snapshot`,
`continuation_policy`, `authorization`, `budgets`, `status`, and `created_at`.
The Target and Control commits must resolve before the first Attempt begins.

Valid Run statuses are:

```text
created -> running -> awaiting_decision -> completed
                  \-> failed
                  \-> cancelled
```

`awaiting_decision` means execution has reached an authority boundary. It is not a
failure. Terminal states are `completed`, `failed`, and `cancelled`.

### Focus

All loop kinds use the same engine. They differ only in their writable surface and
evaluation strategy.

| Kind | Mutable focus | Typical external evaluation surface | Promotion surface |
| --- | --- | --- | --- |
| `task` | Product artifact performing the job | Tests, rubrics, benchmarks, human preference | `task_artifact` |
| `learning` | Harness behavior used to produce task Attempts | Frozen tasks and holdout benchmarks | `harness` |
| `alignment` | Evaluation definitions and judge configuration | Human judgments and held-out calibration data | `evaluation_strategy` |

Learning subtypes are `skill`, `tool`, `environment`, `context`, and `workflow`.
They share evaluation and promotion semantics. A learning Run must declare its
subtype:

```yaml
focus:
  kind: learning
  subtype: tool
  repository: control
  requested_paths:
    - tools/profiling/**
  resolved_writable_paths:
    - tools/profiling/**
```

An alignment Run distinguishes the proposed evaluator from the meta-evaluator
that judges it:

```yaml
focus:
  kind: alignment
  repository: control
  resolved_writable_paths:
    - .climbhill/evaluations/release-reliability/**

evaluation_strategy:
  repository: control
  commit: a64c212
  path: .climbhill/evaluations/meta/alignment.yaml
  content_hash: sha256:771b...
```

The two path sets must not overlap. Failure against an evaluator is not evidence
that the evaluator is wrong. Alignment requires evidence outside the challenged
evaluator.

## Attempt

An Attempt is one proposed mutation of the Run's declared focus. It is not
limited to product code: a learning Attempt may change the harness, and an
alignment Attempt may change an evaluation definition.

```yaml
schema_version: 1
id: attempt-3
run: run-42
status: completed

strategy:
  summary: Preserve upload state and resume only incomplete artifacts.
  agent: codex
  model: gpt-5.6
  configuration:
    reasoning_effort: high

git:
  repository: target
  base_commit: 8b29f9a
  branch: climbhill/run-42/attempt-3
  commit: 9e33a41
  patch_path: null

execution:
  adapter: isolated_clone
  started_at: 2026-08-19T18:04:00Z
  finished_at: 2026-08-19T18:18:31Z

changes:
  paths:
    - src/release/upload.ts
    - tests/release/upload.test.ts
  diff_hash: sha256:36df...
  policy_verification: evaluation-policy-attempt-3

lineage:
  - relationship: inspired_by
    attempt: attempt-1
    note: Retains the resumable state model but avoids its database migration.

cost:
  input_tokens: 18000
  output_tokens: 4200
  tool_calls: 37
  estimated_usd: 1.84
```

Required Attempt fields are `schema_version`, `id`, `run`, `status`, `strategy`,
`git`, `execution`, and `changes`. Either `git.commit` or `git.patch_path` is
required before evaluation, and a promotable Attempt requires a commit.

Valid Attempt statuses are:

```text
created -> running -> completed
                  \-> failed
                  \-> cancelled
```

Promotion eligibility is computed and is not an Attempt status.

Semantic lineage relationships include `forked_from`, `inspired_by`,
`combined_with`, `supersedes`, `reverted_from`, `failed_due_to`, and
`promoted_from`. They do not alter Git parents.

## Evaluation

An Evaluation is a versioned measurement or judgment of an Attempt. Execution
state and quality verdict are separate.

```yaml
schema_version: 1
id: evaluation-12
run: run-42
attempt: attempt-3

evaluator:
  repository: control
  commit: a64c212
  path: .climbhill/evaluations/release-reliability.yaml
  content_hash: sha256:2b7d...
  capability: integration-tests

execution:
  status: completed
  adapter: isolated_clone
  command: npm test -- release
  started_at: 2026-08-19T18:19:00Z
  finished_at: 2026-08-19T18:22:02Z
  exit_code: 0

verdict: passed
required: true
score: null

criteria:
  - id: interrupted-upload-recovery
    verdict: passed
    score: 1
    evidence:
      - artifacts/evaluation-12/test-results.json

evidence:
  trusted_summary: artifacts/evaluation-12/summary.yaml
  raw_artifacts:
    - artifacts/evaluation-12/stdout.txt
  failure_reason: null

environment:
  assessment: .climbhill/assessments/assessment-20260819T174500Z.yaml
  fingerprint: sha256:917d...

created_at: 2026-08-19T18:19:00Z
```

Evaluation execution statuses are:

```text
pending | running | completed | errored | cancelled
```

Evaluation verdicts are:

```text
passed | failed | inconclusive | skipped
```

An Evaluation with `execution.status: errored` has no quality verdict. Pending,
running, errored, cancelled, inconclusive, and skipped Evaluations must never be
counted as ordinary failures.

Learning and alignment Evaluations may compare a proposed change against a baseline
over calibration and holdout partitions:

```yaml
subjects:
  baseline_attempt: attempt-baseline
  proposed_attempt: attempt-3

partitions:
  calibration:
    aggregate_before: 0.61
    aggregate_after: 0.83
  holdout:
    aggregate_before: 0.79
    aggregate_after: 0.52

aggregate:
  calibration_delta: 0.22
  holdout_delta: -0.27
  verdict: failed
```

Hidden holdout content is supplied only to evaluator adapters. Attempts and the
Continuation Policy receive typed results, never arbitrary holdout access.

## Decision

A Decision records authority. A Run may contain multiple Decisions, including an
initial authorization, continuation authorization, and final promotion or
rejection.

```yaml
schema_version: 1
id: decision-17
run: run-42
action: promote                    # authorize | promote | reject | continue | stop | override
attempt: attempt-3

actor:
  kind: human
  label: maintainer@example.com
  assertion: interactive_local
  signed_evidence: null

rationale: Best eligible Attempt and acceptable operational risk.

eligibility_snapshot:
  evidence_snapshot: sha256:981e...
  promotable_commit: true
  required_evaluations_passed: true
  policy_verified: true
  authorization: allowed
  execution_eligibility: allowed

promotes:
  surface: task_artifact
  repository: target
  commit: 9e33a41
  base_ref: main
  paths:
    - src/release/**
    - tests/release/**

created_at: 2026-08-19T18:31:00Z
```

Local human identity is an explicit assertion, not cryptographic proof. Hosted or
shared environments may attach authenticated or signed evidence without changing
the local contract.

A promotion Decision must reference the computed eligibility snapshot. Recording
`action: promote` does not itself make an Attempt eligible.

## Promotion Eligibility

Promotion eligibility is computed at a specific evidence snapshot. It is never a
stored lifecycle state.

An Attempt is eligible only when all of the following are true:

1. The Attempt belongs to the Run and has a promotable commit.
2. Its changed paths fit the Run's resolved focus.
3. Post-execution policy verification passes for the actual Git diff.
4. All required Evaluations completed with `verdict: passed`.
5. The evaluator identity matches the strategy pinned by the Run.
6. The baseline, evidence snapshot, budgets, and promotion target are current.
7. No unresolved approval-required path remains.

Promotion still requires a human Decision in the MVP.

## Assessment And Execution Adapters

`climbhill assess` combines deterministic probes with lightweight agentic
assessment skills. It produces timestamped Job-independent evidence under
`.climbhill/assessments/`.

Assessment is capability-specific rather than a single readiness boolean:

```yaml
schema_version: 1
id: assessment-20260819T174500Z
subject:
  target_repository: https://example.com/acme/product.git
  target_commit: 8b29f9a
  machine_fingerprint: sha256:d911...

findings:
  - capability: parallel_worktrees
    outcome: unsupported           # supported | conditional | unsupported | unknown
    confidence: high
    evidence:
      - probe: test-isolation
        result: shared_database_path
    recommendation: isolated_clone

adapters:
  worktree: unsupported
  isolated_clone: supported
  container: conditional
  sequential_in_place: supported
  manual: supported

verified_at: 2026-08-19T17:45:00Z
```

Supported execution adapters are `worktree`, `isolated_clone`, `container`,
`sequential_in_place`, and `manual`. `unsupported` is an assessment outcome, not
an adapter. Git versions environment definitions; verification evidence records
whether the current machine satisfied them at a particular time.

An environment definition change is a `learning:environment` Run. Selecting an
already-supported adapter is deterministic execution planning, not optimization.

## Edit Policy

Ignore files are ergonomic write-protection inputs, not the complete authority
model:

```text
.climbhillignore
.climbhillignore.task
.climbhillignore.learning
.climbhillignore.alignment
```

Files use Gitignore pattern syntax relative to the governed repository root.
`.climbhillignore` contains global monotonic denies. A loop-specific file may add
denies but cannot negate a global deny. Negation patterns that would re-include a
globally denied path are invalid.

Policy resolution follows this order:

```text
global denies
  + loop-specific denies
  + repository policy
  + Run focus
  + authorization envelope
  = resolved writable scope
```

The engine validates intended paths before execution and the actual Git diff
after execution. The post-execution result is authoritative. An Attempt cannot
edit the evaluator or policy that governs its own Run, even if a broad path glob
would otherwise include those files.

Read restrictions and context exclusion are separate execution-policy concerns.
`.climbhillignore` controls writes only. Hidden holdouts and secrets must not be
made readable merely because they are write-protected.

## Continuation Controller

The controller has five layers:

```text
Evidence
  -> agentic Continuation Analysis
  -> governance
  -> deterministic control
  -> execution
```

Agents may operate in analysis and execution adapters. Agents do not own
Decisions, authorization intersection, budgets, state transitions, stale
detection, or recommendation consumption.

The controller interface is intentionally small:

```text
ContinuationPolicy.evaluate(ContinuationInput) -> ContinuationAnalysis
```

### Continuation Input

The policy runs only at a quiescent checkpoint in the MVP. Its input includes:

```yaml
run: run-42
evidence_snapshot: sha256:981e...

policy:
  commit: a64c212
  path: .climbhill/policies/continuation/default.yaml
  content_hash: sha256:502a...
  model: gpt-5.6
  configuration:
    reasoning_effort: high

authority_summary:
  permitted_child_focuses:
    - task
    - learning:context
    - learning:skill
  unavailable_focuses:
    - alignment
    - learning:environment

budget_summary:
  attempts_remaining: 1
  root_cost_usd_remaining: 3.00
  root_runtime_seconds_remaining: 900

evidence:
  attempts: []
  evaluations: []
  human_observations: []
  assessment_findings: []
  ancestry_summary:
    focus_transitions: []
    progress_deltas: []
    no_progress_signatures: []

prior_analyses: []
```

The policy receives typed evidence and controlled evidence capabilities, not
arbitrary repository access, raw stdout, Attempt prose, web content, secrets,
or hidden holdouts. Raw artifacts are untrusted and cross a controlled
reader/parser seam before entering Continuation Input.

### Continuation Analysis

A Continuation Analysis is an immutable Run artifact. Its hypothesis statuses are
relative to its evidence snapshot, not declarations of global truth.

```yaml
schema_version: 1
analysis_id: analysis-7
run: run-42
input_fingerprint: sha256:4a68...
evidence_snapshot: sha256:981e...
created_at: 2026-08-19T18:25:00Z

policy_execution:
  commit: a64c212
  path: .climbhill/policies/continuation/default.yaml
  content_hash: sha256:502a...
  model: gpt-5.6
  configuration_hash: sha256:1c43...
  tool_versions: {}

hypotheses:
  - id: harness-missing-profiler
    status: active                # active | supported | contradicted | unresolved
    confidence: medium            # low | medium | high
    explanation: Runtime evidence is insufficient to locate the bottleneck.
    evidence:
      supports:
        - evaluation-11
      contradicts: []

recommendation:
  consumption_key: rec-7
  action:
    type: evaluate
    capability: runtime-profile
    subjects:
      - attempt-3
  rationale: Distinguishes implementation inefficiency from missing diagnostics.
  evidence:
    - evaluation-11
  discriminates:
    - harness-missing-profiler
    - task-implementation-inefficient
  expected_result_effects:
    supports_harness_if: Profiling cannot be produced with pinned capabilities.
    supports_task_if: Profiling identifies an Attempt-local hot path.

alternatives:
  - action:
      type: spawn_run
      focus:
        kind: learning
        subtype: tool
      objective: Add runtime profiling capability.
    rationale: Higher-scope response if the diagnostic capability is absent.
```

Confidence is ordinal because model-emitted numeric probabilities imply
calibration the system does not possess.

### Recommendation Actions

The recommendation action is a closed tagged union:

```text
attempt | evaluate | promote | spawn_run | stop
```

Every action contains a typed payload sufficient for deterministic validation.
Natural-language rationale is never parsed to discover scope or mechanics.

`attempt` requests another Attempt under the existing Run contract:

```yaml
type: attempt
strategy:
  objective: Explore a streaming upload implementation.
  differs_from:
    - attempt-1
    - attempt-2
```

`evaluate` invokes a named diagnostic capability already available in the pinned
Control baseline:

```yaml
type: evaluate
capability: human-pairwise-comparison
subjects:
  - attempt-1
  - attempt-3
```

It cannot invent a new evaluator or tool. Missing capability supports a
`learning:tool` child Run.

`promote` selects only among Attempts that deterministic computation currently
marks eligible:

```yaml
type: promote
attempt: attempt-3
```

`spawn_run` proposes a semantic focus. Requested paths are hints, not authority:

```yaml
type: spawn_run
focus:
  kind: learning
  subtype: context
objective: Add release architecture context missing from every Attempt.
requested_paths:
  - docs/release/**
inherits:
  run: run-42
  evidence_snapshot: sha256:981e...
```

The deterministic focus resolver computes canonical writable scope before
authorization and eligibility checks.

`stop` uses a closed reason union:

```yaml
type: stop
reason: insufficient_evidence     # success | budget | risk | no_progress |
                                  # insufficient_evidence | authority | unsupported
resumable: true
```

Stopping an autonomous process does not declare the optional Job failed.

Alternatives may describe unauthorized actions because they are analysis, not
execution requests. Deterministic control annotates the recommendation and each
alternative with authorization and eligibility results after analysis.

### Diagnosis And Experiment Selection

The Continuation Policy follows this sequence:

1. Verify that evaluation evidence executed successfully and is trustworthy.
2. Generate competing explanations for insufficient progress.
3. If evidence cannot distinguish them, recommend the lowest-cost diagnostic
   action with useful expected information gain.
4. If evidence supports more optimization within the current focus, recommend
   another Attempt.
5. If evidence supports changing another surface, recommend a child Run.
6. If an eligible Attempt provides sufficient improvement, recommend promotion.
7. Stop on success, budget exhaustion, unacceptable risk, insufficient evidence,
   repeated no progress, cycling, diffusion, or an authority boundary.

The policy uses a least-change bias. Another task Attempt is generally preferred
to a harness mutation when both remain plausible. Alignment requires external
evidence such as human disagreement, holdout failure, criterion contradiction,
judge instability, proxy gaming, or inability to distinguish known-good from
known-bad cases.

### Authorization And Eligibility

Recommendation, authorization, and execution eligibility remain distinct:

```text
recommendation
  -> deterministic authorization check
  -> deterministic eligibility/preflight
  -> atomic consumption
  -> execution
```

Authority is what a Decision granted. Eligibility is whether the operation may
execute now. An authorized action may be ineligible because its baseline is
stale, budget is exhausted, required evidence is incomplete, or its resolved
scope violates policy.

Effective execution permission is the intersection of:

```text
authorization envelope
  + repository policy
  + loop-scoped ignore policy
  + remaining root and local budgets
  + resolved focus constraints
```

The Continuation Policy may know these constraints but cannot certify its own
authorization. A deterministic module returns `allowed`, `requires_decision`, or
`denied` and separately reports eligibility.

A child inherits an equal or narrower authorization envelope. Widening allowed
focus, depth, cost, runtime, tools, or paths requires a new Decision. Alignment is
unavailable unless explicitly granted.

### Freshness And Consumption

`analysis_id` is a unique record identity. `input_fingerprint` records whether two
analyses used the same policy definition, execution configuration, and evidence
snapshot. Reconsidering identical inputs creates another analysis record rather
than overwriting history.

A new evidence snapshot does not invalidate historical reasoning. It makes an old
recommendation stale for execution. The engine derives analysis succession from
creation order and snapshot ancestry; it does not mutate old analyses with a
`superseded_by` field.

Each recommendation has a unique `consumption_key`. Deterministic control uses an
atomic compare-and-set lifecycle:

```text
unconsumed -> claimed -> executed
                     \-> failed
```

Before claiming, the engine revalidates evidence freshness, baseline commits,
authorization, eligibility, and remaining budget. Retrying execution reuses the
claim and cannot create a second Attempt or child Run.

## Child Runs And Root Budgets

Creating another Attempt under an unchanged baseline, focus, evaluator, and
promotion target adds an Attempt to the same Run. Changing any element of that
authorization envelope creates a child Run.

The spawning Decision records the child objective, semantic focus, inherited
evidence, and authorization. The child pins fresh target and control commits and
never mutates its parent Run.

Parent links form the recursive tree. A separate Campaign entity is unnecessary.
The engine derives total spend, elapsed time, depth, focus transitions, promotion
count, and human interventions from the tree.

Every Run has a local budget. Every child also consumes the remaining budget of
its root Run. No-progress detection distinguishes:

- `repetition`: the same intervention recurs without material progress;
- `cycling`: focus transitions repeat, such as task -> context -> task -> context;
- `diffusion`: focus keeps changing without measurable progress toward the root
  objective.

These signals are evidence for `stop`, not automatic proof that the objective is
impossible.

## CLI Contract

The human interface remains small:

```bash
climbhill assess
climbhill run "Improve release reliability"
climbhill status
climbhill decide --promote <attempt-id>
```

Jobs are optional conveniences:

```bash
climbhill job create release-reliability
climbhill run --job release-reliability
climbhill job status release-reliability
```

Advanced focus selection is available without requiring users to operate the
recursive tree manually:

```bash
climbhill run --focus task "Improve release reliability"
climbhill run --focus learning:environment --from run-42
climbhill run --focus alignment --from run-42
```

Low-level Attempt, Evaluation, policy, and history commands are agent-facing
plumbing. The top-level `run` module owns orchestration behind a small interface.

## Adversarial Scenarios

### Evaluator Changes Mid-Run

A task Run pins the evaluator by Control commit, path, and content hash. Its focus
resolves only Target paths. If an Attempt changes `.climbhill/evaluations/**`, the
post-execution diff check rejects it. A legitimate evaluator change requires an
alignment child Run. Rescoring produces new Evaluation records without rewriting
the original results.

### Worktree-Incompatible Target

Assessment finds that Attempts share a fixed test database and marks parallel
worktrees unsupported. The Run pins the assessment and selects `isolated_clone`.
No model or schema changes are needed. If no automated adapter is safe, the Run
uses `manual` or stops as `unsupported` while preserving the evidence.

### Alignment Reverses Historical Ranking

An alignment Attempt contains evaluator V2. The alignment Run's pinned
meta-evaluator applies V2 to frozen historical Attempts and compares its ranking
against human preferences and hidden holdouts. V1 results remain attached to V1;
V2 rescoring creates new Evaluation records. A ranking reversal is visible rather
than aggregated across evaluator versions. Adopting V2 requires a human promotion
Decision targeting `evaluation_strategy`.

### Learning Improves Calibration But Regresses Holdout

A `learning:workflow` Attempt improves the current task suite but regresses a
hidden holdout partition. The external Evaluation records both deltas and returns
`failed`. Cheap checks cannot numerically offset the required holdout failure.
The Attempt is ineligible unless a human records an explicit override Decision
whose rationale and eligibility snapshot preserve the regression.

### Continuation Policy Recommends Its Own Replacement

The active Continuation Policy is pinned by the Run's Control baseline. It may
recommend a `learning:workflow` child Run that changes the policy, but the old
policy remains the analyzer for that recommendation. Proposed policies are
evaluated over frozen historical run trees. Neither the proposed policy nor the
policy proposing it may authorize or evaluate its own promotion.

## MVP Non-Goals

- A bespoke recursive revision graph.
- A Campaign aggregate.
- First-class Hypothesis, ContinuationAnalysis, Proposal, or Judgment entities.
- Custom Git ref namespaces or synthetic merge ancestry.
- Per-event Git commits.
- Mandatory worktrees.
- Automatic evaluator mutation or automatic promotion.
- Natural-language parsing in deterministic control.
- Exposing hidden holdouts to Attempts or the Continuation Policy.
