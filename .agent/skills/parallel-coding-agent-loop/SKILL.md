---
name: parallel-coding-agent-loop
description: Coordinate independent, bounded coding candidates against one goal and compare them after policy and evaluation checks. Use for parallel ClimbHill improvement attempts.
---

# Parallel Coding Agent Loop

Use this skill to coordinate independent candidate attempts for the same goal.

## Inputs

- Run goal
- Active policy
- Candidate count
- Base branch and commit
- Required evaluation commands
- Budget limits

## Procedure

1. Create a ClimbHill run with the shared goal.
2. Register one candidate per planned attempt with a distinct branch name.
3. Give each candidate the same goal, policy snapshot, and required checks.
4. Keep candidates independent until after evaluation.
5. For each candidate, attach patch path, branch, head commit, cost, and evaluation records.
6. Compare candidates only after policy and evaluation results are recorded.
7. Recommend promote, reject, or recombine based on evidence.

## Outputs

- Run ID
- Candidate IDs
- Branch plan
- Evaluation matrix
- Recommendation

## Rubric

- Candidates are independent enough to compare.
- Every candidate has recorded policy and evaluation status.
- Costs are recorded or explicitly marked unknown.
- No candidate is promoted without human review.
