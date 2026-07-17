# Experiment Tree Analysis

Use this skill to analyze runs, candidates, failures, lineage, and recurring constraints.

## Inputs

- Registry path
- Run IDs or all recent runs
- Candidate summaries
- Evaluations
- Costs
- Human decisions
- Lineage records

## Procedure

1. List runs and candidates from the registry.
2. Group failures by command, policy surface, file area, and candidate lineage.
3. Identify repeated failure causes and repeated successful patterns.
4. Identify missing docs, weak tests, ambiguous policy, or expensive workflows.
5. Distinguish product-code problems from ClimbHill-process problems.
6. Produce issue proposals with evidence and acceptance criteria.

## Outputs

- Failure pattern summary
- Useful resource and skill observations
- Candidate lineage notes
- GitHub issue proposals

## Rubric

- Findings cite run IDs, candidate IDs, evaluations, or reports.
- Proposed issues are concrete and reviewable.
- The analysis does not invent causes unsupported by registry evidence.
- The next loop is clearer because of the analysis.
