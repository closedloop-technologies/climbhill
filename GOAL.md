# Goal: MCP-First Deep Research to OKF

Build an MCP-first application that turns a human research question into a
traceable Open Knowledge Format folder by running one or more explicitly
selected deep research providers in parallel.

## Primary Outcome

A calling agent can ask a question such as "how can I grow basil at home", name
one or more providers, and receive:

- an Aggregate OKF Bundle path;
- per-provider OKF Bundle paths;
- immutable Raw Provider Output paths;
- an Inline Run Summary with status, latency, cost, provider-specific metadata,
  and artifact locations;
- a persisted Event Log of structured provider progress events.

The canonical domain language and v1 boundaries are defined in
[`CONTEXT.md`](CONTEXT.md).

## Product Boundary

The primary interface is an MCP server, not a CLI. Existing CLIs and benchmark
scripts may remain as developer and benchmark utilities, but the v1 product
surface is limited to:

- `list_providers`
- `deep_research`

Provider execution should use Python Provider Adapters directly. The MCP server
should not depend on shelling out to skill scripts as its normal integration
path.

## Request Contract

`deep_research` accepts a structured Research Request:

- required non-empty `question`;
- required `providers: string[]`;
- optional `max_concurrency`.

Provider names should prefer canonical Provider IDs such as
`deep-research-perplexity`, while accepting aliases such as `perplexity`.
Persisted outputs and metadata should use canonical Provider IDs.

The request schema should not include provider credentials, per-request output
directories, per-request timeouts, or cost budgets in v1.

## Provider Discovery

`list_providers` returns the full supported provider list, including:

- Provider ID;
- aliases;
- enabled state from MCP server configuration;
- required MCP environment variable names;
- Provider Access Mode, such as `commercial_api`, `self_hosted_library`, or
  `search_api`.

Unknown provider names are invalid request errors. Disabled selected providers
are configuration errors and must fail validation before any provider starts.

## Execution Boundary

Provider execution is strictly parallel in v1. If `max_concurrency` is omitted,
all selected providers run concurrently. If provided, it limits concurrent
provider execution without introducing fallback chains or priority policies.

Partial success is allowed when at least one provider succeeds. Failed, timed
out, or interrupted providers remain visible in Run Metadata and the Event Log.
There is no explicit cancellation or resumable-run contract in v1.

## Output Boundary

Artifacts are written under an Output Root from MCP server configuration,
defaulting to `~/.deep-research/outputs`. Each request creates a unique Run
Directory under that root.

Raw Provider Output is immutable evidence and must be written before OKF
normalization. Provider OKF Bundles are derived beside raw output. The Aggregate
OKF Bundle is mechanically assembled from successful Provider OKF Bundles
without an additional LLM synthesis pass in v1.

OKF bundle conventions are described in
[`docs/okf-normalization.md`](docs/okf-normalization.md). The broader deep
research agent model and provider access-mode distinction are described in
[`docs/deep-research-agent.md`](docs/deep-research-agent.md).

## Streaming and Metadata

The MCP server should stream structured Provider Events with at least:

- Provider ID;
- event kind, such as `started`, `finished`, `error`, or `info`;
- message;
- timestamp.

The same events should be persisted to `events.jsonl` in the Run Directory.

The final Inline Run Summary should include compact orchestration metadata, not
large report bodies. It should report costs when available, but v1 does not
enforce cost budgets. Provider-specific fields such as number of searches,
source counts, token usage, effort tier, model, citations, or provider request
IDs should be preserved without forcing all providers into one shared schema.

## Acceptance Criteria

- `list_providers` reports every supported provider and whether it is enabled in
  the MCP Server Environment.
- `deep_research` rejects missing providers, unknown providers, and selected
  disabled providers before execution starts.
- Selected providers run in parallel and emit structured progress events.
- Each successful provider writes Raw Provider Output and a Provider OKF Bundle.
- The run writes an Aggregate OKF Bundle from successful provider bundles.
- Partial success returns a usable aggregate when at least one provider succeeds.
- The final response includes an Inline Run Summary with status, costs,
  latencies, provider-specific metadata, and artifact paths.
- The Run Directory contains enough metadata and logs for another agent to audit
  or re-normalize the result.

## Deferred

- automatic provider selection;
- cost-budget enforcement;
- artifact browsing tools;
- cleanup tools;
- provider dry-run tools;
- explicit cancellation or resumable-run semantics;
- LLM synthesis of the aggregate bundle.
