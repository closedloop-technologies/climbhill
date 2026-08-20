# Use Git-backed Runs as the recursive optimization root

ClimbHill uses `Run -> Attempt -> Evaluation -> Decision` as its recursive engine
model, with optional Jobs providing UX grouping and defaults. Git commits own
content revision history; each Run pins an immutable baseline, one mutable focus,
an external evaluation strategy, an authorization envelope, and a promotion
target. Agentic continuation analysis may recommend typed actions, but only
deterministic policy and explicit Decisions can authorize or execute them. This
avoids a second revision graph and allows task, learning, and alignment loops to
share one controller without letting an optimizer rewrite its own evaluator or
authority.
