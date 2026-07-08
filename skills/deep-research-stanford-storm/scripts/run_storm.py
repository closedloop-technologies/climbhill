import os
import argparse
import sys
import tempfile
import glob
from dotenv import load_dotenv

try:
    # Import STORM components, using LiteLLM for flexible configuration
    from knowledge_storm.storm_wiki.engine import StormEngine, StormEngineArgs
    from knowledge_storm.lm import LiteLLMModelArgs
except ImportError:
    print("Error: 'knowledge-storm' or dependencies not found. 'pip install knowledge-storm litellm dspy-ai'", file=sys.stderr)
    sys.exit(1)

load_dotenv()

def run_storm(topic: str, rm_name: str, fast_model: str, strong_model: str):
    # Define the output directory
    output_base_dir = "./storm_output"
    os.makedirs(output_base_dir, exist_ok=True)

    # Create a unique subdirectory for this run
    sanitized_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
    run_dir = tempfile.mkdtemp(prefix=f"run_{sanitized_topic}_", dir=output_base_dir)

    try:
        print(f"Starting STORM run for topic: '{topic}'", file=sys.stderr)
        print(f"Models: Fast={fast_model}, Strong={strong_model}. Retriever: {rm_name}", file=sys.stderr)
        print(f"Output directory: {run_dir}", file=sys.stderr)

        # 1. Configure Language Models using LiteLLM
        # LiteLLM automatically detects API keys from standard env vars (e.g., OPENAI_API_KEY).

        fast_lm_config = LiteLLMModelArgs(
            model=fast_model,
            temperature=0.7,
            max_tokens=1000
        )

        strong_lm_config = LiteLLMModelArgs(
            model=strong_model,
            temperature=0.7,
            max_tokens=4000
        )

        # 2. Initialize the STORM engine
        # We pass the fast config as the default, and override specific components.
        engine_args = StormEngineArgs(
            lm_config=fast_lm_config,
            rm_name=rm_name,
            # Override specific components to use the strong model
            outline_gen_lm_config=strong_lm_config,
            article_gen_lm_config=strong_lm_config,
            article_polish_lm_config=strong_lm_config
        )

        engine = StormEngine(engine_args)

        # 3. Run the engine (Research, Outline, Write, Polish)
        engine.run(
            topic=topic,
            output_dir=run_dir
        )

        # 4. Extract the results
        # The final polished article is typically saved in a subdirectory named after the topic.

        # STORM organizes output within the output_dir
        article_files = glob.glob(os.path.join(run_dir, "*", "storm_gen_article_polished.md"))

        if article_files:
            article_path = article_files[0]
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print("STORM run completed successfully.", file=sys.stderr)
            # Output the final article to stdout
            print(content)
        else:
            print(f"Error: Final article file not found. Check logs in {run_dir}.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error running Stanford STORM: {e}.", file=sys.stderr)
        print(f"Ensure API keys for the LLM ({strong_model}) and Search ({rm_name}) are correctly set.", file=sys.stderr)
        print(f"Intermediate files at: {run_dir}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Stanford STORM.")
    parser.add_argument("--topic", required=True, help="The subject to research.")
    parser.add_argument("--rm-name", default="bing", choices=["bing", "you"], help="Retriever module (ensure API key BING_SEARCH_API_KEY or YDC_API_KEY is set).")
    # Default models (can be overridden by user)
    parser.add_argument("--fast-model", default="gpt-3.5-turbo", help="LLM for faster tasks (LiteLLM compatible name).")
    parser.add_argument("--strong-model", default="gpt-4o", help="LLM for complex tasks (LiteLLM compatible name).")

    args = parser.parse_args()
    run_storm(args.topic, args.rm_name, args.fast_model, args.strong_model)
