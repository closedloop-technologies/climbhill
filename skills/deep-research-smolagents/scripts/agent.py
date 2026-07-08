import argparse
import os
import sys
from dotenv import load_dotenv

try:
    from smolagents import CodeAgent, ToolCallingAgent
    from smolagents import InferenceClientModel, LiteLLMModel, TransformersModel
    from smolagents import DuckDuckGoSearchTool
except ImportError:
    print("Error: smolagents not found. Install with: pip install 'smolagents[toolkit]'", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

def create_model(model_type: str = "hf", model_id: str = None):
    """Create and return the appropriate model based on type."""

    if model_type == "hf":
        # Hugging Face Inference API
        if not os.getenv("HF_TOKEN"):
            print("Warning: HF_TOKEN not set. Using default (may have rate limits).", file=sys.stderr)

        if model_id:
            return InferenceClientModel(model_id=model_id)
        else:
            # Use a good default reasoning model
            return InferenceClientModel(model_id="Qwen/Qwen2.5-72B-Instruct")

    elif model_type == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
            sys.exit(1)
        model_id = model_id or "gpt-4o"
        return LiteLLMModel(model_id=model_id)

    elif model_type == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY not set.", file=sys.stderr)
            sys.exit(1)
        model_id = model_id or "claude-3-5-sonnet-20241022"
        return LiteLLMModel(model_id=model_id)

    elif model_type == "local":
        if not model_id:
            print("Error: --model-id required for local models.", file=sys.stderr)
            sys.exit(1)
        return TransformersModel(model_id=model_id)

    else:
        print(f"Error: Unknown model type '{model_type}'", file=sys.stderr)
        sys.exit(1)

def run_agent(task: str, model_type: str = "hf", model_id: str = None,
              web_search: bool = False, verbose: bool = False):
    """Run the Smolagents agent on the given task."""

    try:
        print(f"Initializing Smolagents ({model_type})...", file=sys.stderr)

        # Create model
        model = create_model(model_type, model_id)

        # Prepare tools
        tools = []
        if web_search:
            tools.append(DuckDuckGoSearchTool())
            print("✓ Web search enabled", file=sys.stderr)

        # Create agent
        # CodeAgent writes Python code to accomplish tasks (more efficient)
        agent = CodeAgent(
            tools=tools,
            model=model,
            max_steps=10,
        )

        print(f"\nTask: {task}", file=sys.stderr)
        print("="*80, file=sys.stderr)

        # Run the agent
        if verbose:
            print("\n[Agent Execution]", file=sys.stderr)

        result = agent.run(task)

        print("\n" + "="*80, file=sys.stderr)
        print("RESULT:", file=sys.stderr)
        print("="*80 + "\n", file=sys.stderr)

        # Output result to stdout
        print(result)

        # Show agent logs if verbose
        if verbose and hasattr(agent, 'logs'):
            print("\n" + "="*80, file=sys.stderr)
            print("EXECUTION LOGS:", file=sys.stderr)
            print("="*80, file=sys.stderr)
            for log in agent.logs:
                print(log, file=sys.stderr)

    except Exception as e:
        print(f"\nError during agent execution: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Hugging Face Smolagents for agentic research tasks."
    )
    parser.add_argument("--task", required=True, help="The task or research question.")
    parser.add_argument("--model", default="hf",
                       choices=["hf", "openai", "anthropic", "local"],
                       help="Model type (default: hf for Hugging Face Inference API).")
    parser.add_argument("--model-id", help="Specific model ID to use.")
    parser.add_argument("--web-search", action="store_true",
                       help="Enable web search tool (DuckDuckGo).")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed execution logs.")

    args = parser.parse_args()

    run_agent(
        task=args.task,
        model_type=args.model,
        model_id=args.model_id,
        web_search=args.web_search,
        verbose=args.verbose
    )
