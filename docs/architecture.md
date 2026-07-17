# Architecture

ClimbHill.ai is a local-first system for controlled recursive improvement of Git repositories by coding agents.

## Major Components

- **Codex plugin**: distribution package for install instructions, MCP configuration, skills, policy templates, evaluation templates, and example workflows.
- **MCP server**: agent-facing runtime and system of record. It exposes tools for repo inspection, policy checks, resource search, run creation, candidate registration, evaluation recording, reporting, decisions, history sampling, and issue proposals.
- **CLI**: human-friendly commands over the same concepts, initially `climbhill init`, `inspect`, `align`, `run`, `report`, `reflect`, and `policy check`.
- **Experiment registry**: SQLite plus local file storage for repositories, goals, runs, candidates, patches, evaluations, costs, resources, policy snapshots, human decisions, reports, and issue proposals.
- **Policy layer**: conservative edit and promotion controls around allowed paths, denied paths, approval-required paths, budgets, command requirements, and protected surfaces.
- **Skills**: readable agent procedures under `.agent/skills` for alignment, sampling, candidate evolution, protected editing, reporting, and human promotion.
- **Resources**: reusable context under `resources/` with metadata for source, date, trust level, tags, summary, and reason for inclusion.

## Runtime Flow

```text
Repo + Goal + Policy + Resources + Skills
  -> Create Run
  -> Register Candidate Attempts
  -> Attach Patches and Code Pointers
  -> Check Policy
  -> Record Evaluations and Costs
  -> Compare Candidates
  -> Record Human Decision
  -> Generate Report
  -> Promote, Reject, or Reflect
```

## Data Model

The MVP registry should include:

- Repository
- Goal
- Resource
- Skill
- Run
- Candidate
- Evaluation
- Cost
- Human decision
- Report
- Issue proposal

Candidate lineage should support relationships such as `forked_from`, `inspired_by`, `combined_with`, `supersedes`, `reverted_from`, `failed_due_to`, and `promoted_from`.

## Safety Boundaries

Human approval is required by default for:

- Promotion to pull request.
- Modification of tests or evals.
- Modification of CI workflows.
- Modification of infrastructure.
- Modification of security-sensitive code.
- Budget increases.
- Policy relaxation.
- Merge or deployment.
