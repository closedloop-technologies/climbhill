# Idea to Validated Service Playbook

This domain-agnostic playbook turns a raw product or service idea into an
evidence-backed service that helps a real user complete a meaningful Job To Be
Done, wins against available alternatives, can become economically sustainable,
and preserves the organization's governing principles.

It is an uncertainty-reduction process, not a software-development process:

```text
IDEA -> JOB -> CLAIMS -> EVIDENCE -> BET -> EXPERIMENT -> DECISION
     -> VALUE DELIVERY -> ECONOMICS -> REAL USAGE -> REASSESS -> ...
```

At every gate choose `CONTINUE`, `REVISE`, `RETURN`, or `STOP`. `RETURN` names
the earlier assumption or artifact invalidated by new evidence. Stopping early
is successful when evidence does not justify the next investment.

## Operating principles

### Reduce uncertainty, not phases

Work is complete when it consumes known inputs, addresses an explicit
uncertainty, produces a durable artifact with supporting evidence, and makes
the next decision clearer. More documents, features, code, and completed cards
are not progress by themselves.

### Work backward from the idea

The initial idea is a candidate solution and evidence about its creator's
intuition. Work backward to the person, situation, progress sought,
alternatives, deficiencies, and behavior that would show a better solution
matters. Seek evidence capable of killing or substantially changing the idea.

### Match evidence to consequence

Use this as a rough ordering, not a numerical score:

```text
Opinion
-> stated preference
-> stated intent
-> click
-> signup
-> meeting booked
-> access, data, or workflow commitment
-> repeated use
-> payment
-> retention
-> expansion
```

Cheap reversible decisions can use weaker evidence. Major irreversible
investments require stronger evidence.

### Preserve epistemic status

For every consequential claim distinguish:

- `OBSERVATION`: what directly happened or was measured;
- `INFERENCE`: the current interpretation;
- `ASSUMPTION`: what is treated as true without adequate evidence; and
- `CONTRADICTORY EVIDENCE`: what supports another explanation.

Never silently promote an inference into a fact.

## Workspace and lineage

Use a compact workspace and create artifacts lazily:

```text
ventures/<idea-slug>/
├── IDEA.md
├── JTBD.md
├── EVIDENCE.md
├── BETS.md
├── EXPERIMENTS/
├── DECISION.md
├── VALUE_PATH.md
├── SERVICE.md
├── ECONOMICS.md
├── MVP.md
├── OUTCOMES.md
├── VALIDATION.md
└── ARTIFACTS.md
```

Experiment directories may contain `PLAN.md`, `ASSETS.md` when distinct assets
exist, and `RESULTS.md`. Empty files do not count as progress.

Every durable artifact carries stable metadata:

```yaml
---
artifact_id: jtbd-001
artifact_type: jtbd
status: hypothesis
parents: [idea-001]
evidence_refs: [EV1]
decision_refs: []
created_by: discover-job
---
```

Use stable identifiers such as `H3`, `E7`, `EV12`, and `D4`, always paired with
a label. `ARTIFACTS.md` is the human-readable provenance graph and should answer
why a feature exists, why a price exists, what caused a decision, and which
assumptions remain unresolved.

## A. Discover the Job

Work backward from the proposed solution. Determine the job performer, buyer,
triggering situation, desired progress, functional/emotional/social dimensions,
quality criteria, current alternatives, workarounds, switching forces, and
constraints. Generate competing job formulations before converging.

Canonical form:

> **When** [situation], **I want to** [make progress], **so I can** [outcome].

Output `JTBD.md`. Continue only when the job can be stated without mentioning
the proposed product.

## B. Establish problem evidence

Seek concrete past behavior, recurring triggers, workarounds, spending, failed
attempts, complaints, tool use, switching, and evidence against the job. Ask
what happened last time rather than whether someone might use the idea.

Represent consequential claims in `EVIDENCE.md`:

```text
Hypothesis ID:
Claim:
Evidence for:
Evidence against:
Confidence:
What would change our mind:
```

Choose `CONTINUE`, `REVISE` the JTBD, or `STOP`.

## C. Map the opportunity

Connect jobs to desired outcomes, current approaches, deficiencies, and
possible wedges. Identify table stakes, under-served outcomes, over-served
outcomes, active search behavior, and features with no clear job. A feature gap
matters only when it corresponds to important progress or an outcome.

Record the opportunity map in `JTBD.md` or `BETS.md`; create another artifact
only when it represents a distinct durable concept.

## D. Generate competing bets

Generate roughly three materially different service hypotheses. They should
differ in mechanism or business model, not feature arrangement. For each record
the user, promise, mechanism, alternative displaced, reason to switch, wedge,
acquisition, pricing, free value, paid value, critical assumptions, and kill
conditions.

Output `BETS.md`. Continue only when evidence could favor one bet while killing
another.

## E. Select kill assumptions

Rank assumptions by consequence times uncertainty. Test the assumption most
capable of changing the investment decision, not merely the easiest one.
Precommit the hypothesis, null or competing explanation, required evidence,
success and failure thresholds, unresolved outcome, budget, time limit,
authorization bounds, and decision implied by each result.

Output `EXPERIMENTS/<experiment-id>/PLAN.md`.

## F. Smoke test the promise

Expose the promise before building its machinery. Suitable experiments include
landing pages, fake doors, outbound offers, waitlists, pricing tests, preorders,
concierge delivery, and Wizard-of-Oz experiences. Prefer costly behavior over
compliments.

The experiment succeeds as a learning mechanism when its evidence changes a
decision. Record raw observations in `RESULTS.md`.

## G. Interpret evidence

Classify the exact hypothesis as `SUPPORTED`, `CONTRADICTED`, or `UNRESOLVED`.
Evaluate confounders, selection effects, alternative explanations, sample
limits, novelty effects, and instrumentation failure. Preserve the precommitted
threshold and update `EVIDENCE.md`; do not rationalize a weak result.

## H. Choose, change, or kill the bet

Choose `CONTINUE`, `REVISE`, `RETURN`, or `STOP`. Write `DECISION.md` with the
selected bet, alternatives rejected, decisive Evidence IDs, unresolved risks,
decision-maker, and next uncertainty. Ask whether the same decision would be
made if the idea belonged to someone else.

## I. Design the Value Path

Map the shortest credible path from trigger to completed job. For each step
record user action, system action, state transition, dependency, trust
requirement, failure state, and reason the step exists. Identify trigger, entry
state, first value, full value, job completion, and repeat trigger. Delete,
combine, defer, automate, or manually fulfill steps aggressively.

Output `VALUE_PATH.md`.

## J. Define the service

Separate user value from implementation machinery. Determine the minimum
service capable of delivering the Value Path and classify capabilities as
local, hosted, account-bound, customizable, automated, manual, free, or paid.
Apply the organization's governing product and business principles explicitly.

Output `SERVICE.md`.

## K. Prove plausible economics

Model the buyer, pricing unit, price, free utility, paid value, compute, storage,
human effort, support, gross margin, acquisition path, CAC, activation,
retention, expansion, and break-even. Separate measurements from assumptions.
Identify the few assumptions that dominate the result and turn them into
experiments instead of adding imaginary precision.

Output `ECONOMICS.md`.

## L. Prototype complete value delivery

Create the cheapest believable end-to-end experience. Use fake data, mocked
integrations, manual fulfillment, hidden human operations, or clickable
interfaces when the hidden machinery is not the uncertainty. Observe
comprehension, completion, hesitation, trust failures, perceived value, and
willingness to repeat. Update upstream artifacts when evidence demands it.

## M. Specify the minimum real service

Replace temporary machinery only where repeated delivery requires it. Every
implementation item must trace to `JOB COMPLETION`, `LEARNING`, `PAID VALUE`,
or `TRUST / RELIABILITY`. Mark each item `REAL NOW`, `MANUAL FOR NOW`, `MOCKED
FOR NOW`, or `DEFERRED`.

Output `MVP.md` and hand it to the appropriate implementation workflow.

## N. Measure real outcomes

Instrument only behavior that answers a decision question: trigger,
acquisition, activation, first value, job completion, time to value, repeat
job, retention, payment, expansion, abandonment, failure, support burden, and
cost per completed job. Record each metric's definition, population, method,
window, source, threshold, and decision informed.

Output `OUTCOMES.md`.

## O. Falsify the whole business

Assume the business should not continue. Build the strongest evidence-based
case that the job is weak, alternatives are adequate, switching will not occur,
value is insufficient, acquisition or retention is uneconomic, willingness to
pay is low, delivery cost is excessive, or governing principles are violated.
Classify each proposition and recommend exactly one of `DOUBLE DOWN`, `ITERATE`,
`PIVOT`, or `STOP`.

Output `VALIDATION.md`. Ask whether evidence justifies the next week and next
dollar.

## Recursive transitions

Route to the earliest assumption invalidated by new evidence:

```text
VALIDATION -> JTBD       misunderstood job
OUTCOMES -> VALUE_PATH   users start but fail to realize value
ECONOMICS -> EXPERIMENT  a dominant economic assumption is speculative
EXPERIMENT -> BETS       evidence killed the current bets
PROTOTYPE -> VALUE_PATH  observed behavior exposed unnecessary steps
OUTCOMES -> SERVICE      value is real but delivery is uneconomic
```

Going backward because of evidence is progress.

## Increasing confidence

A business is not validated at one moment. Confidence grows only as evidence
supports the chain from plausible job, to repeated occurrence, dissatisfaction
with alternatives, behavior-changing promise, realized value, repeat use,
payment, sustainable delivery economics, and scale that preserves governing
principles. Every unsupported arrow remains a hypothesis.
