# ADR 0001: Control Branches And Worktrees

Status: Accepted

Each job owns a long-lived `climbhill/<job-id>` branch checked out in a separate worktree. The target's active worktree and the control repository's active worktree are never checked out to that branch during initialization.

The target stores a portable pointer containing repository identities and the control branch, but no checkout path. A machine-local locator under the target repository's Git common directory names the control repository checkout. Git's worktree registry resolves the current control worktree path, so `git worktree move` does not invalidate the job.

This applies equally to split-control and Ouroboros jobs. Recovery may recreate the machine-local locator from the portable pointer and a matching control repository.
