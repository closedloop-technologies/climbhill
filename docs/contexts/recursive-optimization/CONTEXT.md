# Recursive Optimization

This context defines ClimbHill's controlled optimization of a Git-backed target.
It explains how evidence, authority, and promotion interact across task, learning,
and alignment work.

## Language

**Run**:
One bounded optimization pass that pins an immutable Target and Control baseline,
declares one mutable Focus, selects an external Evaluation Strategy, and names a
Promotion Target.
_Avoid_: Campaign, loop instance, workflow execution

**Attempt**:
One proposed mutation of a Run's Focus, represented by a Git commit or a patch
before it becomes promotable.
_Avoid_: Solution, revision object

**Evaluation**:
A versioned measurement or judgment of an Attempt using the Evaluation Strategy
pinned by its Run. Execution state and quality verdict are distinct.
_Avoid_: Test result, score, judge response

**Decision**:
A recorded assertion of authority to authorize, promote, reject, continue, stop,
or explicitly override work at a named evidence snapshot.
_Avoid_: Recommendation, automatic selection, status

**Job**:
Optional human-facing metadata that groups related Runs and supplies defaults
which are copied into each Run before execution.
_Avoid_: Engine root, campaign, run owner

**Baseline**:
The immutable Target commit and Control commit against which a Run operates.
_Avoid_: Current checkout, latest state, synthetic revision

**Focus**:
The one primary surface a Run may optimize, including its kind, repository, and
resolved writable paths.
_Avoid_: Scope request, permission, arbitrary diff

**Task Focus**:
A Focus that improves the artifact performing the user's job.
_Avoid_: Product loop, ordinary run

**Learning Focus**:
A Focus that improves the harness producing Attempts, with subtype `skill`,
`tool`, `environment`, `context`, or `workflow`.
_Avoid_: Meta loop, retraining, reflection

**Alignment Focus**:
A Focus that improves evaluation definitions or judge configuration using human
preference and held-out evidence outside the evaluator being changed.
_Avoid_: Repository alignment, test fixing, score optimization

**Evaluation Strategy**:
The immutable evaluator definition used to judge a Run's Attempts, identified by
Control commit, path, and content hash.
_Avoid_: Eval config, mutable test suite, proposed evaluator

**Promotion Target**:
The repository, ref, paths, and control surface advanced when an Attempt is
promoted.
_Avoid_: Merge destination, winner, output branch

**Authorization Envelope**:
A bounded grant defining which Attempts, diagnostics, and child Focuses may be
explored within quantitative limits.
_Avoid_: Policy, eligibility, unrestricted autonomy

**Execution Eligibility**:
The deterministic, current-state result of intersecting authority, policy,
budgets, freshness, and resolved Focus constraints for one proposed action.
_Avoid_: Authorization, recommendation, approval

**Continuation Policy**:
Pinned harness behavior that synthesizes frozen evidence into hypotheses and one
typed recommendation without granting authority or executing it.
_Avoid_: Router, recursive agent, orchestrator authority

**Continuation Analysis**:
An immutable Run artifact containing snapshot-relative hypotheses, evidence
references, a typed recommendation, alternatives, and policy execution metadata.
_Avoid_: Decision, global diagnosis, plan

**Recommendation**:
A typed proposal to `attempt`, `evaluate`, `promote`, `spawn_run`, or `stop`.
_Avoid_: Command, authorization, side effect

**Evidence Snapshot**:
The frozen set of typed evidence used by one Continuation Analysis.
_Avoid_: Latest evidence, raw logs, context window

**Hypothesis**:
A snapshot-relative explanation that Continuation Analysis marks active,
supported, contradicted, or unresolved using explicit evidence references.
_Avoid_: Fact, Evaluation, permanent diagnosis

**Child Run**:
A Run created from a parent Decision when useful progress requires a different
Focus or authorization envelope.
_Avoid_: Nested directory, subtask, recursive primitive

**Assessment Finding**:
Timestamped evidence about a repository or machine capability used to select an
execution adapter or expose a readiness constraint.
_Avoid_: Global readiness score, Run, environment definition

**Execution Adapter**:
The mechanism used to isolate and execute an Attempt, such as a worktree,
isolated clone, container, sequential in-place execution, or manual execution.
_Avoid_: Environment, Focus, required worktree

## Governing Statements

**External Evaluation Principle**:
Every optimization is judged by evidence outside the surface being optimized.
_Avoid_: Self-scoring, evaluator mutation during a Run

**Scoped Autonomy Principle**:
Autonomy may continue within an Authorization Envelope; changing the envelope
requires a Decision.
_Avoid_: Child Runs are always manual, unrestricted recursive execution

**Alignment Evidence Principle**:
Failure against an evaluator is not evidence that the evaluator is wrong.
_Avoid_: Fix the test, optimize the score

**Least-Change Principle**:
When explanations remain plausible, prefer the lowest-scope action that yields
useful information or objective improvement.
_Avoid_: Always retry, always improve the harness
