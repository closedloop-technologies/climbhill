# ClimbHill.ai

> Controlled, measurable, recursive self-improvement loops for Git repositories and coding agents.

ClimbHill.ai helps coding agents improve a repository safely over repeated runs. It provides the repo-local structure, Codex plugin surface, MCP tools, skills, resources, policy gates, experiment registry, evaluation records, reports, and meta-analysis workflows needed to compare candidate improvements without losing human control.

The project is the renamed and narrowed successor to `awesome-llm-evolve` and this repository's earlier deep-research catalog work. It is now a local-first substrate for agentic codebase improvement.

## Goal

ClimbHill.ai helps coding agents run controlled, measurable, recursive self-improvement loops on a Git repository while preserving human control, repository safety, historical memory, and clear promotion paths.

The central thesis is simple: a codebase should learn from every attempted improvement, not only the patches that merge. Failed candidates still produce useful evidence about constraints, brittle tests, weak docs, bad hypotheses, missing policy, and repo areas that are difficult for agents to improve.

## Design Reference

ClimbHill.ai is aligned with Lilian Weng's ["Harness Engineering for Self-Improvement"](https://lilianweng.github.io/posts/2026-07-04-harness/) from July 4, 2026. The post frames a harness as the deployment system around a base model: workflow, tool use, context, persistent artifacts, permissions, and evaluation.

Key takeaways reflected in this repo:

- The harness is an optimization target, not just a prompt template.
- Long-horizon agent work needs durable file and database state instead of relying on transient chat context.
- Parallel candidate attempts should be explicit, inspectable, and recoverable through logs, patches, and status records.
- Context should be curated into structured memory over time, not appended endlessly.
- Self-improvement should use propose, evaluate, accept, and reject loops with regression checks and preserved failure records.
- Harness edits should remain bounded by policy, editable surfaces, passing behavior that must be preserved, and human-visible promotion gates.

## Boundary

ClimbHill.ai begins when a repository needs to be aligned for safe agentic improvement and ends when candidate improvements are evaluated, recorded, reported, and promoted into a pull request, issue, plan, or follow-up loop.

ClimbHill.ai is:

- A Codex plugin for distributing repo-improvement workflows.
- An MCP server that records runs, candidates, patches, evaluations, costs, decisions, and reports.
- A skill bundle under `.agents/skills` for recursive improvement workflows.
- A `/resources` convention for research, prior art, user guidance, postmortems, and reusable experiment learnings.
- A policy system for allowed, denied, and approval-required edits.
- A candidate-evolution system for parallel attempts, historical sampling, recombination, comparison, and promotion.
- A reporting and meta-analysis layer for humans to inspect progress, risk, failures, and next actions.

ClimbHill.ai is not a hosted agent cloud, a model-training framework, an automatic merge system, or a tool that silently modifies tests to make candidates pass.

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

The loop is designed around repo safety, durable memory, evaluation before promotion, human control, readable skills, and a small local MVP that can expand later.

## Components

| Component | Purpose |
|-----------|---------|
| Landing page | Static GitHub Pages site for `https://climbhill.ai/`. |
| Codex plugin | Packages workflows, MCP configuration, skills, policy templates, and install docs. |
| MCP server | Agent-facing runtime and system of record for runs, candidates, policy checks, evaluations, reports, and decisions. |
| CLI | Human-friendly commands such as `climbhill init`, `inspect`, `align`, `run`, `report`, and `reflect`. |
| Skills | Agent-readable procedures for alignment, historical sampling, candidate evolution, protected editing, reporting, and promotion. |
| Resources | Versioned context with provenance, trust level, tags, summary, and reason for inclusion. |
| Experiment registry | SQLite-backed durable state for goals, runs, candidates, evaluations, costs, decisions, reports, and issue proposals. |
| Policy layer | Conservative defaults for allowed edits, denied edits, approval-required paths, budgets, commands, and promotion gates. |

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
- `.agents/skills/` for repo-local skills.
- `resources/` for research, context, and promoted learnings.
- Known install, lint, typecheck, test, and build commands when applicable.

ClimbHill should inspect a target repo, identify missing alignment pieces, and propose or create them without overwriting existing files unless a human approves.

## Local CLI

```bash
# Create conservative alignment files and a local SQLite registry
python -m awesome_deep_research.cli init --repo /path/to/repo

# Inspect alignment status
python -m awesome_deep_research.cli inspect --repo /path/to/repo

# Classify paths against .climbhill/policy.yaml
python -m awesome_deep_research.cli policy check src/app.py tests/test_app.py .env --repo /path/to/repo

# Create a run, record evidence, compare candidates, and report
python -m awesome_deep_research.cli run --repo /path/to/repo --goal "Improve setup docs" --candidates 2
python -m awesome_deep_research.cli registry --repo /path/to/repo record-evaluation --candidate-id 1 --type test --status passed --command "pytest"
python -m awesome_deep_research.cli compare --repo /path/to/repo --run-id 1
python -m awesome_deep_research.cli decision --repo /path/to/repo --run-id 1 --candidate-id 1 --type promote --rationale "Best passing candidate"
python -m awesome_deep_research.cli report --repo /path/to/repo --run-id 1
python -m awesome_deep_research.cli reflect --repo /path/to/repo --run-id 1
```

The installed console script is `climbhill`; `adr` remains as a transitional compatibility alias.

## MCP Servers

The primary MCP server is ClimbHill-focused:

```bash
pip install "climbhill-ai[mcp]"
adr-mcp
```

It exposes tools for repo inspection, alignment, policy checks, resource search, run creation, candidate registration, evaluation recording, comparison, history sampling, report generation, decisions, costs, lineage, and issue proposals.

The upstream deep-research provider fan-out MCP implementation is preserved in `awesome_deep_research.deep_research_mcp_server` for compatibility with the earlier repository direction.

## GitHub Pages Deployment

This repo includes a zero-build landing page for `https://climbhill.ai/`:

- `index.html` - static landing page
- `assets/hero-research-harness.png` - hero artwork
- `CNAME` - custom domain declaration for `climbhill.ai`
- `.nojekyll` - disables Jekyll processing
- `.github/workflows/pages.yml` - deploys static files to GitHub Pages

Configure the repository name and Pages custom domain to match `climbhill.ai`.

## Legacy Deep-Research Assets

The upstream merge preserved the earlier deep-research skills, benchmark helpers, provider docs, audit tools, and OKF normalization assets under `.agents/skills/`, `skills/`, `benchmark/`, `docs/`, and `awesome_deep_research/`. They remain useful as research resources and compatibility tooling, but ClimbHill.ai is now the product direction.

Pricing and model availability change frequently. Use `skills/provider-source-index.md` and `python -m awesome_deep_research.source_refresh --check-links` before refreshing pricing or model guidance. The old provider tables used an "Under-$1 Benchmark Stance" column to keep live smoke tests bounded; keep that cost-control discipline when reusing those assets.

Run the offline repository and environment checks before spending API credits:

```bash
python -m awesome_deep_research.audit
python -m awesome_deep_research.op_env --template
python -m awesome_deep_research.source_refresh
```

## Status

The current repo includes the local MVP scaffolding: landing page, GitHub Pages config, plugin metadata, alignment templates, policy and eval templates, SQLite registry, CLI workflows, MCP tools, resource management, reports, and tests.
