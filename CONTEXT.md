# Awesome Deep Researchers

This context defines the language for the repository's deep research orchestration
application: turning a human research question into traceable Open Knowledge
Format output through one or more selected providers.

## Language

**MCP-first Application**:
The primary user-facing product shape: an MCP server exposes tools that accept a
research question and selected providers, then returns Open Knowledge Format
output. Existing CLIs and scripts are supporting implementation paths, not the
canonical interface.
_Avoid_: CLI-first application, script wrapper

**Provider ID**:
The canonical name for a deep research provider in this repository. Provider IDs
use the `deep-research-` namespace, such as `deep-research-perplexity`.
_Avoid_: provider slug, model name

**Provider Alias**:
A tolerated shorthand for a Provider ID in user input. For example, `perplexity`
may resolve to `deep-research-perplexity`, but persisted outputs should use the
Provider ID.
_Avoid_: alternate provider, informal ID

**Explicit Provider Selection**:
The v1 rule that a research request must name one or more providers. Missing or
empty provider input is an error that should return available Provider IDs and
accepted Provider Aliases.
_Avoid_: automatic provider selection, default provider set

**Research Request**:
The structured input to `deep_research`, containing a required non-empty
question, a required array of provider names, and optional `max_concurrency`.
Provider names may be Provider IDs or Provider Aliases.
_Avoid_: prompt string, comma-separated provider list

**OKF Bundle**:
A folder of Open Knowledge Format-style markdown files that preserves report,
finding, uncertainty, method, source, index, and log concepts for a research run.
_Avoid_: OKR, formatted report

**Provider OKF Bundle**:
An OKF Bundle generated from one provider's raw research output for a research
request. Each selected Provider ID can produce zero or one Provider OKF Bundle.
_Avoid_: provider report, partial bundle

**Raw Provider Output**:
The original response artifacts returned by a provider for a research request.
These artifacts are immutable evidence for the run and should be written before
OKF normalization rather than overwritten by it.
_Avoid_: temporary output, normalized response

**Aggregate OKF Bundle**:
The primary OKF Bundle returned by the MCP-first Application, synthesized across
the successful Provider OKF Bundles for a research request.
_Avoid_: combined report, merged output

**Mechanical Aggregation**:
The v1 aggregation rule: combine successful Provider OKF Bundles into an
Aggregate OKF Bundle without asking another LLM to rewrite or synthesize the
knowledge. Calling agents may use OKF skills later to reformat or interpret the
bundle.
_Avoid_: LLM synthesis, final answer generation

**Run Metadata**:
Structured facts about a research request and each provider result, including
cost, latency, provider status, model or effort settings, timestamps, raw output
paths, and OKF bundle paths.
_Avoid_: logs, stats, incidental output

**Cost Reporting**:
The v1 rule that provider costs are captured in Run Metadata when available,
including estimated or actual cost fields returned by providers. v1 does not
enforce pre-run cost budgets.
_Avoid_: budget enforcement, cost gate

**Inline Run Summary**:
The compact structured metadata returned directly from `deep_research`, including
Run Status, Aggregate OKF Bundle path, per-provider status, latency, cost, Raw
Provider Output path, Provider OKF Bundle path, and Provider-Specific Metadata.
Large reports remain in run artifacts rather than in the MCP response body.
_Avoid_: full report response, path-only response

**Provider Event**:
A streamed progress event for one provider during a research request. It should
include the Provider ID, an event kind such as `started`, `finished`, `error`,
or `info`, a human-readable message, and a timestamp.
_Avoid_: unstructured log line, hidden progress

**Event Log**:
The persisted `events.jsonl` file in the Run Directory containing Provider
Events and run-level events emitted during execution.
_Avoid_: stdout-only progress, transient stream

**Provider-Specific Metadata**:
Additional structured fields returned by a provider, such as number of searches,
source counts, token usage, effort tier, model, citations, or provider request
IDs. These fields should be preserved under the provider result without forcing
all providers into one shared schema.
_Avoid_: dropped provider fields, normalized-only metadata

**Optional Citation Evidence**:
The v1 rule that citations and source records are preserved when providers return
them, but a successful provider result does not require at least one citation.
Missing citations should remain visible in Provider-Specific Metadata or OKF
uncertainty records rather than becoming a provider failure.
_Avoid_: mandatory citation gate, hidden missing sources

**Parallel Provider Execution**:
The v1 rule that all selected providers are run concurrently. Callers may
optionally provide a concurrency limit, but fallback chains and sequential
provider policies are out of scope for v1.
_Avoid_: fallback execution, provider priority chain

**Partial Success**:
A completed research request where at least one selected provider succeeded and
at least one selected provider failed. The Aggregate OKF Bundle is built only
from successful Provider OKF Bundles, while failed providers remain visible in
Run Metadata.
_Avoid_: degraded success, ignored failure

**Interrupted Run**:
A research request whose MCP client disconnects or process is interrupted before
normal completion. In v1, interruption is recorded best-effort in the Event Log
and Run Metadata, but there is no explicit cancellation contract, cancel tool, or
resume semantics.
_Avoid_: cancellation workflow, resumable run

**Run Status**:
The status for the whole Research Request. Valid v1 values are `succeeded`,
`partial_success`, `failed`, `invalid_request`, and `configuration_error`.
_Avoid_: provider status, HTTP status

**Provider Result Status**:
The status for one selected provider after provider execution begins. Valid v1
values are `succeeded`, `failed`, `timed_out`, and rare internal `skipped`.
_Avoid_: run status, preflight status

**Provider Adapter**:
A callable Python integration for one Provider ID that returns structured
provider output, Provider-Specific Metadata, and Provider Result Status. The MCP
server should call Provider Adapters directly; CLI scripts are wrappers.
_Avoid_: subprocess-only provider, script parser

**MCP Tool Surface**:
The v1 MCP server exposes only `list_providers` for discovery and configuration
visibility, and `deep_research` for execution. Artifact browsing,
re-normalization, provider dry-runs, and cleanup are later features or developer
utilities.
_Avoid_: broad MCP API, management tool suite

**Output Root**:
The MCP server configuration value that determines where research run artifacts
are written. If omitted, the Output Root defaults to `~/.deep-research/outputs`.
_Avoid_: temporary folder, implicit cwd output

**MCP Server Environment**:
The environment variables supplied by the MCP server definition, including API
keys and `DEEP_RESEARCH_OUTPUT_ROOT`. In v1, provider credentials live here
rather than in per-request arguments.
_Avoid_: request credentials, inline API keys

**Provider Timeout Configuration**:
Provider-specific or default timeout limits supplied by MCP server
configuration. In v1, timeout limits are installation concerns rather than
per-request `deep_research` fields.
_Avoid_: request timeout, caller-controlled timeout

**Provider Enabled State**:
A boolean reported by `list_providers` that says whether a supported provider
has the required configuration in the MCP Server Environment. Disabled providers
remain visible but should fail validation if selected for a research request.
_Avoid_: hidden provider, installed provider

**Provider Access Mode**:
The discovery-time category for how a provider is accessed, such as
`commercial_api`, `self_hosted_library`, or `search_api`. `list_providers`
should expose this so agents can distinguish API providers from self-hosted
libraries before starting a research request.
_Avoid_: provider type, implementation detail

**Configuration Error**:
A preflight failure caused by missing or invalid MCP Server Environment values,
such as selecting a disabled provider. The error should identify missing
configuration and point the user or agent to the provider's required env vars.
_Avoid_: provider failure, runtime failure

**Unknown Provider Error**:
A preflight failure caused by a provider name that cannot be resolved to a
Provider ID or Provider Alias. The remedy is to fix the request using
`list_providers`, not to change MCP configuration.
_Avoid_: provider failure, configuration error

**Run Directory**:
A unique directory created under the Output Root for one research request. v1
does not accept arbitrary per-request output paths.
_Avoid_: caller output directory, temporary run folder

## Example Dialogue

Developer: "Should the MCP tool accept `perplexity`?"
Domain expert: "Yes, as a Provider Alias. Store and report it as the Provider ID
`deep-research-perplexity`."

Developer: "Is the CLI the main interface?"
Domain expert: "No. The MCP-first Application is the main product. The CLI can
remain as an implementation or debugging path."

Developer: "Can the MCP tool choose providers if the request omits them?"
Domain expert: "No. In v1 we use Explicit Provider Selection; missing providers
returns a helpful error."

Developer: "Should providers be a comma-separated MCP field?"
Domain expert: "No. A Research Request uses an array of provider names; agents
can translate comma-separated human input into that array."

Developer: "Do we only keep the final synthesized result?"
Domain expert: "No. Keep Provider OKF Bundles for auditability and return the
Aggregate OKF Bundle as the primary result."

Developer: "Can OKF normalization overwrite provider responses?"
Domain expert: "No. Treat Raw Provider Output as immutable evidence and write
Provider OKF Bundles beside it."

Developer: "Should the aggregate bundle be rewritten by an LLM?"
Domain expert: "No. Use Mechanical Aggregation for v1; downstream agents can
reformat the OKF Bundle later."

Developer: "Should the result only return folders?"
Domain expert: "No. Return Run Metadata with costs, latency, status, and paths
alongside the OKF bundle locations."

Developer: "Should v1 stop providers before execution based on a cost budget?"
Domain expert: "No. Use Cost Reporting only in v1; budget enforcement can come
later."

Developer: "Should `deep_research` return only artifact paths?"
Domain expert: "No. Return both source-of-truth artifact paths and an Inline Run
Summary for orchestration."

Developer: "Should callers wait silently for the whole run?"
Domain expert: "No. Stream Provider Events such as `[provider] started ...`,
`[provider] finished ...`, and `[provider] error ...`, and persist them in the
Event Log."

Developer: "Are Provider Events just text lines?"
Domain expert: "No. Provider Events are structured records that clients may
render as text."

Developer: "What about extra API details like number of searches?"
Domain expert: "Keep them as Provider-Specific Metadata on the provider result."

Developer: "Does a successful provider need at least one citation?"
Domain expert: "No. Use Optional Citation Evidence: preserve citations when
present and make missing citations visible without failing the provider."

Developer: "If one provider fails, do we fail the whole request?"
Domain expert: "No. Use Partial Success when at least one provider succeeds, and
record failed providers in Run Metadata."

Developer: "Should v1 define a cancellation tool or resumable cancellation
semantics?"
Domain expert: "No. Treat disconnects and process interruptions as Interrupted
Runs and record them best-effort."

Developer: "Do provider failures and invalid requests share one status?"
Domain expert: "No. Use Run Status for the whole request and Provider Result
Status for individual provider execution."

Developer: "Should the MCP server shell out to skill scripts?"
Domain expert: "No. The MCP server should call Provider Adapters; scripts can
remain wrappers for humans and benchmarks."

Developer: "Should the MCP server expose artifact browsing and cleanup tools in
v1?"
Domain expert: "No. Keep the MCP Tool Surface to `list_providers` and
`deep_research`."

Developer: "Should providers run one after another?"
Domain expert: "No. Use Parallel Provider Execution in v1; a concurrency limit
is optional."

Developer: "Where do run artifacts go?"
Domain expert: "Use the configured Output Root, defaulting to
`~/.deep-research/outputs`."

Developer: "Can a request choose any output directory?"
Domain expert: "No. v1 creates a Run Directory under the configured Output Root."

Developer: "Where do provider API keys live?"
Domain expert: "In the MCP Server Environment, not in request payloads."

Developer: "Should callers pass provider timeouts with each request?"
Domain expert: "No. Use Provider Timeout Configuration from the MCP server
configuration."

Developer: "Should unconfigured providers disappear from provider discovery?"
Domain expert: "No. `list_providers` returns all supported providers and marks
each Provider Enabled State."

Developer: "Should provider discovery say whether providers are APIs or
self-hosted libraries?"
Domain expert: "Yes. `list_providers` should expose each Provider Access Mode
alongside ID, aliases, enabled state, and required MCP env var names."

Developer: "What if a request selects a disabled provider?"
Domain expert: "Return a Configuration Error before starting any providers, with
instructions for fixing the MCP Server Environment."

Developer: "What if a request uses an unsupported provider name?"
Domain expert: "Return an Unknown Provider Error and point the caller to
`list_providers`."
