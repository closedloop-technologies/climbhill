# Deep Research

This context defines the compatibility and research subsystem that acquires
evidence through one or more providers and persists traceable Open Knowledge
Format artifacts for later use.

## Language

**Research Request**:
A structured question with explicitly selected Provider IDs and optional bounded
concurrency.
_Avoid_: Prompt string, recursive Run

**Provider ID**:
The canonical `deep-research-` name for one supported research provider.
_Avoid_: Provider alias, model name

**Provider Alias**:
A tolerated input shorthand that resolves to a Provider ID but is not persisted
as canonical identity.
_Avoid_: Alternate provider, informal ID

**Provider Adapter**:
A callable integration that executes one Provider ID and returns raw output,
provider metadata, and a provider result status.
_Avoid_: Script parser, subprocess-only provider

**Provider Access Mode**:
The discovery category describing whether a provider is a commercial API,
self-hosted library, or search API.
_Avoid_: Provider type, implementation detail

**Raw Provider Output**:
Immutable original artifacts returned by a provider before normalization.
_Avoid_: Temporary output, normalized response

**OKF Bundle**:
A directory of traceable research concepts, findings, uncertainties, methods,
sources, indexes, and logs.
_Avoid_: Formatted report, recursive Run record

**Provider OKF Bundle**:
An OKF Bundle derived from one provider's Raw Provider Output.
_Avoid_: Partial report, aggregate bundle

**Aggregate OKF Bundle**:
The mechanically assembled OKF Bundle containing successful Provider OKF Bundles
for one Research Request.
_Avoid_: LLM synthesis, rewritten final answer

**Provider Event**:
A structured progress record containing Provider ID, kind, message, and timestamp.
_Avoid_: Unstructured log line, hidden progress

**Research Execution**:
One bounded execution of a Research Request with provider results, costs, events,
and artifact paths.
_Avoid_: Run, Campaign, task loop

**Research Execution Status**:
The overall outcome `succeeded`, `partial_success`, `failed`, `invalid_request`,
or `configuration_error` for a Research Execution.
_Avoid_: Run Status, Provider Result Status

**Provider Result Status**:
The outcome `succeeded`, `failed`, `timed_out`, or `skipped` for one selected
provider after execution begins.
_Avoid_: Research Execution Status, HTTP status

**Provider-Specific Metadata**:
Structured provider fields such as searches, sources, tokens, effort, model,
citations, or request IDs preserved without forcing a shared provider schema.
_Avoid_: Dropped fields, normalized-only metadata

**Output Root**:
The configured directory beneath which compatibility research executions write
their artifacts.
_Avoid_: Arbitrary request directory, recursive control repository

**Research Evidence Import**:
The operation that brings selected research artifacts into the Control Repository
so a recursive Run can pin them by commit and path.
_Avoid_: Transient citation, implicit context injection
