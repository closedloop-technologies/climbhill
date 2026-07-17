# Historical Candidate Sampling

Use this skill before generating a new candidate when prior ClimbHill runs exist.

## Inputs

- Current run goal
- Registry access or exported reports
- Prior candidate summaries
- Prior evaluation results
- Prior human decisions

## Procedure

1. Search prior runs with similar goals, files, failures, or evaluation patterns.
2. Sample both successful and failed candidates.
3. Extract reusable ideas, rejected approaches, brittle areas, and known constraints.
4. Identify candidate lineage that may matter: `inspired_by`, `failed_due_to`, `supersedes`, or `combined_with`.
5. Convert findings into a short plan for the next candidate.
6. Record which historical items influenced the new candidate.

## Outputs

- Sampled candidate list
- Lessons reused
- Failure patterns to avoid
- Candidate lineage notes

## Rubric

- The new attempt does not repeat known failures without justification.
- Useful partial solutions are identified.
- Human decisions are respected.
- Sources are linked to run IDs, candidate IDs, branches, commits, or reports.
