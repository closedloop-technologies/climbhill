# Context Map

## Contexts

- [Recursive Optimization](./docs/contexts/recursive-optimization/CONTEXT.md) - controls what a Run may change, how Attempts are evaluated, and what authority may promote or continue work
- [Deep Research](./docs/contexts/deep-research/CONTEXT.md) - acquires evidence through research providers and produces traceable OKF research artifacts

## Relationships

- **Deep Research -> Recursive Optimization**: Research produces versioned evidence in the Control Repository; a Run pins the exact Control commit and research paths it used.
- **Recursive Optimization -> Deep Research**: A diagnostic evaluation may identify an evidence gap and request bounded research without changing the Run's writable focus.
- **Shared Git state**: Both contexts use ordinary Git commits for content identity. Neither introduces a second revision graph.
