# ADR 0002: Filesystem Canonical, Cache Rebuildable

Status: Accepted

YAML and Markdown below `.climbhill/<job-id>/` are canonical. Runs use flat stable directories with parent references; OKF concepts remain independently readable and validate without SQLite.

`cache/registry.sqlite` is ignored and contains only indexes rebuilt by `climbhill cache rebuild`. Deleting it cannot remove a run, candidate, evaluation, decision, observation, graph concept, or promotion record. Writers use an atomic temporary-file rename for canonical records.
