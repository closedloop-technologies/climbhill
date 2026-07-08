"""Configuration for benchmark system."""
import os
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
SKILLS_DIRS = [SKILLS_DIR]
TAXONOMY_FILE = REPO_ROOT / "docs" / "taxonomy-and-examples.md"
RESULTS_DIR = REPO_ROOT / "benchmark" / "results"

# Cost per token (approximate, update based on actual pricing)
# These are rough estimates - actual costs vary by provider and model
COST_PER_1K_TOKENS = {
    "openai": {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "o3-deep-research": {"input": 0.01, "output": 0.04},  # Estimated
        "o4-mini-deep-research": {"input": 0.001, "output": 0.004},  # Estimated
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
    },
    "exa": {
        "exa-research": {"input": 0.01, "output": 0.02},  # Estimated
        "exa-research-pro": {"input": 0.02, "output": 0.04},  # Estimated
    },
    "perplexity": {
        "sonar-small-online": {"input": 0.0002, "output": 0.0002},
        "sonar-medium-online": {"input": 0.0006, "output": 0.0006},
        "sonar-large-online": {"input": 0.001, "output": 0.001},
    },
    "xai": {
        "grok-4": {"input": 0.01, "output": 0.03},  # Estimated
        "grok-4.1-fast-reasoning": {"input": 0.005, "output": 0.015},  # Estimated
    },
}

# Default cost for unknown models
DEFAULT_COST_PER_1K = {"input": 0.001, "output": 0.003}

# Timeout for each skill run (seconds)
SKILL_TIMEOUT = 600  # 10 minutes

# Maximum expected or estimated cost for a single benchmark call.
MAX_BENCHMARK_COST_USD = 1.00

# Skills to exclude from benchmarking (if needed)
EXCLUDED_SKILLS = []
