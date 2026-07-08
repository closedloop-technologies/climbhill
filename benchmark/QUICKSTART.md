# Benchmark System Quick Start

## 1. Install Dependencies

```bash
# From repo root
pip install -r .agents/skills/test-requirements.txt
```

## 2. Set API Keys

Export required API keys for the skills you want to test:

```bash
export OPENAI_API_KEY="your-key"
export TAVILY_API_KEY="your-key"
export EXA_API_KEY="your-key"
export PERPLEXITY_API_KEY="your-key"
export XAI_API_KEY="your-key"
# ... etc
```

## 3. Run a Quick Test (Recommended First Step)

Test one skill with one question per category:

```bash
cd benchmark
python run_benchmark.py --skills deep-research-tavily --max-questions 1 -v
```

## 4. Run Full Benchmark

Test all skills with all questions (this will take a while and cost money):

```bash
python run_benchmark.py -v
```

## 5. View Results

```bash
# View summary report
cat results/benchmark_report.md

# Analyze performance
python analyze.py

# View quality scores
python scoring.py
```

## Common Commands

### Test specific skills
```bash
python run_benchmark.py --skills deep-research-exa deep-research-tavily deep-research-perplexity -v
```

### Test specific categories
```bash
python run_benchmark.py --categories "Source Retrieval" "Technical Decomposition" -v
```

### Quick smoke test
```bash
python run_benchmark.py --max-questions 1 -v
```

### Analyze by specific metric
```bash
python analyze.py --metric cost
python analyze.py --metric duration
python analyze.py --metric efficiency
```

## Expected Costs

Costs vary by skill and model used:
- **Quick test** (1 skill × 10 categories × 1 question): ~$0.50 - $2.00
- **Small test** (3 skills × 10 categories × 1 question): ~$1.50 - $6.00
- **Full benchmark** (10 skills × 10 categories × 3 questions): ~$15 - $60+

**Note**: Costs depend heavily on which models each skill uses. Skills using GPT-4 or Claude Opus will cost more than those using GPT-3.5 or smaller models.

## Troubleshooting

### "Timeout" errors
Increase timeout in `config.py`:
```python
SKILL_TIMEOUT = 1200  # 20 minutes
```

### "Missing API key" errors
Make sure you've exported the required API keys for the skills you're testing.

### "Module not found" errors
Install dependencies:
```bash
pip install -r ../.agents/skills/test-requirements.txt
```

## Next Steps

1. ✅ Run quick test to verify setup
2. ✅ Run full benchmark to collect data
3. ✅ Analyze results with analysis tools
4. 📊 Create custom visualizations
5. 🎯 Develop quality evaluation rubric
6. 📈 Track performance over time
