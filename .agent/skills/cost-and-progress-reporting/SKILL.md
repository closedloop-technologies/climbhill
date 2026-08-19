---
name: cost-and-progress-reporting
description: Produce evidence-backed run and candidate reports with evaluations, costs, risks, and promotion recommendations. Use at the end of a ClimbHill run or candidate attempt.
---

# Cost and Progress Reporting

Use this skill at the end of a run or candidate attempt.

## Inputs

- Run goal
- Candidate list
- Tool logs
- Evaluation results
- Token and cost estimates when available
- Human decisions

## Procedure

1. Summarize the goal and repo state used.
2. List candidates with branch, commit, patch path, status, and summary.
3. Record tests, lint, typecheck, build, benchmark, rubric, and human review results.
4. Record costs: input tokens, output tokens, tool calls, wall-clock time, and estimated USD when available.
5. Highlight policy violations, approval-required edits, and unresolved risks.
6. Recommend promote, reject, or continue with another loop.
7. Propose next actions or GitHub issue drafts.

## Outputs

- Markdown run report
- Candidate comparison table
- Cost summary
- Risk summary
- Recommendation

## Rubric

- A maintainer can understand what happened without reading chat logs.
- Claims are grounded in recorded evidence.
- Costs and unknown costs are explicit.
- The recommendation is reviewable and reversible.
