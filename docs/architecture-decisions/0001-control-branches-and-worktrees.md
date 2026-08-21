# ADR 0001: Control Branches And Worktrees

Status: Superseded by `docs/adr/0001-run-centered-recursive-optimization.md`

Each job owns a long-lived `climbhill/<job-id>` branch checked out in a separate worktree. The target's active worktree and the control repository's active worktree are never checked out to that branch during initialization.

The target stores a portable pointer containing repository identities and the control branch, but no checkout path. A machine-local locator under the target repository's Git common directory names the control repository checkout. Git's worktree registry resolves the current control worktree path, so `git worktree move` does not invalidate the job.

This applied to the first npm MVP in split-control and Ouroboros modes. Recovery
may recreate its machine-local locator from the portable pointer and a matching
control repository.

The Run-centered contract no longer requires this topology. Worktree is one
Execution Adapter selected from assessment evidence alongside isolated clone,
container, sequential in-place, and manual execution. Jobs are optional UX
metadata and do not own Runs.
