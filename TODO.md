# Completed Implementation Checklist

This repo's original implementation checklist is complete. Keep this file as a
historical map to the shipped docs, skills, benchmark runner, and latest
aggregate report.

1. [x] Research all of the top deep research APIs and frameworks
2. [x] Create agent skill files for each of them
3. [x] Create a benchmark of cannonical deep research tasks based on [docs/taxonomy-and-examples.md](docs/taxonomy-and-examples.md)
   - Canonical task guide: [docs/benchmark-tasks.md](docs/benchmark-tasks.md)
   - Runner: [benchmark/live_smoke.py](benchmark/live_smoke.py)
4. [x] Create a script to run the benchmark across all of the deep research APIs and frameworks.
   - Benchmark runner: [benchmark/run_benchmark.py](benchmark/run_benchmark.py)
   - Parallel API fan-out: [scripts/run_api_fanout.py](scripts/run_api_fanout.py)
5. [x] Aggregate the results and create a report
   - Use the aggregated reports to bootstrap a rubric to evaluate them
   - Evaluate each of the APIs and frameworks based on the rubric
   - Create a final report that ranks the APIs and frameworks based on the rubric
   - Latest aggregate report: [research/2026-06-23-08-30-53-i62o/AGGREGATE_REPORT.md](research/2026-06-23-08-30-53-i62o/AGGREGATE_REPORT.md)

6. [x] Update with all of the models from https://huggingface.co/spaces/muset-ai/DeepResearch-Bench-Leaderboard
   - Model inventory: [docs/deepresearch-bench-leaderboard.md](docs/deepresearch-bench-leaderboard.md)
   - Source CSV snapshots: [research/2026-06-23-08-30-53-i62o](research/2026-06-23-08-30-53-i62o)
