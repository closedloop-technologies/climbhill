# Resources

Resources contain research, prior art, user guidance, postmortems, benchmark notes, case studies, and promoted experiment learnings that agents may use during improvement loops.

Resources should not silently become trusted. Each added resource should include metadata:

- Title
- Source or path
- Author when known
- Date when known
- Type
- Summary
- Tags
- Trust level
- Path or URL
- Reason it was added

## Structure

- `research/` - published research and third-party technical references
- `prior-art/` - related systems and implementation approaches
- `benchmarks/` - benchmark notes and evaluation context
- `case-studies/` - examples from real improvement runs
- `user-guidance/` - user-provided instructions and constraints
- `postmortems/` - failures, lessons, and follow-up actions

## Trust Levels

- `primary` - official docs, source code, direct user instruction, or first-party evidence
- `secondary` - high-quality analysis or credible third-party interpretation
- `experimental` - unverified notes, hypotheses, or early observations
- `deprecated` - retained for history but no longer recommended
