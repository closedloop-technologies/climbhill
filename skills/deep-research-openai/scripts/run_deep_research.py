import argparse
import json
import os
import sys
from typing import Optional

from dotenv import load_dotenv

try:
    from openai import OpenAI
    from openai._exceptions import APIStatusError
except ImportError:  # pragma: no cover - dependency issue surfaced to user
    print("Error: openai package not installed. Run 'pip install openai'.", file=sys.stderr)
    sys.exit(1)

load_dotenv()


def validate_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is not set. Add it to your environment or .env file.", file=sys.stderr)
        sys.exit(1)


def run_deep_research(
    prompt: str,
    model: str = "o4-mini-deep-research",
    effort: str = "medium",
    emit_json: bool = False,
    output_path: Optional[str] = None,
) -> None:
    validate_api_key()

    client = OpenAI()

    reasoning = {"effort": effort}

    # Stream the response so users can see progress in the terminal.
    try:
        stream = client.responses.stream(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            reasoning=reasoning,
            extra_headers={"OpenAI-Beta": "assistants=v2"},
        )
    except APIStatusError as exc:
        print(f"Deep Research request failed ({exc.status_code}): {exc.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unexpected error calling OpenAI API: {exc}", file=sys.stderr)
        sys.exit(1)

    report_sections = []
    json_payload = None

    with stream as events:
        for event in events:
            event_type = getattr(event, "type", "")

            if event_type == "response.output_text.delta":
                chunk = event.delta
                if chunk:
                    report_sections.append(chunk)
                    if not emit_json:
                        print(chunk, end="", flush=True)

            elif event_type == "response.completed":
                json_payload = event.response
            elif event_type == "response.error":  # pragma: no cover - surfaced immediately
                print(f"Deep Research error: {event.error}", file=sys.stderr)
                sys.exit(1)

    final_report = "".join(report_sections)

    if emit_json and json_payload is not None:
        serialized = json.dumps(json_payload, indent=2)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(serialized)
            print(f"\nReport JSON saved to {output_path}", file=sys.stderr)
        else:
            print(serialized)
        return

    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(final_report)
        print(f"\nReport saved to {output_path}", file=sys.stderr)
    elif emit_json:
        print("{}")  # no payload returned


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OpenAI Deep Research jobs from Claude Skills.")
    parser.add_argument("--prompt", required=True, help="Research prompt to investigate.")
    parser.add_argument("--model", default="o4-mini-deep-research",
                        choices=["o4-mini-deep-research", "o3-deep-research"],
                        help="Deep Research model to use.")
    parser.add_argument("--effort", default="medium",
                        choices=["low", "medium", "high"],
                        help="Research effort / depth level.")
    parser.add_argument("--json", action="store_true",
                        help="Emit the full JSON payload instead of only the final report text.")
    parser.add_argument("--output", help="Optional output file path for the report or JSON.")

    args = parser.parse_args()
    run_deep_research(args.prompt, args.model, args.effort, args.json, args.output)
