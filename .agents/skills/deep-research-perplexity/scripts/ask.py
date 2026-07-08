import os
import argparse
import sys
from dotenv import load_dotenv

try:
    # Perplexity API is compatible with the OpenAI client structure
    from openai import OpenAI
except ImportError:
    print("Error: openai library not found. Please run 'pip install openai'", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

def ask_perplexity(prompt, model="sonar", search_context_size="low"):
    """Sends a prompt to the Perplexity Sonar API."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("Error: PERPLEXITY_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert researcher. Respond to the user's query using the most recent and relevant information available on the web."
                    "Provide a comprehensive, accurate, and neutral response. Cite your sources clearly."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_body={"search_context_size": search_context_size},
        )

        # Extract and output the synthesized answer
        answer = response.choices[0].message.content
        print(answer)
        usage = getattr(response, "usage", None)
        cost = getattr(usage, "cost", None) if usage is not None else None
        total_cost = None
        if isinstance(cost, dict):
            total_cost = cost.get("total_cost")
        elif cost is not None:
            total_cost = getattr(cost, "total_cost", None)
        if total_cost is not None:
            print(f"actual_cost = {total_cost}", file=sys.stderr)

    except Exception as e:
        print(f"Error during Perplexity API call: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perplexity Sonar Tool for Claude Skills")
    parser.add_argument("--prompt", required=True, help="The research question or prompt.")
    parser.add_argument("--model", default="sonar",
                        choices=["sonar", "sonar-pro"],
                        help="The Perplexity Sonar model to use.")
    parser.add_argument("--search-context-size", default="low",
                        choices=["low", "medium", "high"],
                        help="Search context size. Use low for under-$1 benchmark smoke.")

    args = parser.parse_args()
    ask_perplexity(args.prompt, args.model, args.search_context_size)
