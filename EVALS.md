# Evaluation Strategy

ClimbHill evaluates candidates before promotion. A candidate is not better merely because it produced a diff.

## MVP Evaluation Types

- Unit tests
- Integration tests
- Type checks
- Lint checks
- Build checks
- Static analysis
- Rubric-based review
- Human review
- Regression checks

## Candidate Report Requirements

Each candidate evaluation should record:

- Candidate ID
- Evaluation type
- Command or rubric
- Status
- Score when applicable
- Log path
- Started and finished timestamps
- Failure reason when applicable

## Promotion Gate

By default, a promoted candidate must have:

- Passing required commands.
- No policy violations.
- Recorded risk notes.
- Recorded cost summary.
- Human approval.
- A branch or patch path suitable for PR review.
