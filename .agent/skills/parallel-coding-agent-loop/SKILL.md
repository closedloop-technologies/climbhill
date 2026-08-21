---
name: parallel-coding-agent-loop
description: Coordinate independent, bounded coding attempts against one goal and compare them after policy and evaluation checks. Use for parallel ClimbHill improvement attempts.
---

# Parallel Coding Agent Loop

Use this skill to coordinate independent Attempts for the same Run objective.

## Inputs

- Run goal
- Active policy
- Attempt count
- Base branch and commit
- Required evaluation commands
- Budget limits

## Procedure

1. Create a ClimbHill run with the shared goal.
2. Register one attempt per planned attempt with a distinct branch name.
3. Give each attempt the same goal, policy snapshot, and required checks.
4. Keep attempts independent until after evaluation.
5. For each attempt, attach patch path, branch, head commit, cost, and evaluation records.
6. Compare attempts only after policy and evaluation results are recorded.
7. Recommend promote, reject, or recombine based on evidence.

## Outputs

- Run ID
- Attempt IDs
- Branch plan
- Evaluation matrix
- Recommendation

## Rubric

- Attempts are independent enough to compare.
- Every attempt has recorded policy and evaluation status.
- Costs are recorded or explicitly marked unknown.
- No attempt is promoted without human review.
