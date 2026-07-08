"""Metrics tracking for benchmark runs."""
import time
import json
import re
from typing import Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class BenchmarkMetrics:
    """Metrics for a single benchmark run."""
    skill_name: str
    category: str
    question: str
    
    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0
    
    # Output
    output: str = ""
    output_length: int = 0
    error: Optional[str] = None
    success: bool = False
    
    # Token usage (estimated from output)
    tokens_input: int = 0
    tokens_output: int = 0
    total_tokens: int = 0
    
    # Cost
    estimated_cost_usd: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Mark the start of execution."""
        self.start_time = time.time()
    
    def end(self) -> None:
        """Mark the end of execution and calculate duration."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
    
    def set_output(self, output: str) -> None:
        """Set the output and calculate metrics."""
        self.output = output
        self.output_length = len(output)
        self.success = True
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        self.tokens_output = len(output) // 4
        self.tokens_input = len(self.question) // 4
        self.total_tokens = self.tokens_input + self.tokens_output
    
    def set_error(self, error: str) -> None:
        """Set error information."""
        self.error = error
        self.success = False
    
    def calculate_cost(self, model: str, provider: str) -> None:
        """Calculate estimated cost based on token usage."""
        from .utils import estimate_cost
        self.estimated_cost_usd = estimate_cost(
            self.tokens_input,
            self.tokens_output,
            model,
            provider
        )

    def apply_actual_cost_if_present(self, output: str, error: str = "") -> None:
        """Use provider-reported cost when output includes a parseable USD amount."""
        actual_cost = self.extract_cost_from_output(output, error)
        if actual_cost is not None:
            self.estimated_cost_usd = actual_cost
            self.add_metadata("cost_source", "provider_output")
        else:
            self.add_metadata("cost_source", "token_estimate")
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata."""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Add formatted timestamps
        data['start_time_iso'] = datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None
        data['end_time_iso'] = datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @staticmethod
    def extract_api_calls_from_output(output: str) -> int:
        """
        Attempt to extract number of API calls from output.
        This is heuristic-based and may need adjustment per skill.
        """
        # Look for common patterns in debug output
        patterns = [
            r'API call[s]?:\s*(\d+)',
            r'(\d+)\s+API call[s]?',
            r'Made\s+(\d+)\s+request[s]?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Default: assume 1 API call if we got output
        return 1 if output else 0

    @staticmethod
    def extract_cost_from_output(output: str, error: str = "") -> Optional[float]:
        """Extract an actual USD cost if a skill prints one."""
        combined = output + "\n" + (error or "")
        patterns = [
            r'(?:total[_\s-]?cost|actual[_\s-]?cost|cost[_\s-]?usd|usd[_\s-]?cost)\s*[:=]\s*\$?([0-9]+(?:\.[0-9]+)?)',
            r'\bCost\s*:\s*\$([0-9]+(?:\.[0-9]+)?)',
            r'\$([0-9]+(?:\.[0-9]+)?)\s*(?:USD)?\s*(?:total|for this run|estimated)',
        ]

        for pattern in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    @staticmethod
    def extract_model_info(output: str, error: str = "") -> Dict[str, str]:
        """
        Attempt to extract model and provider information from output/error.
        """
        combined = (output + " " + (error or "")).lower()
        
        # Detect provider
        provider = "unknown"
        if "openai" in combined or "gpt" in combined:
            provider = "openai"
        elif "anthropic" in combined or "claude" in combined:
            provider = "anthropic"
        elif "exa" in combined:
            provider = "exa"
        elif "perplexity" in combined or "sonar" in combined:
            provider = "perplexity"
        elif "grok" in combined or "xai" in combined:
            provider = "xai"
        
        # Detect model
        model = "unknown"
        model_patterns = [
            r'(gpt-4[o]?(?:-mini)?(?:-deep-research)?)',
            r'(gpt-3\.5-turbo)',
            r'(o3-deep-research)',
            r'(o4-mini-deep-research)',
            r'(claude-[^\s]+)',
            r'(exa-research(?:-pro)?)',
            r'(sonar-[^\s]+)',
            r'(grok-[^\s]+)',
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, combined)
            if match:
                model = match.group(1)
                break
        
        return {"provider": provider, "model": model}


class BenchmarkTracker:
    """Track metrics across multiple benchmark runs."""
    
    def __init__(self):
        self.runs: list[BenchmarkMetrics] = []
        self.start_time = time.time()
    
    def create_run(self, skill_name: str, category: str, question: str) -> BenchmarkMetrics:
        """Create a new benchmark run."""
        metrics = BenchmarkMetrics(
            skill_name=skill_name,
            category=category,
            question=question
        )
        self.runs.append(metrics)
        return metrics
    
    def get_summary(self) -> Dict:
        """Get summary statistics across all runs."""
        if not self.runs:
            return {}
        
        successful_runs = [r for r in self.runs if r.success]
        failed_runs = [r for r in self.runs if not r.success]
        
        return {
            "total_runs": len(self.runs),
            "successful": len(successful_runs),
            "failed": len(failed_runs),
            "success_rate": len(successful_runs) / len(self.runs) if self.runs else 0,
            "total_duration": sum(r.duration_seconds for r in self.runs),
            "avg_duration": sum(r.duration_seconds for r in successful_runs) / len(successful_runs) if successful_runs else 0,
            "total_cost": sum(r.estimated_cost_usd for r in self.runs),
            "total_tokens": sum(r.total_tokens for r in self.runs),
            "avg_output_length": sum(r.output_length for r in successful_runs) / len(successful_runs) if successful_runs else 0,
        }
    
    def get_skill_summary(self, skill_name: str) -> Dict:
        """Get summary for a specific skill."""
        skill_runs = [r for r in self.runs if r.skill_name == skill_name]
        if not skill_runs:
            return {}
        
        successful = [r for r in skill_runs if r.success]
        
        return {
            "skill": skill_name,
            "total_runs": len(skill_runs),
            "successful": len(successful),
            "failed": len(skill_runs) - len(successful),
            "avg_duration": sum(r.duration_seconds for r in successful) / len(successful) if successful else 0,
            "total_cost": sum(r.estimated_cost_usd for r in skill_runs),
            "total_tokens": sum(r.total_tokens for r in skill_runs),
        }
    
    def get_category_summary(self, category: str) -> Dict:
        """Get summary for a specific question category."""
        category_runs = [r for r in self.runs if r.category == category]
        if not category_runs:
            return {}
        
        successful = [r for r in category_runs if r.success]
        
        return {
            "category": category,
            "total_runs": len(category_runs),
            "successful": len(successful),
            "avg_duration": sum(r.duration_seconds for r in successful) / len(successful) if successful else 0,
            "total_cost": sum(r.estimated_cost_usd for r in category_runs),
        }
    
    def to_dict(self) -> Dict:
        """Convert all tracked data to dictionary."""
        return {
            "summary": self.get_summary(),
            "runs": [r.to_dict() for r in self.runs],
            "skills": {
                skill: self.get_skill_summary(skill)
                for skill in set(r.skill_name for r in self.runs)
            },
            "categories": {
                cat: self.get_category_summary(cat)
                for cat in set(r.category for r in self.runs)
            },
        }
    
    def save_to_json(self, filepath: str) -> None:
        """Save all tracking data to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
