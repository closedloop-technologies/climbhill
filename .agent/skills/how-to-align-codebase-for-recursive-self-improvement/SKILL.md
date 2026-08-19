---
name: how-to-align-codebase-for-recursive-self-improvement
description: Align a repository for safe recursive improvement by defining goals, agent guidance, policies, evaluations, resources, and protected surfaces. Use when a codebase lacks ClimbHill operating structure.
---

# Align a Codebase for Recursive Self-Improvement

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
4. Propose missing alignment files before creating them.
5. Avoid overwriting existing files unless the human explicitly approves.
6. Write conservative policy defaults: protect tests, evals, CI, migrations, infra, lockfiles, and security-sensitive paths.
7. Record assumptions and unknowns in the alignment report.

## Outputs

- Alignment gap summary
- Created or proposed alignment files
- Known commands
- Protected surfaces
- Follow-up issues or questions

## Rubric

- The repo goal is explicit.
- Edit boundaries are machine-readable.
- Test and evaluation commands are recorded.
- Human approval surfaces are clear.
- Existing guidance is preserved.
