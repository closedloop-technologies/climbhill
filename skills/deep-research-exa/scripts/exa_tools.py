import argparse
import json
import os
import sys
from dotenv import load_dotenv
import requests

try:
    # Exa's research endpoint uses OpenAI SDK compatibility
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Load environment variables
load_dotenv()

EXA_SEARCH_URL = "https://api.exa.ai/search"


def get_exa_key():
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("Error: EXA_API_KEY not found.", file=sys.stderr)
        sys.exit(1)
    return api_key


def get_exa_client():
    get_exa_key()

def search(query, num_results=5, highlights=False):
    api_key = get_exa_key()
    try:
        contents = {"highlights": True} if highlights else {"text": True}
        response = requests.post(
            EXA_SEARCH_URL,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json={
                "query": query,
                "numResults": num_results,
                "type": "auto",
                "contents": contents,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()

        results = []
        for result in payload.get("results", []):
            results.append({
                "url": result.get("url"),
                "title": result.get("title"),
                # Return highlights or text based on the flag
                "content": result.get("highlights") if highlights else result.get("text"),
            })
        return results
    except requests.RequestException as e:
        print(f"Error during Exa search: {e}", file=sys.stderr)
        sys.exit(1)

def research(query, model="exa-research"):
    # Research uses OpenAI compatible endpoint hosted by Exa
    api_key = get_exa_key()
    if OpenAI is None:
        print("Error: openai not found. 'pip install openai'", file=sys.stderr)
        sys.exit(1)

    # Initialize OpenAI client pointing to Exa's base URL
    client = OpenAI(
        base_url="https://api.exa.ai",
        api_key=api_key
    )

    try:
        # Using Chat Completions API for Exa research models
        print(f"Starting Exa Research task (Model: {model})...", file=sys.stderr)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}]
        )
        # Note: Citations are typically embedded in the content for this endpoint format.
        return {"output": completion.choices[0].message.content}

    except Exception as e:
        print(f"Error during Exa research: {e}", file=sys.stderr)
        sys.exit(1)


def find_similar(url, num_results=5):
    print("find_similar requires the exa-py SDK and is not used by the benchmark.", file=sys.stderr)
    sys.exit(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Exa AI for search and research.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search parser
    search_parser = subparsers.add_parser("search", help="Perform a neural search and retrieve content.")
    search_parser.add_argument("query")
    search_parser.add_argument("--num-results", type=int, default=5)
    search_parser.add_argument("--highlights", action="store_true", help="Return highlights instead of full text.")

    # Research parser
    research_parser = subparsers.add_parser("research", help="Automate in-depth web research.")
    research_parser.add_argument("query")
    research_parser.add_argument("--model", default="exa-research", choices=["exa-research", "exa-research-pro"])

    # Find Similar parser
    similar_parser = subparsers.add_parser("find_similar", help="Find pages similar to a given URL.")
    similar_parser.add_argument("url")
    similar_parser.add_argument("--num-results", type=int, default=5)

    args = parser.parse_args()

    result = None
    if args.command == "search":
        result = search(args.query, args.num_results, args.highlights)
    elif args.command == "research":
        result = research(args.query, args.model)
    elif args.command == "find_similar":
        result = find_similar(args.url, args.num_results)

    if result:
        print(json.dumps(result, indent=2))
