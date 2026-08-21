---
name: experiment-tree-analysis
description: Analyze ClimbHill runs, attempts, lineage, costs, failures, and recurring constraints. Use for experiment-history diagnosis and evidence-backed follow-up proposals.
---

# Experiment Tree Analysis

Use this skill to analyze runs, attempts, failures, lineage, and recurring constraints.

## Inputs

- Registry path
- Run IDs or all recent runs
- Attempt summaries
- Evaluations
- Costs
- Human decisions
- Lineage records

## Procedure

1. List runs and attempts from the registry.
2. Group failures by command, policy surface, file area, and attempt lineage.
3. Identify repeated failure causes and repeated successful patterns.
4. Identify missing docs, weak tests, ambiguous policy, or expensive workflows.
5. Distinguish product-code problems from ClimbHill-process problems.
6. Produce issue proposals with evidence and acceptance criteria.

## Outputs

- Failure pattern summary
- Useful resource and skill observations
- Attempt lineage notes
- GitHub issue proposals

## Rubric

- Findings cite run IDs, attempt IDs, evaluations, or reports.
- Proposed issues are concrete and reviewable.
- The analysis does not invent causes unsupported by registry evidence.
- The next loop is clearer because of the analysis.
