---
name: human-in-the-loop-promotion
description: Review policy, evaluations, cost, lineage, and risk before recording a human promotion or rejection decision. Use when a ClimbHill attempt is ready for disposition.
---

# Human-in-the-Loop Promotion

Use this skill when an Attempt is ready to be promoted, rejected, or converted into follow-up work.

## Inputs

- Attempt comparison
- Attempt patch or branch
- Evaluation records
- Policy check results
- Cost summary
- Risk notes
- Maintainer decision

## Procedure

1. Confirm the attempt has no denied path edits.
2. Confirm approval-required paths have explicit approval.
3. Confirm required tests and evaluations passed.
4. Review cost, risk, lineage, and report summary.
5. Ask the human to choose promote, reject, request changes, or run another loop.
6. Record the decision with actor, rationale, run ID, and attempt ID.
7. If promoted, prepare a PR-ready branch and checklist.
8. If rejected, record reasons so future attempts can avoid repeating the failure.

## Outputs

- Human decision record
- Promotion or rejection rationale
- PR-ready checklist or follow-up issue proposal

## Rubric

- No promotion happens without a recorded human decision.
- Policy and evaluation status are visible.
- Rejections preserve useful lessons.
- The next step is clear and reversible.
