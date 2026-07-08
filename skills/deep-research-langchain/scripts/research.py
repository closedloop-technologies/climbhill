import argparse
import asyncio
import json
import os
import sys
from dotenv import load_dotenv

try:
    from langchain_core.messages import HumanMessage
    from langgraph_sdk import get_client
except ImportError:
    print("Error: Required packages not found.", file=sys.stderr)
    print("Install with: pip install langgraph-sdk langchain-core", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

async def run_research(query: str, max_iterations: int = 3, output_file: str = None):
    """
    Run the LangChain Open Deep Research agent.

    This function assumes the LangGraph server is running locally.
    You can start it with: langgraph dev --allow-blocking
    """

    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("TAVILY_API_KEY"):
        print("Warning: TAVILY_API_KEY not set. Search may not work properly.", file=sys.stderr)

    try:
        print(f"Starting deep research on: {query}", file=sys.stderr)
        print(f"Max iterations: {max_iterations}", file=sys.stderr)
        print("", file=sys.stderr)

        # Connect to LangGraph server (assumes server is running)
        # To start server: cd to open_deep_research dir and run: langgraph dev --allow-blocking
        client = get_client(url="http://localhost:2024")

        # Create thread for this research session
        thread = await client.threads.create()

        # Create input message
        input_data = {
            "messages": [HumanMessage(content=query)],
            "max_iterations": max_iterations
        }

        print("Running research agent...", file=sys.stderr)
        print("", file=sys.stderr)

        # Stream the response to show progress
        final_state = None
        async for chunk in client.runs.stream(
            thread["thread_id"],
            "agent",
            input=input_data,
            stream_mode="updates"
        ):
            if chunk.data:
                # Print progress to stderr
                for key, value in chunk.data.items():
                    if isinstance(value, dict):
                        if "messages" in value:
                            last_msg = value["messages"][-1] if value["messages"] else None
                            if last_msg:
                                print(f"[{key}] {last_msg.content[:100]}...", file=sys.stderr)
                final_state = chunk.data

        # Extract the final report
        if final_state and "messages" in final_state:
            messages = final_state["messages"]
            final_message = messages[-1] if messages else None

            if final_message:
                report = final_message.content

                # Output to file or stdout
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"\n✅ Report saved to: {output_file}", file=sys.stderr)
                else:
                    print("\n" + "="*80, file=sys.stderr)
                    print("FINAL REPORT", file=sys.stderr)
                    print("="*80, file=sys.stderr)
                    print(report)
            else:
                print("Error: No final message received from agent.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: No state received from agent.", file=sys.stderr)
            sys.exit(1)

    except ConnectionError:
        print("\n❌ Error: Could not connect to LangGraph server.", file=sys.stderr)
        print("\nTo use this skill, you need to:", file=sys.stderr)
        print("1. Clone the open_deep_research repository:", file=sys.stderr)
        print("   git clone https://github.com/langchain-ai/open_deep_research.git", file=sys.stderr)
        print("2. Navigate to the directory and install dependencies:", file=sys.stderr)
        print("   cd open_deep_research && uv sync", file=sys.stderr)
        print("3. Start the LangGraph server:", file=sys.stderr)
        print("   langgraph dev --allow-blocking", file=sys.stderr)
        print("4. Run this script again", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during research: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run LangChain Open Deep Research agent for comprehensive research reports."
    )
    parser.add_argument("--query", required=True, help="The research question or topic.")
    parser.add_argument("--max-iterations", type=int, default=3,
                       help="Maximum number of research iterations (default: 3).")
    parser.add_argument("--output", help="Output file path for the report (optional).")

    args = parser.parse_args()

    # Run the async function
    asyncio.run(run_research(args.query, args.max_iterations, args.output))
