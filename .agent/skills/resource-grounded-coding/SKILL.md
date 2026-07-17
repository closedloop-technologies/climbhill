# Resource-Grounded Coding

Use this skill to ground code changes in `resources/` entries and cited prior work.

## Inputs

- Improvement goal
- Search query or known resource paths
- Active policy
- Target files

## Procedure

1. Search `resources/` for relevant prior art, user guidance, postmortems, and experiment summaries.
2. Prefer resources with explicit source, trust level, and reason for inclusion.
3. Summarize the resources that affect the planned edit.
4. If a useful source is missing, add it through the resource ingestion workflow before relying on it.
5. Implement changes that are traceable to the selected resources.
6. Record resource paths in the candidate summary or report.

## Outputs

- Resource list
- Trust notes
- Implementation plan
- Candidate summary with resource references

## Rubric

- Important claims are grounded in recorded resources.
- Untrusted resources are treated cautiously.
- New resources include source, summary, tags, trust level, and reason added.
- The candidate report explains how resources influenced the change.
