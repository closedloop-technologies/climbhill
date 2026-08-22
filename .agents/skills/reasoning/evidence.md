# Evidence

Interpret observations against a hypothesis or decision without trying to defend
the current plan.

## Rule

Evidence updates the plan; it does not exist to vindicate the route already
chosen.

## Use when

Use Evidence when observations already exist but their implications are unclear:
experiment results, benchmarks, interviews, analytics, test output, incident
logs, production telemetry, sales outcomes, or measurements from physical
systems.

## Procedure

1. Restate the decision or hypothesis being evaluated.
2. List observations separately from interpretation.
3. Identify which observations support the hypothesis.
4. Identify which observations contradict it.
5. Look for confounders, selection effects, measurement error, missing data, and
   credible alternative explanations.
6. Compare the result with any decision rule or threshold set before evidence
   was collected.
7. Conclude only **supported**, **contradicted**, or **unresolved** at the level
   justified by the evidence.
8. State what changed in the current belief or plan.
9. Name the highest-value remaining uncertainty and whether it calls for
   research, another experiment, human judgment, or a decision.

## Output shape

```markdown
## Question
<decision or hypothesis>

## Observations
- <raw observation>

## Supporting evidence
- <evidence and why it bears on the question>

## Contradicting evidence
- <evidence and why it bears on the question>

## Confounders and alternatives
- <credible alternative explanation or limitation>

## Conclusion
supported | contradicted | unresolved

## Update
<what should change because of this evidence>

## Remaining uncertainty
<what matters next>
```

Do not turn `unresolved` into a weak version of `supported`. Lack of contradictory
evidence is not confirmation, and noisy evidence should remain noisy.
