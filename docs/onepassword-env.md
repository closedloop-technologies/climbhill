# 1Password Environment Setup

Store provider API keys in 1Password and expose them to benchmark commands with
`op run`. Do not commit raw keys, generated `.env` files, or copied secrets.

## Recommended Vault and Item

Use one vault and one dotenv-style item for this repo:

- Vault: `awesome-deep-researchers`
- Item: `api-keys`
- Local env file: `.env.adr`

Start from the committed template:

```bash
cp .env.adr.example .env.adr
```

Use `docs/api-key-signup-checklist.md` for the service signup URLs and exact
1Password field names to create.

Example `.env.adr` using 1Password secret references:

```dotenv
OPENAI_API_KEY=op://awesome-deep-researchers/api-keys/OPENAI_API_KEY
PERPLEXITY_API_KEY=op://awesome-deep-researchers/api-keys/PERPLEXITY_API_KEY
EXA_API_KEY=op://awesome-deep-researchers/api-keys/EXA_API_KEY
TAVILY_API_KEY=op://awesome-deep-researchers/api-keys/TAVILY_API_KEY
JINA_API_KEY=op://awesome-deep-researchers/api-keys/JINA_API_KEY
XAI_API_KEY=op://awesome-deep-researchers/api-keys/XAI_API_KEY
YOU_API_KEY=op://awesome-deep-researchers/api-keys/YOU_API_KEY
GOOGLE_API_KEY=op://awesome-deep-researchers/api-keys/GOOGLE_API_KEY
GOOGLE_CLOUD_PROJECT=op://awesome-deep-researchers/api-keys/GOOGLE_CLOUD_PROJECT
HF_TOKEN=op://awesome-deep-researchers/api-keys/HF_TOKEN
ANTHROPIC_API_KEY=op://awesome-deep-researchers/api-keys/ANTHROPIC_API_KEY
BING_SEARCH_API_KEY=op://awesome-deep-researchers/api-keys/BING_SEARCH_API_KEY
YDC_API_KEY=op://awesome-deep-researchers/api-keys/YDC_API_KEY
```

## Commands

Create the vault if it does not exist:

```bash
op vault create awesome-deep-researchers
```

Create or edit the item:

```bash
op item create \
  --vault awesome-deep-researchers \
  --category "API Credential" \
  --title api-keys \
  OPENAI_API_KEY= \
  PERPLEXITY_API_KEY= \
  EXA_API_KEY= \
  TAVILY_API_KEY= \
  JINA_API_KEY= \
  XAI_API_KEY= \
  YOU_API_KEY= \
  GOOGLE_API_KEY= \
  GOOGLE_CLOUD_PROJECT= \
  HF_TOKEN= \
  ANTHROPIC_API_KEY= \
  BING_SEARCH_API_KEY= \
  YDC_API_KEY=
```

Run a benchmark through 1Password:

```bash
op run --env-file .env.adr -- python benchmark/run_benchmark.py \
  --skills deep-research-perplexity \
  --categories "Repository Refresh & Meta Research" \
  --max-questions 1 \
  -v
```

## Verification

Check that references resolve without printing secret values:

```bash
python -m awesome_deep_research.op_env --template
python -m awesome_deep_research.op_env --env-file .env.adr --scope core
python -m awesome_deep_research.op_env --op-scaffold --scope commercial
op run --env-file .env.adr -- python -m awesome_deep_research.op_env --live --scope core
```

The live check only reports whether variables are set and their string lengths.
It does not print secret values.

## Local Service Account Token

For local automation, `.env.local` may contain an ignored
`OP_SERVICE_ACCOUNT_TOKEN` with read/write access to the
`awesome-deep-researchers` vault. Load it only in the shell running `op`:

```bash
set -a
. ./.env.local
set +a
python -m awesome_deep_research.op_env --op-scaffold --scope commercial
op run --env-file .env.adr -- python -m awesome_deep_research.op_env --live --scope commercial
```

Do not commit `.env.local` or paste the token into logs. Verify access by
checking item metadata or redacted env status, not by printing field values.

## Live Benchmark Flow

1. Run the offline repository audit:

   ```bash
   python -m awesome_deep_research.audit
   ```

2. Verify 1Password references:

   ```bash
   python -m awesome_deep_research.op_env --env-file .env.adr --scope commercial
   python -m awesome_deep_research.op_env --op-scaffold --scope commercial
   op run --env-file .env.adr -- python -m awesome_deep_research.op_env --live --scope commercial
   ```

3. Run one under-`$1` smoke benchmark:

   ```bash
   op run --env-file .env.adr -- python benchmark/live_smoke.py -v
   ```

See `docs/live-benchmark-runbook.md` for strict mode and result inspection.
