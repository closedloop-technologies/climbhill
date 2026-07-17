# Repo Alignment

A repository is ClimbHill-aligned when coding agents have enough structure to improve it safely.

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

## Initialization Rules

ClimbHill should:

- Inspect existing files before proposing changes.
- Avoid overwriting existing guidance without approval.
- Identify known install, lint, typecheck, test, and build commands.
- Propose conservative policy defaults.
- Record unknowns instead of guessing.
