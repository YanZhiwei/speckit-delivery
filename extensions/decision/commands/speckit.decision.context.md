---
description: "Retrieve architecture decisions and durable project context governing the current work"
---

# Decision Context

## Input and run/output binding

```text
$ARGUMENTS
```

When invoked by a Delivery workflow, require explicit
`lane=feature|bugfix|lightweight` and `delivery_run=<id>`. Validate the run as a
safe single path segment and use the exact canonical output
`.specify/delivery/<delivery_run>/decision-context.md`; the run id is not a
Feature or Bug slug. A standalone invocation without `delivery_run` returns the
context inline and reports `DECISION_CONTEXT_PATH: inline`; it must not infer
another active Feature, create a directory, or relocate an existing packet.

Per-run operational state/results belong under
`.specify/delivery/<delivery_run>/runtime/`; the decision context report remains
at the run root. Follow the central Delivery runtime owner at
`.specify/extensions/delivery/templates/runtime.md`. When either
`runtime_stage` or `runtime_result` is supplied, require the canonical
`delivery_run`, read that file in full, and follow its runtime contract; do not
invent helper flags, paths, or result schemas. With neither argument, do not
create runtime state here.

Read the project's decision-memory configuration when present. Discover the Constitution, agent instructions, domain context, configured ADR roots, and the code area named by the work. Search ADR titles, status, links, terms, components, configuration keys, APIs, storage formats, and supersession relations.

Classify results as:

- active constraints;
- superseded historical context;
- conflicts with the proposed work;
- open decisions the plan must resolve; and
- missing evidence.

In pre-spec discovery mode, return terminology and constraints without selecting a solution. In pre-plan resolve mode, follow relevant ADR dependencies and compare their claims with current code.

When `delivery_run` is supplied, write or update only
`.specify/delivery/<delivery_run>/decision-context.md`; never derive the path
from a Feature/Bug slug or move a packet after identity becomes known. Without a
run, report the result inline and do not create a directory. Return
`LANE: <feature|bugfix|lightweight|standalone>`, `DELIVERY_RUN: <id or none>`,
and `DECISION_CONTEXT_PATH: <actual path or inline>`. The command is complete
when every cited ADR was read, its status is known, and conflicts/open decisions
are explicit.
