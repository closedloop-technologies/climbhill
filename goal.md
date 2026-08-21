# ClimbHill.ai Goal

## One-Sentence Goal

ClimbHill repeatedly decides what to improve next, gathers evidence when it is
uncertain, and changes only what it has authority to change.

## Product Boundary

ClimbHill is a local-first controlled optimizer over Git repositories. It begins
with a human objective and ends with an explicit promotion, a preserved stop, or a
clear authority boundary. It may optimize the task artifact, the harness producing
Attempts, or the evaluator judging them, but never lets an Attempt rewrite the
evaluator or authority governing its own Run.

## Core Thesis

Recursive self-improvement is evidence-guided experiment selection under scoped
authority.

The engine model is:

```text
Run -> Attempt -> Evaluation -> Decision
```

Jobs are optional UX projections. Git owns content history. Parent-linked Runs
provide recursion without a Campaign or bespoke revision graph.

## Success Criteria

ClimbHill is successful when a user can:

1. Assess whether a repository and machine support safe optimization.
2. Start a standalone Run without creating a Job.
3. Generate multiple Attempts inside a bounded Authorization Envelope.
4. Evaluate every Attempt with a pinned external strategy.
5. Gather diagnostic evidence instead of prematurely changing Focus.
6. Continue automatically while the authorization envelope remains unchanged.
7. Pause for authority before widening scope or promoting work.
8. Inspect the complete Run tree, costs, evidence, reasoning, and Decisions.
9. Promote an eligible task, harness, or evaluator change through ordinary Git.
10. Reuse research and failed Attempts as evidence in later Runs.
