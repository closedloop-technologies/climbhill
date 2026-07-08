import argparse
import json
import os
import sys
from dotenv import load_dotenv

try:
    from xai_sdk import Client
    from xai_sdk.chat import user
    # Import server-side tools
    from xai_sdk.tools import web_search, x_search
except ImportError:
    print("Error: xai-sdk not found. Please install it using 'pip install xai-sdk'", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

def grok_research(query, model="grok-4.1-fast-reasoning", enable_web_search=False, enable_x_search=False):
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("Error: XAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = Client(api_key=api_key)

    tools = []
    if enable_web_search:
        tools.append(web_search())
    if enable_x_search:
        tools.append(x_search())

    if not tools:
        print("Note: No tools enabled. Grok will rely on internal knowledge.", file=sys.stderr)

    try:
        chat = client.chat.create(
            model=model,
            tools=tools,
        )
        chat.append(user(query))

        # Stream the response to see the agent's process
        print("--- Grok Agent Process (stderr) ---", file=sys.stderr)
        response = None
        for chunk in chat.stream():
            # Print tool calls and thought process to stderr for visibility
            if chunk.tool_calls:
                for call in chunk.tool_calls:
                    print(f"[Tool Call] {call.type}: {call.arguments}", file=sys.stderr)
            if chunk.is_thinking and chunk.content:
                 print(f"[Thinking] {chunk.content}", file=sys.stderr)
            response = chunk

        print("\n--- Final Answer (stdout) ---", file=sys.stderr)

        # Output the final answer to stdout
        if response and response.content:
            print(response.content)
            if response.citations:
                print("\n--- Citations ---")
                for c in response.citations:
                    print(f"- {c.title}: {c.url}")
        else:
            print("No final response received.")

    except Exception as e:
        print(f"Error calling xAI API: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform research using the xAI Grok API with agentic tools.")
    parser.add_argument("--query", required=True, help="The research query.")
    parser.add_argument("--model", default="grok-4.1-fast-reasoning", help="The Grok model to use (e.g., grok-4.1-fast-reasoning, grok-4).")
    parser.add_argument("--web-search", action="store_true", help="Enable web search tool.")
    parser.add_argument("--x-search", action="store_true", help="Enable X (Twitter) search tool.")

    args = parser.parse_args()
    grok_research(args.query, args.model, args.web_search, args.x_search)
