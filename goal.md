# ClimbHill.ai Goal

## One-Sentence Goal

ClimbHill.ai helps coding agents run controlled, measurable, recursive self-improvement loops on a Git repository while preserving human control, repository safety, historical memory, and clear promotion paths.

## Product Boundary

ClimbHill.ai is a repo-local self-improvement system for software projects. It provides a Codex plugin, an MCP server, agent skills, resource conventions, policy gates, experiment tracking, reporting, and meta-analysis workflows so coding agents can repeatedly improve a codebase in bounded loops.

ClimbHill.ai begins when a repository needs to be aligned for safe agentic improvement and ends when candidate improvements are evaluated, recorded, reported, and promoted into a pull request, issue, plan, or follow-up loop.

## Problem

Modern coding agents can produce useful one-off patches, but most repositories are not structured for repeated self-improvement. Agents often lack:

- A clear repo goal and improvement boundary.
- A machine-readable understanding of allowed and forbidden edits.
- Durable memory of previous candidate attempts.
- A way to compare competing solutions.
- A way to combine promising ideas from prior runs.
- A way to persist experiment results outside the working tree.
- Human-in-the-loop gates for sensitive changes.
- Skills for running recursive improvement loops safely.

ClimbHill.ai solves this by turning a repository into a controlled improvement environment.

## Core Thesis

A codebase should learn from every attempted improvement, not only the patches that merge.

Each candidate attempt should produce code pointers, traces, costs, evaluations, failure reasons, decisions, and lessons. Future agents should be able to sample from that history, reuse promising ideas, avoid repeated mistakes, and propose better next steps.

## Success Criteria

ClimbHill.ai is successful when a user can:

1. Install the Codex plugin in an existing repo.
2. Run `climbhill init` or an equivalent agent workflow.
3. Produce or validate repo alignment files.
4. Define an improvement goal.
5. Run multiple candidate attempts.
6. Prevent agents from modifying protected files.
7. Persist every candidate with branch, commit, patch, evaluation, and cost metadata.
8. Compare candidates.
9. Generate a clear Markdown report.
10. Promote one candidate to a PR-ready branch or reject all candidates with reasons.
11. Run meta-analysis over the experiment tree.
12. Propose concrete GitHub issues from the meta-analysis.
