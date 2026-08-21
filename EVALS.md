# Evaluation Strategy

ClimbHill evaluates Attempts before promotion. Producing a diff is not evidence
that an Attempt is better.

## Evaluation Surfaces

- Task Attempts use tests, builds, benchmarks, rubrics, and human preference.
- Learning Attempts use frozen tasks and calibration/holdout suites.
- Alignment Attempts use human judgments, false-positive/negative cases, ranking
  stability, evaluator variance, cost, redundancy, and hidden holdouts.

Every Evaluation identifies its evaluator by Control commit, path, and content
hash. The evaluator must be outside the Run's mutable Focus.

## Record Requirements

Each Evaluation records:

- Run and Attempt IDs;
- evaluator identity and capability;
- execution state and quality verdict separately;
- requiredness, criteria, and score when applicable;
- trusted evidence summary and raw artifact paths;
- environment fingerprint;
- start and finish timestamps;
- execution error or failure reason when applicable.

Pending, running, errored, cancelled, inconclusive, and skipped Evaluations are not
ordinary failures.

## Promotion Gate

Promotion eligibility requires a promotable commit, Focus-compliant diff,
successful post-execution policy verification, every required Evaluation passing
under the pinned strategy, current baseline and budget, no unresolved approvals,
and a human Decision.

Eligibility is computed at an Evidence Snapshot and is not an Attempt status.
