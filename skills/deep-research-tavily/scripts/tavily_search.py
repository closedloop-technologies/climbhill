import os
import argparse
import json
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

API_URL = "https://api.tavily.com/search"


def perform_search(query, search_depth="basic", max_results=5):
    """Performs a search using the Tavily API."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not set.", file=sys.stderr)
        exit(1)

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()

        # Structure the output for LLM consumption
        output = {
            "answer": payload.get("answer"),
            "results": payload.get("results", [])
        }

        # Output the results as JSON
        print(json.dumps(output, indent=2))

    except requests.RequestException as e:
        print(f"Error during Tavily search: {e}", file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tavily Research Tool")
    parser.add_argument("--query", required=True, help="The search query.")
    parser.add_argument("--search-depth", default="basic", choices=["basic", "advanced"])
    parser.add_argument("--max-results", type=int, default=5)

    args = parser.parse_args()
    perform_search(args.query, args.search_depth, args.max_results)
