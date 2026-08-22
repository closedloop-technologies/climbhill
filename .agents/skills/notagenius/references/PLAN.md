# PLAN — Execute the Validation Playbook with ClimbHill

This adapter operationalizes `PLAYBOOK.md` with ClimbHill and the repository's
reasoning skills. `PLAYBOOK.md` is authoritative for the validation methodology;
this document defines execution, evidence, authority, and persistence semantics.

## Two state systems

Keep venture decisions distinct from ClimbHill controller actions:

```text
Venture decision: CONTINUE | REVISE | RETURN | STOP
ClimbHill action:  attempt | evaluate | promote | spawn_run | stop
```

A venture decision is domain evidence recorded in `DECISION.md`. A ClimbHill
Continuation Analysis makes one typed recommendation from a frozen Evidence
Snapshot. The recommendation grants no authority and performs no action.
Deterministic control then checks authorization, eligibility, freshness, scope,
and budget before atomic consumption and execution.

Typical mappings are contextual:

| Venture decision | Likely ClimbHill action |
| --- | --- |
| Continue the current investigation | `attempt` or `evaluate` |
| Revise within the current Focus | `attempt` |
| Return to an upstream artifact in the same Focus | `attempt` |
| Return through a different Focus or authority envelope | `spawn_run` |
| Accept an eligible artifact change | `promote` |
| Stop the venture or autonomous work | `stop` |

The table informs a recommendation; it is not executable policy.

## Persistence and terminology

Create venture artifacts under `ventures/<idea-slug>/`. `ARTIFACTS.md` is the
human-readable projection of product lineage. ClimbHill's canonical execution
records remain under `.climbhill/runs/<run-id>/`, where pinned baselines,
Attempts, Evaluations, Evidence Snapshots, Continuation Analyses, Decisions,
costs, and events retain their native semantics. Link the two systems with IDs;
do not duplicate or overwrite ClimbHill control state in venture Markdown.

In this plan, **JTBD** or **user job** means the progress sought by a user.
**ClimbHill Job** retains its engine meaning: optional UX metadata grouping
Runs and supplying defaults.

Every Run that changes venture state should record its input artifact IDs,
hypotheses examined, Evidence IDs produced, domain Decision IDs, output artifact
IDs, cost, and lineage. Example:

```text
Run R17
  input: hypothesis:H7
  experiment: E4
  produced: evidence:EV12, evidence:EV13
  domain decision: D6
  updated: economics-001
  next uncertainty: willingness to pay at the proposed unit
```

## Skill routing

Use `$reasoning` as the router. Its Discover, Bet, Smoke Test, Value Path, and
Falsify documents are workflows inside that skill; Experiment and Evidence are
its core primitives. Use `research`, `prototype`, `domain-modeling`, and
`grilling` when their information source matches the uncertainty.

Use `$business-soul` for service boundaries, accounts, customization, hosting,
pricing, trust, and go-to-market. Preserve an open, account-free workflow spine;
attach paid value to workload, workspace, warranty, or another genuine cost or
trust surface.

`wayfinder` and engineering routers are optional integrations, not package
dependencies. When available, Wayfinder may map a decision space larger than
one useful session. After M1, an engineering router may receive the justified
MVP and service definition.

## Initialize or resume

1. Write the raw idea to `ventures/<idea-slug>/IDEA.md` and initialize its
   stable ID in `ARTIFACTS.md`.
2. When resuming, inspect `ARTIFACTS.md`, the latest domain Decision, and the
   ClimbHill Run evidence needed to locate the current frontier. File presence
   alone does not establish board state.
3. Select the highest-consequence unresolved uncertainty whose prerequisites
   exist. Board order is a map, not authority.
4. Create or resume a bounded Run with an immutable baseline, one Focus, a
   pinned Evaluation Strategy, a Promotion Target, budgets, and an Authorization
   Envelope.
5. Work until the next evidence or authority gate. Continue automatically only
   within the existing envelope and user instruction.

## Board

### J1 — Discover JTBD

- Inputs: `IDEA.md`
- Playbook: Discover the Job
- Guidance: Reasoning Discover; optionally grilling, domain modeling, research,
  and Evidence
- Output: `JTBD.md`
- Gate: repeat J1 while the JTBD remains solution-shaped; otherwise consider J2

### J2 — Establish problem evidence

- Inputs: `IDEA.md`, `JTBD.md`
- Playbook: Establish problem evidence
- Guidance: research, Experiment, Evidence
- Output: `EVIDENCE.md`
- Domain decision: `CONTINUE -> B1`, `REVISE -> J1`, `STOP -> F1`

### B1 — Generate competing bets

- Inputs: `JTBD.md`, `EVIDENCE.md`, governing business principles
- Playbook: Map the opportunity; Generate competing bets
- Guidance: Reasoning Bet, grilling, Evidence, Business SOUL where applicable
- Output: `BETS.md`
- Gate: evidence must be capable of distinguishing the bets before E1

### E1 — Select a kill assumption

- Inputs: `BETS.md`, `EVIDENCE.md`
- Playbook: Select kill assumptions
- Guidance: Experiment and Evidence
- Output: `EXPERIMENTS/<id>/PLAN.md`
- Gate: hypothesis, competing explanation, thresholds, bounds, and implied
  Decisions are precommitted before E2

### E2 — Execute an experiment

- Input: `EXPERIMENTS/<id>/PLAN.md`
- Playbook: Smoke test the promise; Interpret evidence
- Guidance: Experiment; optionally prototype or research; then Evidence
- Outputs: `EXPERIMENTS/<id>/RESULTS.md`, updated `EVIDENCE.md` and
  `ARTIFACTS.md`
- Authority: execute only within approved cost, exposure, data, safety, and
  external-action bounds
- Gate: proceed to D1 when evidence can inform a Decision; otherwise recommend
  the smallest useful diagnostic or another bounded experiment

### D1 — Continue, revise, return, or stop

- Inputs: `JTBD.md`, `BETS.md`, `EVIDENCE.md`, relevant experiments
- Playbook: Choose, change, or kill the bet
- Guidance: Evidence
- Output: `DECISION.md`
- Domain transitions: `CONTINUE -> V1`, `REVISE -> B1`, `RETURN -> J1 or J2`,
  `STOP -> F1`
- Controller mapping: recommend `attempt`, `evaluate`, `spawn_run`, `promote`,
  or `stop` according to Focus and authority; do not encode the domain word as
  an untyped controller action

### V1 — Define the Value Path

- Inputs: `JTBD.md`, `DECISION.md`
- Playbook: Design the Value Path
- Guidance: Reasoning Value Path; optionally domain modeling, prototype, and
  grilling
- Output: `VALUE_PATH.md`
- Gate: the shortest credible path delivers the selected bet's promise

### S1 — Define the service

- Inputs: `JTBD.md`, `VALUE_PATH.md`, governing business principles
- Playbook: Define the service
- Guidance: Business SOUL
- Output: `SERVICE.md`
- Gate: meaningful local utility remains available without an artificial
  account or paywall; hosted, identity, persistence, collaboration,
  customization, workload, and trust surfaces are explicit
- Next: P1 and P2 may proceed as parallel investigations when authorized

### P1 — Test economics

- Inputs: `SERVICE.md`, `EVIDENCE.md`
- Playbook: Prove plausible economics
- Guidance: research, Experiment, Evidence
- Output: `ECONOMICS.md`
- Gate: dominant speculative assumptions return to E1; plausible sustainable
  economics may proceed to M1

### P2 — Prototype value delivery

- Inputs: `VALUE_PATH.md`, `SERVICE.md`
- Playbook: Prototype complete value delivery
- Guidance: prototype, Experiment, Evidence
- Outputs: experiment plan and results; update `VALUE_PATH.md`, `EVIDENCE.md`,
  and `ARTIFACTS.md` when required
- Domain transitions: success may proceed to M1; flow failure returns to V1;
  bet failure returns to B1; JTBD failure returns to J1

### M1 — Specify the minimum real service

- Inputs: `JTBD.md`, `VALUE_PATH.md`, `SERVICE.md`, `ECONOMICS.md`,
  `EVIDENCE.md`
- Playbook: Specify the minimum real service
- Output: `MVP.md`
- Gate: every significant implementation item traces to job completion,
  learning, paid value, trust/reliability, Evidence, or an explicit governing
  principle
- Handoff: an implementation workflow may now receive the evidence-justified
  service and MVP

### O1 — Evaluate real outcomes

- Inputs: `MVP.md`, `JTBD.md`, `VALUE_PATH.md`, `ECONOMICS.md`
- Playbook: Measure real outcomes
- Guidance: Experiment and Evidence
- Output: `OUTCOMES.md`
- Gate: route to F1 or the earliest invalidated upstream assumption

### F1 — Falsify and reassess

- Inputs: all relevant venture artifacts and ClimbHill evidence records
- Playbook: Falsify the whole business
- Guidance: Reasoning Falsify; research, Experiment, and Evidence as needed
- Output: `VALIDATION.md`
- Domain recommendation: exactly one of `DOUBLE DOWN`, `ITERATE`, `PIVOT`, or
  `STOP`
- Recursion: double down selects the next highest-value uncertainty; iterate
  returns to the earliest affected card; pivot returns to J1 or B1; stop ends
  the venture loop

## Continuation checkpoints

At each quiescent checkpoint:

```text
freeze typed evidence
-> run pinned Continuation Policy
-> record hypotheses, alternatives, and one typed recommendation
-> check authorization and execution eligibility
-> atomically consume the recommendation if permitted
-> execute or await a Decision
```

Prefer the authorized action expected to reduce the most consequential
uncertainty per unit of cost. Another card, a later card, or an upstream card may
be appropriate. A recommendation to widen Focus, authority, budget, tools, or
external exposure must stop at the corresponding Decision boundary.

## Success criterion

Success is not reaching the bottom of the board. It is repeatedly selecting and
resolving the uncertainty that most affects whether the service creates
valuable, profitable, principled user outcomes. The board is a map; evidence,
authority, and eligibility determine the route.
