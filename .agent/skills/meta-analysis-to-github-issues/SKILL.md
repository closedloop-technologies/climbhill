# Meta-Analysis to GitHub Issues

Use this skill to convert experiment-tree findings into concrete GitHub issue proposals.

## Inputs

- Experiment-tree analysis
- Run IDs
- Candidate IDs
- Failure evidence
- Relevant resources or reports

## Procedure

1. Select only findings with concrete evidence.
2. Write one issue per actionable repo improvement.
3. Include problem, evidence, suggested implementation, acceptance criteria, risk level, and labels.
4. Link or name the source run IDs and candidate IDs.
5. Store the issue proposal in the registry.
6. Export issue proposal Markdown for human review.

## Output Template

```markdown
# <Issue title>

Problem:

Evidence:

Suggested implementation:

Acceptance criteria:

Risk level:

Labels:
```

## Rubric

- Every issue proposal names evidence.
- Acceptance criteria are testable.
- Risk level is explicit.
- The proposal is ready for a human to convert into a GitHub issue.
