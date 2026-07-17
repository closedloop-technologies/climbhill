# Experiment Registry

The experiment registry stores durable state for improvement loops.

## MVP Backend

- SQLite database for structured records.
- Local file storage for patches, logs, reports, and exported artifacts.

## Entities

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
- Candidate lineage

## Candidate Fields

Candidates should record branch, base commit, head commit, patch path, summary, status, lineage, and promotion decision.

## Why It Exists

Experiment history should not be trapped inside transient chat logs. The registry lets future agents sample previous attempts, avoid repeated failures, and reuse partial wins.
