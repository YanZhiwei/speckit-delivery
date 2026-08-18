---
description: "Retrieve architecture decisions and durable project context governing the current work"
---

# Decision Context

## Input

```text
$ARGUMENTS
```

Read the project's decision-memory configuration when present. Discover the Constitution, agent instructions, domain context, configured ADR roots, and the code area named by the work. Search ADR titles, status, links, terms, components, configuration keys, APIs, storage formats, and supersession relations.

Classify results as:

- active constraints;
- superseded historical context;
- conflicts with the proposed work;
- open decisions the plan must resolve; and
- missing evidence.

In pre-spec discovery mode, return terminology and constraints without selecting a solution. In pre-plan resolve mode, follow relevant ADR dependencies and compare their claims with current code.

Write `.specify/delivery/<feature>/decision-context.md` when a feature directory is known; otherwise report the result without inventing a feature path. The command is complete when every cited ADR was read, its status is known, and conflicts/open decisions are explicit.
