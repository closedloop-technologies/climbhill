## Deep Research Skills Benchmark System

Comprehensive benchmarking framework for evaluating deep research skills across standardized taxonomy questions.

## Overview

This benchmark system:
- ✅ **Dynamically discovers** all skills in `.claude/skills/`
- ✅ **Extracts questions** from the research taxonomy document
- ✅ **Runs each skill** on each question category
- ✅ **Tracks metrics**: duration, cost, tokens, API calls
- ✅ **Saves detailed results** for analysis
- ✅ **Generates reports** in JSON and Markdown formats

## Quick Start

### Install Dependencies

```bash
pip install -r ../.claude/skills/test-requirements.txt
```

### Run Full Benchmark

```bash
python run_benchmark.py -v
```

### Run Specific Skills

```bash
python run_benchmark.py --skills exa-research tavily-search -v
```

### Run Specific Categories

```bash
python run_benchmark.py --categories "Source Retrieval" "Technical Decomposition" -v
```

### Limit Questions Per Category

```bash
python run_benchmark.py --max-questions 1 -v
```

## Command Line Options

```
usage: run_benchmark.py [-h] [--skills SKILLS [SKILLS ...]]
                        [--categories CATEGORIES [CATEGORIES ...]]
                        [--max-questions MAX_QUESTIONS]
                        [--output-dir OUTPUT_DIR] [-v]

options:
  -h, --help            show this help message and exit
  --skills SKILLS [SKILLS ...]
                        Specific skills to test (default: all)
  --categories CATEGORIES [CATEGORIES ...]
                        Specific categories to test (default: all)
  --max-questions MAX_QUESTIONS
                        Maximum questions per category (default: 3)
  --output-dir OUTPUT_DIR
                        Output directory for results
  -v, --verbose         Verbose output
```

## Output Structure

Results are saved in the following structure:

```
benchmark/results/
├── benchmark_summary.json          # Aggregated metrics across all runs
├── benchmark_report.md             # Human-readable report
├── exa-research/
│   ├── source_retrieval/
│   │   ├── q1_metrics.json
│   │   ├── q1_output.txt
│   │   ├── q2_metrics.json
│   │   ├── q2_output.txt
│   │   └── q3_metrics.json
│   │   └── q3_output.txt
│   └── technical_decomposition/
│       └── ...
├── gpt-researcher/
│   └── ...
└── ...
```

## Metrics Tracked

For each skill × question combination:

### Timing Metrics
- **Start time** (ISO timestamp)
- **End time** (ISO timestamp)
- **Duration** (seconds)

### Output Metrics
- **Output text** (full response)
- **Output length** (characters)
- **Success/failure** status
- **Error messages** (if any)

### Cost Metrics
- **Input tokens** (estimated)
- **Output tokens** (estimated)
- **Total tokens**
- **Estimated cost** (USD)

### Additional Metadata
- **Provider** (openai, anthropic, etc.)
- **Model** (gpt-4o, claude-3-5-sonnet, etc.)
- **API calls** (estimated)
- **Custom metadata** (skill-specific)

## Configuration

Edit `config.py` to customize:
- **Cost per token** rates for different models
- **Timeout** duration for skill execution
- **Excluded skills** (skills to skip)
- **Default models** and providers

## Taxonomy Categories

The benchmark covers 10 research categories from `docs/taxonomy-and-examples.md`:

1. **Source Retrieval** - Finding authoritative primary sources
2. **Cross-Validation** - Reconciling conflicting information
3. **Domain Mapping** - Identifying entities and relationships
4. **Technical Decomposition** - Breaking down complex systems
5. **Quantitative Synthesis** - Extracting and computing on data
6. **Regulatory / Standards Analysis** - Interpreting compliance requirements
7. **Scholarly Synthesis** - Surveying academic literature
8. **Bias & Uncertainty Assessment** - Identifying reliability issues
9. **Multi-Domain Integration** - Blending cross-disciplinary information
10. **Executive Summarization** - Producing decision-oriented outputs

Each category has 3 example questions.

## Example Usage

### Test a Single Skill on All Categories

```bash
python run_benchmark.py --skills tavily-search -v
```

### Quick Smoke Test (1 question per category)

```bash
python run_benchmark.py --max-questions 1 -v
```

### Test Specific Research Modes

```bash
python run_benchmark.py \
  --categories "Source Retrieval" "Cross-Validation" "Quantitative Synthesis" \
  --max-questions 2 \
  -v
```

## Analyzing Results

### View Summary Report

```bash
cat results/benchmark_report.md
```

### Parse JSON Metrics

```python
import json

with open('results/benchmark_summary.json') as f:
    data = json.load(f)

# Overall statistics
print(data['summary'])

# Per-skill performance
for skill, metrics in data['skills'].items():
    print(f"{skill}: {metrics['avg_duration']:.1f}s, ${metrics['total_cost']:.2f}")
```

### Compare Skills

```bash
# Extract cost per skill
jq '.skills | to_entries[] | "\(.key): $\(.value.total_cost)"' results/benchmark_summary.json

# Extract success rates
jq '.skills | to_entries[] | "\(.key): \(.value.successful)/\(.value.total_runs)"' results/benchmark_summary.json
```

## Scoring Rubric (Future)

After collecting benchmark data, we will implement a scoring rubric that evaluates:

### Speed (Objective)
- Average duration per question
- Consistency across question types

### Cost (Objective)
- Total cost per run
- Cost per token
- Cost efficiency ratio

### Quality (Multi-Dimensional)
- **Completeness**: Coverage of question requirements
- **Accuracy**: Factual correctness (human evaluation)
- **Relevance**: On-topic responses
- **Structure**: Organization and clarity
- **Citations**: Source quality and traceability
- **Depth**: Level of analysis provided

### Trade-Off Analysis
- Speed vs. Quality curve
- Cost vs. Quality curve
- Pareto frontier analysis

## Extending the Benchmark

### Add a New Skill

1. Place skill code in `.claude/skills/{skill-name}/scripts/`
2. Add `requirements.txt` with dependencies
3. Skill will be auto-discovered

### Add New Questions

Edit `docs/taxonomy-and-examples.md` following the existing format:

```markdown
### **X.Y Category Name**

* "Question 1"
* "Question 2"
* "Question 3"
```

### Custom Metrics

Extend `BenchmarkMetrics` in `tracker.py`:

```python
metrics.add_metadata("custom_metric", value)
```

## Troubleshooting

### Skill Times Out

Increase timeout in `config.py`:

```python
SKILL_TIMEOUT = 1200  # 20 minutes
```

### Missing Dependencies

Install all skill dependencies:

```bash
pip install -r ../.claude/skills/test-requirements.txt
```

### API Rate Limits

Add delays between runs by modifying `benchmark.py`:

```python
import time
# After each run
time.sleep(5)  # 5 second delay
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Benchmark Skills

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r .claude/skills/test-requirements.txt
      - name: Run benchmark
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
          # Add other API keys
        run: python benchmark/run_benchmark.py --max-questions 1
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark/results/
```

## License

Part of the ClimbHill.ai repository.
