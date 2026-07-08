# Environment Variables Setup Guide

Quick reference for setting up API keys for all deep research skills.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys**

3. **Verify your setup:**
   ```bash
   # Check which keys are set
   grep -v '^#' .env | grep -v '^$' | cut -d'=' -f1
   ```

## Required API Keys by Skill

### Minimal Setup (2-3 keys for most skills)

For a quick start, get these first:

```bash
OPENAI_API_KEY=sk-...        # Most commonly used
TAVILY_API_KEY=tvly-...      # Used by multiple skills
```

### Complete Setup

| Skill | Required Keys | Optional Keys |
|-------|--------------|---------------|
| **deep-research-exa** | `EXA_API_KEY` | - |
| **deep-research-gpt-researcher** | `TAVILY_API_KEY`, `OPENAI_API_KEY` | - |
| **deep-research-jina** | - | `JINA_API_KEY` |
| **deep-research-langchain** | `TAVILY_API_KEY`, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` | - |
| **deep-research-openai** | `OPENAI_API_KEY` | - |
| **deep-research-perplexity** | `PERPLEXITY_API_KEY` | - |
| **deep-research-smolagents** | `HF_TOKEN` or `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` | - |
| **deep-research-stanford-storm** | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, `BING_SEARCH_API_KEY` or `YDC_API_KEY` | - |
| **deep-research-tavily** | `TAVILY_API_KEY` | - |
| **deep-research-xai-grok** | `XAI_API_KEY` | - |

## Getting API Keys

### LLM Providers

- **OpenAI**: https://platform.openai.com/api-keys
  - Free trial credit, then pay-as-you-go
  - GPT-4: ~$0.03-0.12 per 1K tokens

- **Anthropic**: https://console.anthropic.com/settings/keys
  - Free trial credit, then pay-as-you-go
  - Claude: ~$0.015-0.075 per 1K tokens

- **Hugging Face**: https://huggingface.co/settings/tokens
  - Free tier available
  - Pro: $9/month for more usage

### Search Providers

- **Tavily**: https://tavily.com/
  - Research-focused search API
  - Free tier: 1,000 searches/month
  - Pro: $20/month for 10K searches

- **Exa**: https://exa.ai/
  - Neural search engine
  - Free tier available
  - Pay-as-you-go pricing

- **Perplexity**: https://www.perplexity.ai/settings/api
  - AI-powered search
  - Pay-per-request pricing

- **xAI (Grok)**: https://console.x.ai/
  - Access to Grok models
  - Beta access required

- **Jina AI**: https://jina.ai/
  - Reader and search APIs
  - Free tier with rate limits

- **Bing Search**: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
  - Free tier: 1,000 calls/month
  - Paid tiers available

- **You.com**: https://api.you.com/
  - Search API
  - Contact for access

## Testing Your Setup

### Test Individual Skills

```bash
# Test Tavily
cd .agents/skills/deep-research-tavily
python scripts/tavily_search.py --query "test"

# Test OpenAI Deep Research
cd ../deep-research-openai
python scripts/run_deep_research.py --prompt "test query"

# Test Exa
cd ../deep-research-exa
python scripts/exa_tools.py search "test"
```

### Run System Test

```bash
cd benchmark
python test_system.py
```

### Quick Benchmark

```bash
# Test one skill with minimal questions
python run_benchmark.py --skills deep-research-tavily --max-questions 1 -v
```

## Cost Management

### Free Tier Options

Skills that can work with free tiers:
- **deep-research-jina**: Works without API key (rate limited)
- **deep-research-smolagents**: Can use HuggingFace free tier
- **deep-research-tavily**: 1,000 free searches/month

### Budget-Friendly Combinations

For testing on a budget (~$5-10):
1. Use `HF_TOKEN` with deep-research-smolagents (free tier)
2. Use `TAVILY_API_KEY` (free tier)
3. Use `OPENAI_API_KEY` with GPT-3.5-turbo (cheaper)

### Full Production Setup

For comprehensive testing (~$50-100):
- All OpenAI models (including GPT-4)
- Multiple search providers
- Premium features

## Environment Variable Priority

Some skills support multiple providers. They check in this order:

**LLM Selection:**
1. `OPENAI_API_KEY` (most common)
2. `ANTHROPIC_API_KEY` (alternative)
3. `HF_TOKEN` (fallback for deep-research-smolagents)

**Search Selection:**
1. `TAVILY_API_KEY` (recommended for research)
2. `BING_SEARCH_API_KEY` (for STORM)
3. `YDC_API_KEY` (You.com alternative)

## Security Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`

2. **Use environment-specific files**
   - `.env.local` for local development
   - `.env.production` for production (if applicable)

3. **Rotate keys regularly**
   - Especially if exposed or shared

4. **Use minimum required permissions**
   - API keys should have minimal scopes

5. **Monitor usage**
   - Set up billing alerts
   - Track API usage

## Troubleshooting

### "API key not set" errors

```bash
# Check if key is in .env
grep "OPENAI_API_KEY" .env

# Check if .env is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### "Rate limit exceeded" errors

- Wait before retrying
- Upgrade to paid tier
- Use alternative provider

### "Invalid API key" errors

- Verify key is correct (copy-paste errors)
- Check if key has been revoked
- Ensure no extra spaces in `.env`

## Example .env File

```bash
# LLM Providers
OPENAI_API_KEY=sk-proj-abc123...
ANTHROPIC_API_KEY=sk-ant-api03-xyz789...
HF_TOKEN=hf_abc123...

# Search Providers
TAVILY_API_KEY=tvly-abc123...
EXA_API_KEY=exa_abc123...
PERPLEXITY_API_KEY=pplx-abc123...

# Additional
XAI_API_KEY=xai-abc123...
JINA_API_KEY=jina_abc123...
BING_SEARCH_API_KEY=abc123...
```

## Next Steps

After setting up your environment:

1. ✅ Test with `python benchmark/test_system.py`
2. ✅ Run a quick benchmark on one skill
3. ✅ Review cost estimates in `benchmark/SUMMARY.md`
4. ✅ Run full benchmark when ready
5. ✅ Analyze results with `python benchmark/analyze.py`

## Additional Resources

- [Benchmark System README](benchmark/README.md)
- [Benchmark Quick Start](benchmark/QUICKSTART.md)
- [Complete System Summary](benchmark/SUMMARY.md)
- [Skills Documentation](.agents/skills/*/SKILL.md)
