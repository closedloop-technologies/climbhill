# CLI

This directory is reserved for the ClimbHill CLI package layout described in the project goal.

Current local MVP command implementation lives in `climbhill/cli.py` and exposes:

- `climbhill init`
- `climbhill prepare`
- `climbhill run`
- `climbhill compare`
- `climbhill decision`
- `climbhill report`
- `climbhill reflect`
- `climbhill policy check`

The target human interface is `assess`, `run`, `status`, and `decide`. The
additional commands above expose transitional implementation plumbing.
