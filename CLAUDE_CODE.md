# CLAUDE_CODE.md: Headless Execution Manual for Deep Research Skills

## 1\. Introduction

Claude Code (`claude`) is an agentic tool that allows LLMs to interact with your local environment using "Skills." While often used interactively, these skills can also be operated in "headless" mode for automation.

There are two primary ways to execute these skills headlessly:

1. **Agentic Headless Execution (The Claude CLI)**: You use the Claude Code CLI to ask the agent (Claude) to perform a task non-interactively. The agent then selects and executes the appropriate skill script. This uses the official headless mode (`claude -p`).
2. **Direct Script Execution (Pipelines)**: You bypass the agent entirely and directly run the Python scripts that power the skills. This offers maximum reliability and performance, ideal for robust automation pipelines and chaining skills together.

This guide covers both methods.

## 2\. Prerequisites

Before running headless tasks, ensure your environment is configured.

### 2.1. Claude Code CLI Installation

If using Mode 1, you must install the Claude Code CLI.

**Native Install (Recommended):**

```bash
# macOS, Linux, WSL
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew
brew install --cask claude-code
```

**NPM Install:**

```bash
npm install -g @anthropic-ai/claude-code
```

### 2.2. Authentication (Mode 1 only)

If using Mode 1, authenticate the CLI with your Claude account.

```bash
claude
# Follow the prompts to log in. Exit the interactive session once authenticated.
```

### 2.3. Skill Setup and Dependencies

The skills must be installed either globally (`~/.agents/skills/<skill-name>`) or locally in your project (`.agents/skills/<skill-name>`).

Crucially, you must install the Python dependencies required by the skill scripts, regardless of the execution mode.

```bash
pip install openai tavily-python exa-py gpt-researcher xai-sdk requests python-dotenv knowledge-storm litellm dspy-ai
```

### 2.4. API Key Configuration

The deep research skills rely heavily on API keys. The provided scripts use `python-dotenv` to load keys from a `.env` file in the current working directory.

```bash
# Example .env file
OPENAI_API_KEY=sk_...
PERPLEXITY_API_KEY=pplx_...
TAVILY_API_KEY=tvly_...
EXA_API_KEY=exa_...
XAI_API_KEY=xai_...
JINA_API_KEY=jina_...
BING_SEARCH_API_KEY=... # Required for STORM default
```

*Note: Always add `.env` to your `.gitignore` file.*

## 3\. Mode 1: Agentic Headless Execution (Claude CLI)

In this mode, you invoke the Claude CLI to run a task non-interactively. The agent interprets your prompt and executes the necessary tools.

### 3.1. Using `claude -p`

The primary command for this mode is `claude -p` (or `--print`).

```bash
claude -p "<task_description>" [--model <model_name>] [--output-format <format>]
```

### 3.2. Directing Skill Usage

For reliable automation, your prompt must be explicit about which skill and script to use. If the prompt is ambiguous, the agent might ask for clarification or choose the wrong tool, breaking the automation.

**Effective Prompt Structure:**

> "Use the `<skill-name>` skill. Execute the `<script_name.py>` script with the following parameters: `<parameters>`."

### 3.3. Examples

#### Example 1: Real-Time Synthesis (Perplexity Sonar)

```bash
claude -p "Use the deep-research-perplexity skill. Execute the scripts/ask.py script with the prompt 'What are the latest developments in the EV market in Q4 2025?' and use the 'sonar-large-online' model." \
  --model claude-3-5-sonnet-20240620 > ev_market_q4_2025.md
```

The CLI will output the agent's thought process to the terminal (stderr), while the final report (stdout) is saved to the file.

#### Example 2: Comprehensive Report (GPT Researcher)

*Note: Agents like GPT Researcher can take several minutes.*

```bash
claude -p "Use the deep-research-gpt-researcher skill. Execute the scripts/run_research.py script with the query 'The future of renewable energy sources' and the report type 'deep_research_report'." \
  --model claude-3-5-sonnet-20240620 > renewable_energy_report.md
```

### 3.4. Using JSON Output

For robust programmatic parsing, use `--output-format json`. This wraps the result in a structured format, including metadata.

```bash
claude -p "Use deep-research-tavily (scripts/tavily_search.py) to find 'latest LLM benchmarks'." --output-format json
```

**Output Structure (JSON):**

```json
{
  "session_id": "...",
  "model": "claude-3-5-sonnet-20240620",
  "result": "{\n  \"answer\": \"The latest LLM benchmarks...\",\n  \"results\": [...] \n}",
  "cost_usd": 0.015
}
```

You can extract the actual result using `jq` (a command-line JSON processor):

```bash
claude -p "..." --output-format json | jq -r '.result' | jq .
```

## 4\. Mode 2: Direct Script Execution (Pipelines)

In this mode, you directly execute the Python scripts associated with the skills. This bypasses the LLM agent entirely, offering maximum reliability, speed, and flexibility for automation pipelines.

### 4.1. Syntax

You invoke the scripts using your standard Python interpreter. The scripts load configurations automatically from the `.env` file in the current directory.

```bash
python3 path/to/skill/scripts/<script_name.py> [arguments]
```

### 4.2. Examples

Assuming skills are installed locally in `./.agents/skills/`.

#### Example 1: Tavily Search (Direct)

```bash
python3 .agents/skills/deep-research-tavily/scripts/tavily_search.py \
  --query "LLM interpretability techniques" \
  --search-depth advanced > sources.json
```

#### Example 2: Stanford STORM (Direct)

```bash
# Ensure OPENAI_API_KEY and BING_SEARCH_API_KEY are set in .env
python3 .agents/skills/deep-research-stanford-storm/scripts/run_storm.py \
  --topic "The History of Quantum Computing" \
  --strong-model gpt-4o \
  --rm-name bing > quantum_history_article.md
```

### 4.3. Chaining Skills (Automation Workflows)

A key advantage of direct execution is the ability to chain skills together using standard Unix command substitution, creating complex research workflows.

#### Example Workflow: Neural Search and Content Extraction

**Goal**: Find the most relevant article on a topic using Exa AI, and then convert that specific article into clean Markdown using Jina AI.

**Prerequisite**: Install `jq` for parsing JSON.

```bash
#!/bin/bash

# Define script paths (assuming local installation)
EXA_SCRIPT=".agents/skills/deep-research-exa/scripts/exa_tools.py"
JINA_SCRIPT=".agents/skills/deep-research-jina/scripts/jina_tools.py"
QUERY="Best practices for securing Kubernetes clusters in production"

# 1. Search using Exa. The exa_tools.py script outputs a JSON array.
echo "Searching for relevant articles with Exa..."
SEARCH_RESULTS=$(python3 $EXA_SCRIPT search "$QUERY" --num-results 5)

# 2. Extract the URL of the first result using jq
TARGET_URL=$(echo "$SEARCH_RESULTS" | jq -r '.[0].url')

# 3. Check if a URL was found (Crucial error handling)
if [ -z "$TARGET_URL" ] || [ "$TARGET_URL" == "null" ]; then
    echo "Error: No relevant URL found by Exa."
    exit 1
fi

echo "Found top URL: $TARGET_URL"

# 4. Use Jina Reader to convert the URL to Markdown
echo "Converting URL content to Markdown with Jina..."
python3 $JINA_SCRIPT read "$TARGET_URL" > k8s_security_article.json

echo "Article content (JSON with Markdown) saved to k8s_security_article.json"
```

## 5\. Best Practices for Automation

The provided deep research skills adhere to these conventions to enable robust headless execution:

1. **stdout vs. stderr**:

      * **stdout** is used exclusively for the primary output (the report, the JSON data). This enables piping (`|`) and redirection (`>`).
      * **stderr** is used for logging, progress indicators, warnings, and errors.

2. **Exit Codes**:

      * Scripts exit with status `0` upon success.
      * Scripts exit with a non-zero status (e.g., `1`) upon failure (e.g., missing API key, failed request).

3. **Error Handling in Scripts**: Always check the exit code when automating, regardless of the mode used.

<!-- end list -->

```bash
# Example: Direct Execution Error Handling
python3 .agents/skills/deep-research-perplexity/scripts/ask.py ...
if [ $? -ne 0 ]; then
    echo "Perplexity skill failed!"
    exit 1
fi

# Example: Agentic CLI Error Handling
if ! claude -p "Use deep-research-tavily to check the weather."; then
    echo "Claude Code execution failed."
    exit 1
fi
```
