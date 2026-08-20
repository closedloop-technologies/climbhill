# Repository Preparedness

Repository preparedness is the shallow check that expected support files exist. It is
not an Alignment Focus and does not establish execution readiness by itself.

## Expected Files

- `goal.md`
- `AGENTS.md`
- `README.md`
- `docs/architecture.md` or `ARCHITECTURE.md`
- `TESTING.md`
- `EVALS.md`
- `.climbhill/policy.yaml`
- `.climbhill/eval.yaml`
- `.agent/skills/`
- `resources/`

## Preparation Rules

ClimbHill should:

- Inspect existing files before proposing changes.
- Avoid overwriting existing guidance without approval.
- Identify known install, lint, typecheck, test, and build commands.
- Propose conservative policy defaults.
- Record unknowns instead of guessing.

`climbhill prepare` performs this file-presence check. `climbhill assess` is the
target command for evidence-backed setup, evaluation, isolation, and policy readiness.
