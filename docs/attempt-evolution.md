# Attempt Evolution

Attempt evolution improves solution strategies across one Run or parent-linked Run
trees while preserving content and semantic lineage.

## Modes

- Single Attempt
- Parallel independent Attempts
- Historical sampling
- Recombination
- Meta-analysis

Additional Attempts remain in the same Run only while Baseline, Focus, Evaluation
Strategy, Promotion Target, and Authorization Envelope are unchanged. Changing
one of those creates a child Run.

## Lineage

Supported semantic relationships are:

- `forked_from`
- `inspired_by`
- `combined_with`
- `supersedes`
- `reverted_from`
- `failed_due_to`
- `promoted_from`

Lineage explains why an Attempt exists and what evidence it used. Git ancestry is
reserved for real content ancestry.
