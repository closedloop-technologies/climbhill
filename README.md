# ClimbHill.ai

> Controlled, measurable, recursive self-improvement loops for Git repositories and coding agents.

ClimbHill.ai helps coding agents improve a repository safely over repeated runs. It provides the repo-local structure, Codex plugin surface, MCP tools, skills, resources, policy gates, experiment registry, evaluation records, reports, and meta-analysis workflows needed to compare candidate improvements without losing human control.

The project is the renamed and narrowed successor to `awesome-llm-evolve`. It is not a generic deep-research catalog; it is a local-first substrate for agentic codebase improvement.

## Contents

- [Goal](#goal)
- [Boundary](#boundary)
- [Core Loop](#core-loop)
- [Components](#components)
- [Repo Alignment](#repo-alignment)
- [MVP Scope](#mvp-scope)
- [GitHub Pages Deployment](#github-pages-deployment)
- [Status](#status)

## Goal

ClimbHill.ai helps coding agents run controlled, measurable, recursive self-improvement loops on a Git repository while preserving human control, repository safety, historical memory, and clear promotion paths.

The central thesis is simple: a codebase should learn from every attempted improvement, not only the patches that merge. Failed candidates still produce useful evidence about constraints, brittle tests, weak docs, bad hypotheses, missing policy, and repo areas that are difficult for agents to improve.

## Boundary

ClimbHill.ai begins when a repository needs to be aligned for safe agentic improvement and ends when candidate improvements are evaluated, recorded, reported, and promoted into a pull request, issue, plan, or follow-up loop.

ClimbHill.ai is:

- A Codex plugin for distributing repo-improvement workflows.
- An MCP server that records runs, candidates, patches, evaluations, costs, decisions, and reports.
- A skill bundle under `.agent/skills` that teaches agents how to run recursive improvement loops safely.
- A `/resources` convention for research, prior art, user guidance, postmortems, and reusable experiment learnings.
- A policy system for allowed, denied, and approval-required edits.
- A candidate-evolution system for parallel attempts, historical sampling, recombination, comparison, and promotion.
- A reporting and meta-analysis layer for humans to inspect progress, risk, failures, and next actions.

ClimbHill.ai is not:

- A fully autonomous software company.
- A replacement for Git, GitHub, or CI.
- A hosted agent cloud.
- A model-training framework.
- A benchmark-only harness.
- A greenfield product-requirements generator.
- A tool that silently modifies tests to make candidates pass.
- A system that merges code without human approval by default.

## Core Loop

```text
Repository + Goal + Policy + Resources + Skills
  -> Run
  -> Candidate Attempts
  -> Policy Checks
  -> Tests and Evaluations
  -> Candidate Comparison
  -> Human Decision
  -> Promotion or Rejection
  -> Experiment Registry Update
  -> Meta-Analysis
  -> Issues, Resources, or Next Run
```

The loop is designed around seven principles:

- **Repo safety first**: protected surfaces are explicit before agents edit.
- **Out-of-band memory**: experiment state persists outside transient chats and scattered branches.
- **Every attempt teaches the next attempt**: failures are recorded as useful evidence.
- **Human control is a feature**: promotion remains visible and reviewable.
- **Evaluation before promotion**: candidates must pass checks and be compared against alternatives.
- **Skills over hidden magic**: agent-facing knowledge lives in readable files.
- **Small local MVP, expandable architecture**: SQLite, files, Git, and MCP first; hosted services later.

## Components

| Component | Purpose |
|-----------|---------|
| Codex plugin | Packages the workflows, MCP configuration, skills, policy templates, and install docs. |
| MCP server | Agent-facing runtime and system of record for runs, candidates, policy checks, evaluations, reports, and decisions. |
| CLI | Human-friendly commands such as `climbhill init`, `climbhill inspect`, `climbhill align`, `climbhill run`, `climbhill report`, and `climbhill reflect`. |
| Skills | Agent-readable procedures for alignment, historical sampling, candidate evolution, protected editing, reporting, and promotion. |
| Resources | Versioned context with provenance, trust level, tags, summary, and reason for inclusion. |
| Experiment registry | SQLite-backed durable state for repositories, goals, runs, candidates, evaluations, costs, decisions, reports, and issue proposals. |
| Policy layer | Conservative defaults for allowed edits, denied edits, approval-required paths, budgets, commands, and promotion gates. |
| Reporting layer | Markdown reports covering goal, repo state, policy, candidates, evaluations, costs, risks, decisions, recommendation, and next actions. |

## Repo Alignment

A repository is ClimbHill-aligned when it has enough structure for agents to improve it safely:

- `goal.md` describing the repo goal.
- `AGENTS.md` describing agent operating instructions.
- `README.md` describing setup and usage.
- `docs/architecture.md` or `ARCHITECTURE.md` describing design boundaries.
- `TESTING.md` describing test commands and expectations.
- `EVALS.md` describing evaluation strategy.
- `.climbhill/policy.yaml` defining edit and promotion policy.
- `.climbhill/eval.yaml` defining evaluation commands and rubrics.
- `.agent/skills/` for repo-local skills.
- `resources/` for research, context, and promoted learnings.
- Known install, lint, typecheck, test, and build commands when applicable.
- Branch, commit, and PR conventions.

ClimbHill should inspect a target repo, identify missing alignment pieces, and propose or create them without overwriting existing files unless a human approves.

## MVP Scope

The first useful version should include:

1. Standalone ClimbHill.ai repository with this goal.
2. Codex plugin metadata and installation documentation.
3. Local MCP server.
4. SQLite experiment registry.
5. `climbhill init` for adding repo alignment files.
6. Default `.climbhill/policy.yaml`.
7. Default `.climbhill/eval.yaml`.
8. At least five high-quality agent skills.
9. `/resources` convention and README.
10. Run and candidate registration.
11. Policy checking for patches.
12. Evaluation recording.
13. Markdown report generation.
14. Historical candidate sampling.
15. Meta-analysis that proposes GitHub issues.

MVP non-goals include hosted SaaS, multi-user accounts, billing, dashboards, automatic PR or issue creation, automatic merge, distributed workers, fine-tuned models, and support for every coding agent.

## Local CLI

The current Python CLI exposes the first local MVP primitives:

```bash
# Create conservative alignment files and a local SQLite registry
python -m awesome_deep_research.cli init --repo /path/to/repo

# Inspect alignment status
python -m awesome_deep_research.cli inspect --repo /path/to/repo

# Classify paths against .climbhill/policy.yaml
python -m awesome_deep_research.cli policy check src/app.py tests/test_app.py .env --repo /path/to/repo

# Create a run, register a candidate, record an evaluation, and generate a report
python -m awesome_deep_research.cli run --repo /path/to/repo --goal "Improve setup docs" --candidates 2
python -m awesome_deep_research.cli registry --repo /path/to/repo record-evaluation --candidate-id 1 --type test --status passed --command "pytest"
python -m awesome_deep_research.cli registry --repo /path/to/repo record-cost --run-id 1 --agent codex --model gpt-5 --estimated-usd 0.03
python -m awesome_deep_research.cli compare --repo /path/to/repo --run-id 1
python -m awesome_deep_research.cli decision --repo /path/to/repo --run-id 1 --candidate-id 1 --type promote --rationale "Best passing candidate"
python -m awesome_deep_research.cli report --repo /path/to/repo --run-id 1
python -m awesome_deep_research.cli reflect --repo /path/to/repo --run-id 1
```

The installed console script is `climbhill`; `adr` remains as a transitional compatibility alias for the previous package.

## GitHub Pages Deployment

This repo includes a zero-build landing page for `https://climbhill.ai/`:

- `index.html` - static landing page
- `assets/hero-research-harness.png` - generated hero artwork
- `CNAME` - custom domain declaration for `climbhill.ai`
- `.github/workflows/pages.yml` - GitHub Actions deployment workflow

Repository settings:

1. Go to **Settings -> Pages**.
2. Set **Build and deployment -> Source** to **GitHub Actions**.
3. Set the custom domain to `climbhill.ai` and enable HTTPS after DNS propagates.

DNS records at 101domain:

| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | closedloop-technologies.github.io |

The Pages workflow stages only the static site files into `_site` before deployment, so local files such as `.env` are not included in the published artifact.

## Status

This repository is in transition from the previous deep-research catalog toward the ClimbHill.ai product boundary. Current work should prioritize alignment files, plugin metadata, local MCP server design, registry schema, policy templates, and the initial skill bundle.

## License

[MIT](LICENSE)
