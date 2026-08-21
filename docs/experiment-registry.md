# Run Store And Index

The Run store preserves durable recursive evidence outside transient agent
conversations. Canonical files are version-controlled; SQLite is only a rebuildable
index.

## Engine Records

- Run
- Attempt
- Evaluation
- Decision

Optional Job files and supporting assessment, continuation, consumption, cost,
event, and report records are indexed but are not additional engine roots.

## Run Tree

Each Run records an optional `parent_run` and the Decision that authorized its
creation. The tree is sufficient to derive total spend, runtime, depth, Focus
transitions, promotions, human interventions, repetition, cycling, and diffusion.
A separate Campaign record is unnecessary.

## Attempt Identity And Lineage

An Attempt records its Run, strategy, base commit, resulting commit or patch,
actual changed paths, adapter, evaluations, costs, and timestamps. Semantic
lineage supports `forked_from`, `inspired_by`, `combined_with`, `supersedes`,
`reverted_from`, `failed_due_to`, and `promoted_from`.

Semantic lineage never creates fake Git merge parents.

## Index Guarantees

- Deleting SQLite loses no canonical state.
- Every indexed row resolves to a canonical file.
- Foreign references are validated within the same Control Repository.
- Closed states and action types are validated while indexing.
- Evaluation results remain partitioned by evaluator identity and cohort.
- Stale Continuation Analyses remain queryable but cannot be consumed.
- Recommendation consumption keys are unique and at-most-once.

See [recursive-loops.md](recursive-loops.md) for normative schemas.
