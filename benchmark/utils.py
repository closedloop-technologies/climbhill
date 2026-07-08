"""Utility functions for benchmark system."""
import re
from typing import Dict, List

from .config import SKILLS_DIRS, TAXONOMY_FILE, EXCLUDED_SKILLS


PREFERRED_MAIN_SCRIPTS = {
    "deep-research-custom-data": "validate_manifest.py",
    "deep-research-okf-normalize": "normalize_to_okf.py",
}

SKILL_COMMAND_INFO = {
    "deep-research-exa": {
        "command": "python {script} search {question} --num-results 5 --highlights",
        "supports_query": True,
    },
    "deep-research-gpt-researcher": {
        "command": "python {script} --query {question}",
        "supports_query": True,
    },
    "deep-research-jina": {
        "command": "python {script} search {question}",
        "supports_query": True,
    },
    "deep-research-langchain": {
        "command": "python {script} --query {question}",
        "supports_query": True,
        "requires_server": True,
    },
    "deep-research-openai": {
        "command": "python {script} --prompt {question}",
        "supports_query": True,
    },
    "deep-research-perplexity": {
        "command": "python {script} --prompt {question} --model sonar --search-context-size low",
        "supports_query": True,
    },
    "deep-research-smolagents": {
        "command": "python {script} --task {question}",
        "supports_query": True,
    },
    "deep-research-stanford-storm": {
        "command": "python {script} --topic {question}",
        "supports_query": True,
    },
    "deep-research-tavily": {
        "command": "python {script} --query {question} --search-depth basic --max-results 5",
        "supports_query": True,
    },
    "deep-research-xai-grok": {
        "command": "python {script} --query {question}",
        "supports_query": True,
    },
    "deep-research-you": {
        "command": "python {script} --prompt {question} --research-effort lite",
        "supports_query": True,
    },
    "deep-research-gemini": {
        "command": "python {script} --prompt {question} --mode grounded --model gemini-3.5-flash",
        "supports_query": True,
    },
    "deep-research-custom-data": {
        "command": "python {script} docs/examples/custom-data-corpus.example.json",
        "supports_query": False,
    },
    "deep-research-okf-normalize": {
        "command": "python {script} --text {question} --title {question} --provider {skill_name} --bundle-dir \"{output_dir}/okf/{skill_name}/{category_slug}/{question_slug}\"",
        "supports_query": True,
    },
}


def discover_skills() -> List[Dict[str, str]]:
    """
    Dynamically discover all runnable skills in configured skill directories.
    
    Returns:
        List of skill dictionaries with name, script_path, and requirements
    """
    skills = []
    
    existing_roots = [skills_dir for skills_dir in SKILLS_DIRS if skills_dir.exists()]
    if not existing_roots:
        searched = ", ".join(str(skills_dir) for skills_dir in SKILLS_DIRS)
        raise FileNotFoundError(f"No skills directory found. Searched: {searched}")

    for skills_dir in existing_roots:
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_name = skill_dir.name

            # Skip excluded skills and test-related directories
            if skill_name in EXCLUDED_SKILLS or skill_name in ['tests', '__pycache__']:
                continue

            # Find the main script
            scripts_dir = skill_dir / "scripts"
            if not scripts_dir.exists():
                continue

            # Look for Python scripts
            python_files = list(scripts_dir.glob("*.py"))
            if not python_files:
                continue

            preferred_script = PREFERRED_MAIN_SCRIPTS.get(skill_name)
            if preferred_script and (scripts_dir / preferred_script).exists():
                main_script = scripts_dir / preferred_script
            else:
                main_script = sorted(python_files)[0]

            # Check for requirements
            requirements_file = skill_dir / "requirements.txt"
            requirements = []
            if requirements_file.exists():
                requirements = requirements_file.read_text().strip().split('\n')
                requirements = [
                    r.strip()
                    for r in requirements
                    if r.strip() and not r.startswith('#')
                ]

            skills.append({
                "name": skill_name,
                "script_path": str(main_script),
                "requirements": requirements,
                "skill_dir": str(skill_dir),
                "skills_root": str(skills_dir),
            })
    
    return sorted(skills, key=lambda x: x['name'])


def parse_taxonomy_questions() -> Dict[str, List[str]]:
    """
    Parse the taxonomy document and extract example questions by category.
    
    Returns:
        Dictionary mapping category names to lists of questions
    """
    if not TAXONOMY_FILE.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {TAXONOMY_FILE}")
    
    content = TAXONOMY_FILE.read_text()
    
    categories = {}
    current_category = None
    
    # Pattern to match category headers like "### **3.1 Source Retrieval**"
    category_pattern = re.compile(r'###\s+\*\*\d+\.\d+\s+(.+?)\*\*')
    
    # Pattern to match questions (bullet points starting with *, handles both straight and curly quotes)
    # Matches: * "question" or * "question" (with curly quotes U+201C and U+201D)
    question_pattern = re.compile(r'^\*\s+["\u201C](.+?)["\u201D]', re.MULTILINE)
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Check if this is a category header
        category_match = category_pattern.match(line.strip())
        if category_match:
            current_category = category_match.group(1).strip()
            categories[current_category] = []
            continue
        
        # Check if this is a question
        if current_category:
            question_match = question_pattern.match(line.strip())
            if question_match:
                question = question_match.group(1).strip()
                categories[current_category].append(question)
    
    # Filter out empty categories
    categories = {k: v for k, v in categories.items() if v}
    
    return categories


def get_skill_command_info(skill_name: str) -> Dict[str, str]:
    """
    Get the command-line interface information for a specific skill.
    
    Returns:
        Dictionary with command template and parameter mappings
    """
    if skill_name not in SKILL_COMMAND_INFO:
        raise KeyError(f"No benchmark command registered for skill: {skill_name}")
    return SKILL_COMMAND_INFO[skill_name]


def find_unregistered_benchmark_skills() -> List[str]:
    """Return discovered runnable skills that lack explicit benchmark commands."""
    discovered = {skill["name"] for skill in discover_skills()}
    return sorted(discovered - set(SKILL_COMMAND_INFO))


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """
    Convert text to a safe filename.
    
    Args:
        text: Input text
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename string
    """
    # Remove or replace invalid characters
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    text = text.strip('_')
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.lower()


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 30.5s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.1f}s"
    
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m {remaining_seconds:.0f}s"


def estimate_cost(tokens_input: int, tokens_output: int, model: str, provider: str) -> float:
    """
    Estimate cost based on token usage.
    
    Args:
        tokens_input: Number of input tokens
        tokens_output: Number of output tokens
        model: Model name
        provider: Provider name (openai, anthropic, etc.)
        
    Returns:
        Estimated cost in USD
    """
    from .config import COST_PER_1K_TOKENS, DEFAULT_COST_PER_1K
    
    # Get pricing for provider and model
    if provider in COST_PER_1K_TOKENS and model in COST_PER_1K_TOKENS[provider]:
        pricing = COST_PER_1K_TOKENS[provider][model]
    else:
        pricing = DEFAULT_COST_PER_1K
    
    input_cost = (tokens_input / 1000) * pricing["input"]
    output_cost = (tokens_output / 1000) * pricing["output"]
    
    return input_cost + output_cost
