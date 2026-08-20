---
name: historical-attempt-sampling
description: Sample successful and failed historical ClimbHill Attempts before planning new work. Use when prior Runs may contain reusable approaches or known failure modes.
---

# Historical Attempt Sampling

Use this skill before generating a new attempt when prior ClimbHill runs exist.

## Inputs

- Current run goal
- Registry access or exported reports
- Prior attempt summaries
- Prior evaluation results
- Prior human decisions

## Procedure

1. Search prior runs with similar goals, files, failures, or evaluation patterns.
2. Sample both successful and failed attempts.
3. Extract reusable ideas, rejected approaches, brittle areas, and known constraints.
4. Identify attempt lineage that may matter: `inspired_by`, `failed_due_to`, `supersedes`, or `combined_with`.
5. Convert findings into a short plan for the next attempt.
6. Record which historical items influenced the new attempt.

## Outputs

- Sampled attempt list
- Lessons reused
- Failure patterns to avoid
- Attempt lineage notes

## Rubric

- The new attempt does not repeat known failures without justification.
- Useful partial solutions are identified.
- Human decisions are respected.
- Sources are linked to run IDs, attempt IDs, branches, commits, or reports.
