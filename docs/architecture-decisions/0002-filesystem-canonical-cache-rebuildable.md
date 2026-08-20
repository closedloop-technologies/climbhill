# ADR 0002: Filesystem Canonical, Cache Rebuildable

Status: Accepted

YAML and Markdown are canonical. The initial npm MVP stores them below
`.climbhill/<job-id>/`; the Run-centered layout stores Runs independently under
`.climbhill/runs/`. Runs use flat stable directories with parent references, and
OKF concepts remain independently readable and validate without SQLite.

`cache/registry.sqlite` is ignored and contains only indexes rebuilt by `climbhill cache rebuild`. Deleting it cannot remove a run, attempt, evaluation, decision, observation, graph concept, or promotion record. Writers use an atomic temporary-file rename for canonical records.
