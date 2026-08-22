---
name: reasoning
description: Resolve important uncertainty with a small set of evidence-oriented reasoning primitives and reusable workflows. Use when a decision should be driven by research, experiments, observations, or explicit falsification rather than more unaided reasoning.
---

# Reasoning

Use this skill as the entrypoint for evidence-oriented reasoning in ClimbHill.
Keep the primitive set small. Prefer composing these primitives into workflows
rather than creating a new skill for every product or business technique.

## Core rule

Do not spend tokens answering a question that reality can answer cheaply.

Evidence updates the plan; it does not exist to vindicate the route already
chosen.

## Primitives

- [Experiment](experiment.md) - design the cheapest credible encounter with
  reality that can resolve an uncertain assumption.
- [Evidence](evidence.md) - interpret observations against a hypothesis or
  decision without defending the current plan.

Other existing skills remain complementary:

- `research` / deep-research skills: gather facts from external sources.
- `prototype`: make a concrete artifact when behavior or design is unclear.
- grilling / human-in-the-loop discussion: obtain judgment only the human can
  supply.
- domain modeling: sharpen concepts and language before deciding.
- task / execution skills: perform mechanical work needed to unblock learning.

## Choosing a primitive

Use **Experiment** when the unresolved question is empirical and a small action
can produce evidence. Examples: demand, willingness to pay, usability, runtime
behavior, benchmark performance, reliability, or whether a user will complete a
workflow.

Use **Evidence** when observations already exist but their implications are
unclear. Examples: experiment results, user interviews, benchmark output,
production telemetry, test results, incident logs, or sales outcomes.

Use research instead when the answer already exists in trustworthy sources. Use
a prototype when the main uncertainty is what a proposed interaction or design
should be like rather than whether a claim about reality is true.

## Workflows

Common compositions live in [`workflows/`](workflows/):

- [Discover](workflows/discover.md) - find the real job and current solution
  landscape, then identify opportunities.
- [Bet](workflows/bet.md) - generate a small number of genuinely different bets
  before converging.
- [Smoke Test](workflows/smoke-test.md) - test the promise before building the
  machinery.
- [Value Path](workflows/value-path.md) - shorten the path from first contact to
  realized value and test it cheaply.
- [Falsify](workflows/falsify.md) - actively try to kill an important assumption
  or the whole plan before investing further.

These are workflows, not additional primitives. They may call research,
prototype, Experiment, Evidence, domain modeling, implementation, and human
judgment as needed.

## Wayfinder relationship

Wayfinder determines **which uncertainty matters next**. Reasoning determines
**how to attack that uncertainty**. A workflow may resolve one Wayfinder ticket
or expose new tickets, but should not replace Wayfinder's map, frontier,
dependency, or scope semantics.
