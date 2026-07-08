# Safety Policy

The policy layer defines safe operating boundaries for agents.

## Policy Categories

- `allow`: paths agents may edit.
- `deny`: paths agents must not edit.
- `require_human_approval`: paths agents may edit only after approval.

## Protected by Default

- Tests and evals
- Snapshots
- CI workflows
- Lockfiles
- Migrations
- Infrastructure
- Security-sensitive code

## Promotion Requirements

Promotion should require passing tests, passing policy checks, recorded risk notes, recorded costs, and explicit human approval.
