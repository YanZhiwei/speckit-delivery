---
description: "Find evidence-backed simplification candidates and route them without expanding scope silently"
---

# Simplification Scan

## Input

```text
$ARGUMENTS
```

Default to the current outgoing diff. Scan the repository only when the user explicitly requested a broad audit. Read project governance, decisions, architecture, and dependency policy before judging intentional seams.

Look for unused public methods/config/events, tests-or-docs-only behavior, duplicate representations, unused seams, speculative generality, redundant lifecycle state, obsolete compatibility machinery, and hand-rolled behavior covered by a healthy builtin or dependency.

For each candidate classify consumers as production, non-production, or ambiguous. Inspect dynamic registration, configuration, serialization, plugins, scripts, examples, migrations, and external contracts before claiming absence. Estimate net deletion: removed implementation/tests/docs minus remaining glue and compatibility cost.

Write `.specify/delivery/<feature>/simplifications.md` when a feature is active. Route a behavior-preserving local candidate to `tasks.md`; route behavior/public-contract changes to clarify/plan; route architecture changes to a Proposed ADR; route out-of-scope work to an issue/proposal; report insufficient evidence without editing.

The scan is complete when every proposed removal has consumer evidence, a stated capability trade-off, and a route. A wrapper that relocates the same complexity is not a simplification.
