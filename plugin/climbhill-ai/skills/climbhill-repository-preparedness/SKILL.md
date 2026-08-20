---
name: climbhill-repository-preparedness
description: Prepare a repository with goals, agent guidance, policies, evaluations, resources, and protected surfaces for controlled optimization. Use when setting up or auditing ClimbHill support files.
---

# ClimbHill Repository Preparedness

Use this skill when a repository needs enough structure for coding agents to improve it safely over repeated loops.

## Inputs

- Repository path
- User goal or repo mission
- Existing agent instructions
- Available install, lint, typecheck, test, and build commands

## Procedure

1. Inspect the repository tree, README, package metadata, tests, CI, and existing agent guidance.
2. Identify the repo goal, public API, protected surfaces, test strategy, and deployment path.
3. Check whether these files exist: `goal.md`, `AGENTS.md`, `README.md`, `docs/architecture.md` or `ARCHITECTURE.md`, `TESTING.md`, `EVALS.md`, `.climbhill/policy.yaml`, `.climbhill/eval.yaml`, `.agent/skills/`, and `resources/`.
4. Propose missing repository support files before creating them.
5. Avoid overwriting existing files unless the human explicitly approves.
6. Write conservative policy defaults: protect tests, evals, CI, migrations, infra, lockfiles, and security-sensitive paths.
7. Record assumptions and unknowns in the preparedness report.

## Outputs

- Preparedness gap summary
- Created or proposed repository support files
- Known commands
- Protected surfaces
- Follow-up issues or questions

## Rubric

- The repo goal is explicit.
- Edit boundaries are machine-readable.
- Test and evaluation commands are recorded.
- Human approval surfaces are clear.
- Existing guidance is preserved.
