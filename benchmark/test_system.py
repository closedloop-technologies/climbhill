#!/usr/bin/env python3
"""Test that the benchmark system is set up correctly."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.utils import discover_skills, parse_taxonomy_questions
from benchmark.config import SKILLS_DIR, TAXONOMY_FILE


def test_discovery():
    """Test skill discovery and question parsing."""
    print("🔍 Testing benchmark system setup...\n")
    
    # Check paths exist
    print(f"Skills directory: {SKILLS_DIR}")
    print(f"  Exists: {'✅' if SKILLS_DIR.exists() else '❌'}")
    
    print(f"\nTaxonomy file: {TAXONOMY_FILE}")
    print(f"  Exists: {'✅' if TAXONOMY_FILE.exists() else '❌'}")
    
    # Discover skills
    print("\n" + "="*60)
    print("Discovering Skills")
    print("="*60)
    
    try:
        skills = discover_skills()
        print(f"\n✅ Found {len(skills)} skills:\n")
        for skill in skills:
            print(f"  - {skill['name']}")
            print(f"    Script: {Path(skill['script_path']).name}")
            print(f"    Requirements: {len(skill['requirements'])} packages")
            print()
    except Exception as e:
        print(f"❌ Error discovering skills: {e}")
        return False
    
    # Parse questions
    print("="*60)
    print("Parsing Taxonomy Questions")
    print("="*60)
    
    try:
        questions = parse_taxonomy_questions()
        total_questions = sum(len(q) for q in questions.values())
        print(f"\n✅ Found {len(questions)} categories with {total_questions} total questions:\n")
        
        for category, question_list in questions.items():
            print(f"  - {category}: {len(question_list)} questions")
        
        # Show first question from first category
        if questions:
            first_category = list(questions.keys())[0]
            first_question = questions[first_category][0]
            print(f"\n📝 Example question ({first_category}):")
            print(f"   \"{first_question}\"")
    except Exception as e:
        print(f"❌ Error parsing questions: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ Benchmark system is ready!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Set your API keys (export OPENAI_API_KEY=...)")
    print("  2. Run a quick test: python run_benchmark.py --max-questions 1 --skills deep-research-tavily -v")
    print("  3. View QUICKSTART.md for more options")
    
    return True


if __name__ == "__main__":
    success = test_discovery()
    sys.exit(0 if success else 1)
