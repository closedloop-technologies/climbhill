---
name: protected-surface-editing
description: Classify proposed paths and enforce denied or approval-required ClimbHill policy before edits. Use when work may touch tests, CI, infrastructure, secrets, or other protected surfaces.
---

# Protected Surface Editing

Use this skill before touching paths that are denied or approval-required by ClimbHill policy.

## Inputs

- Active policy
- Proposed edit paths
- Reason for edit
- Human approval status

## Procedure

1. Read `.climbhill/policy.yaml` or the active policy snapshot.
2. Classify every proposed path as allowed, denied, or approval-required.
3. If any path is denied, stop and propose an alternative.
4. If any path requires approval, ask for human approval before editing.
5. For approved protected edits, keep changes minimal and document why they are necessary.
6. Record the policy check result in the candidate report.

## Outputs

- Path classification
- Approval request when needed
- Policy check result
- Risk notes

## Rubric

- Denied paths are not edited.
- Approval-required paths are not edited before approval.
- Protected edits are narrow and justified.
- Reports identify the protected surface and reason.
