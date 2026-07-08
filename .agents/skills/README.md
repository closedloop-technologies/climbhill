# Codex Skills

This directory is the supported agent skill bundle for the repository. Skill
docs, runnable scripts, requirements, and tests live here and are registered in
`benchmark/utils.py`.

## Current Skills

- `deep-research-api-calls` - provider call patterns, API-key expectations,
  cost controls, and 1Password environment guidance.
- `deep-research-okf-normalize` - convert a deep research output into an Open
  Knowledge Format-style bundle.
- `deep-research-custom-data` - plan custom-source research across Google Docs,
  YouTube, local files, S3 buckets, arXiv papers, and similar corpora.
- Provider-specific call guides:
  - `deep-research-openai`
  - `deep-research-perplexity`
  - `deep-research-exa`
  - `deep-research-tavily`
  - `deep-research-jina`
  - `deep-research-xai-grok`
  - `deep-research-you`
  - `deep-research-gemini`
  - `deep-research-gpt-researcher`
  - `deep-research-langchain`
  - `deep-research-stanford-storm`
  - `deep-research-smolagents`

Provider skills include runnable scripts, requirements, and tests under this
tree so benchmark and fan-out commands use the supported agent skill paths.

## Adding a Skill

1. Add `.agents/skills/<skill-name>/SKILL.md`.
2. Add executable scripts under `.agents/skills/<skill-name>/scripts/` when the
   skill should run in the benchmark.
3. Add or confirm command wiring in `benchmark/utils.py`.
4. Add the tox environment to `tox.ini` when the skill has tests or runtime
   dependencies.
5. Keep benchmark prompts and runtime defaults below the documented `$1` per
   call budget.
