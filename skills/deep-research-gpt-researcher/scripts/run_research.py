import asyncio
import os
import argparse
import sys
from dotenv import load_dotenv

try:
    from gpt_researcher import GPTResearcher
except ImportError:
    print("Error: gpt-researcher not found. 'pip install gpt-researcher'", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

async def generate_research_report(query, report_type="research_report"):
    """Generates a research report using GPT Researcher."""

    # Basic check for required keys (GPT-R uses these by default)
    if not os.getenv("TAVILY_API_KEY"):
         print("Warning: TAVILY_API_KEY not set. GPT Researcher may fail without a search provider.", file=sys.stderr)

    # Note: LLM keys (like OPENAI_API_KEY) are also required depending on the LLM configured.

    try:
        print(f"Initializing GPT Researcher for query: {query} (Type: {report_type})...", file=sys.stderr)
        # Initialize the researcher
        # Configuration for LLM is typically handled via environment variables
        researcher = GPTResearcher(query=query, report_type=report_type)

        print("Conducting research (this may take a few minutes)...", file=sys.stderr)
        await researcher.conduct_research()

        print("Writing report...", file=sys.stderr)
        report = await researcher.write_report()

        # Output the final report to stdout
        print(report)

    except Exception as e:
        print(f"Error running GPT Researcher: {e}", file=sys.stderr)
        print("Please ensure all required dependencies and API keys (LLM and Search) are configured.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GPT Researcher.")
    parser.add_argument("--query", required=True, help="The research topic.")
    parser.add_argument("--report-type", default="research_report",
                        choices=["research_report", "resource_report", "outline_report", "custom_report", "deep_research_report"],
                        help="The type of report to generate.")

    args = parser.parse_args()
    # Run the async function
    asyncio.run(generate_research_report(args.query, args.report_type))
