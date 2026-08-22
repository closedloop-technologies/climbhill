# Self-Improvement Papers for ClimbHill

This directory is a durable reading corpus for the research that most directly informs ClimbHill's recursive improvement loop, evaluation contract, promotion boundaries, graph repair, and multi-agent governance.

The checked-in Markdown files are **reference notes**, not verbatim full-text conversions. The source PDFs have mixed redistribution licenses, so `download-pdfs.sh` downloads canonical arXiv snapshots into a local, git-ignored `pdfs/` directory.

Related ClimbHill reasoning primitives: [`../../../.agents/skills/reasoning/SKILL.md`](../../../.agents/skills/reasoning/SKILL.md).

## Read first: the three-paper foundation

1. **[On the Fragility of Self-Improving Agents](notes/2608.18066-fragility.md)** — defines what should count as evidence that an optimizer actually improved.
2. **[ENPIRE](notes/2606.19980-enpire.md)** — provides a concrete reset → execute → verify → diagnose → modify → rerun experimental loop.
3. **[Zetta](notes/2608.16590-zetta.md)** — separates runtime recovery, rollout-level diagnosis, and validation-gated promotion across different timescales.

## Essential reading

- [On the Fragility of Self-Improving Agents: Variance, Task Order, and Underspecification](notes/2608.18066-fragility.md) — arXiv:2608.18066
- [ENPIRE: Agentic Robot Policy Self-Improvement in the Real World](notes/2606.19980-enpire.md) — arXiv:2606.19980
- [Zetta ζ: An Efficient Closed-Loop Embodied Harness for Self-Evolving Physical Intelligence](notes/2608.16590-zetta.md) — arXiv:2608.16590
- [Recursive Self-Improvement in AI: From Bounded Self-Refinement to Autonomous Research Loops](notes/2607.07663-recursive-self-improvement.md) — arXiv:2607.07663

## Architecture-defining follow-ups

- [HarnessEval-W: Agentifying the Evaluation of Visual Worlds](notes/2608.16859-harnesseval-w.md) — arXiv:2608.16859
- [TRUSS: Towards Task-Reliable and User-Safe Automated Agent Skill Generation](notes/2608.17588-truss.md) — arXiv:2608.17588
- [Atomic Task Graph: A Unified Framework for Agentic Planning and Execution](notes/2607.01942-atomic-task-graph.md) — arXiv:2607.01942
- [Don't Drop the BATON: Long-Horizon Robot Manipulation via Agentic Subtask Exploration and Transition-aware Memory](notes/2608.16889-baton.md) — arXiv:2608.16889

## Important for multi-agent ClimbHill

- [Governance at the Boundary: How Agent Decomposition Degrades Policy Compliance](notes/2608.16055-governance-boundary.md) — arXiv:2608.16055
- [CompoSkill: Compositional Skill Chain Attacks from Individually Scanner-Passing LLM Agent Skills](notes/2608.16246-composkill.md) — arXiv:2608.16246
- [Skill2Query: Exploiting Skill Structure to Generate Pseudo-Queries for Agent Skill Retrieval](notes/2608.16071-skill2query.md) — arXiv:2608.16071

## Local PDFs

Download the canonical arXiv PDFs:

```bash
bash resources/papers/self-improvement/download-pdfs.sh
```

The script writes into `resources/papers/self-improvement/pdfs/`, which is intentionally ignored by Git.

## Corpus principles

- Pin an exact paper identifier/version when a Run relies on research.
- Keep source evidence separate from ClimbHill interpretations.
- Treat negative results and evaluation methodology as first-class design inputs.
- Prefer evidence that exposes variance, confounders, transitions, authority boundaries, and composition effects.
- Revisit this corpus as the recursive-improvement literature changes quickly.
