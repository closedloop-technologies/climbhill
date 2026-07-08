# Under-$1 Deep Research Benchmark Tasks

The benchmark should exercise real deep-research behavior while keeping each
provider call below `$1` in expected cost. Prefer `--max-questions 1` smoke runs
when adding a provider, then broaden only after cost metadata is captured.

## Canonical Tasks

| Task ID | Prompt | Success Criteria | Cost Guard |
| --- | --- | --- | --- |
| `meta-deepresearchers` | Deepresearch the deepresearchers: identify current deep research APIs, open-source frameworks, cost controls, and citation behavior. | Names providers, distinguishes API vs UI, cites primary or official sources, reports uncertainty. | cap source count/search count; short report |
| `ai-for-science` | Compare current AI-for-science research agents or systems and identify where they are actually useful. | Uses scholarly or official sources, distinguishes demos from validated systems, captures limitations. | cap output tokens; max 5-8 sources |
| `standards-trace` | Find the current source of truth for one technical standard and summarize its latest revision status. | Finds authoritative standards body pages, reports exact revision identifier/date, flags access limits. | no broad web sweep; stop after authoritative source |
| `provider-cost-check` | For one named provider, find pricing controls that keep a deep research call under `$1`. | Cites official pricing/docs when available, computes a conservative budget, names unknowns. | one provider per run |

## Required Result Artifacts

Each completed benchmark call should keep:

- raw provider output;
- run metadata with duration and estimated or actual cost;
- normalized OKF bundle;
- source/citation list;
- uncertainty register.

The benchmark runner automatically creates OKF bundles for successful runs under
`benchmark/results/okf/<skill>/<category>/qN_<prompt_slug>/` and records
`okf_bundle_dir` plus `okf_valid` in the run metrics.
