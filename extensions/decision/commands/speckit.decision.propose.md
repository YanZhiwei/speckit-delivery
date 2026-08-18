---
description: "Create or revise Proposed ADRs after a Spec Kit plan establishes an implementation baseline"
---

# Propose Architecture Decision

## Input

```text
$ARGUMENTS
```

Read the current Spec, clarified requirements, Plan, decision context, and existing same-topic ADRs. Create an ADR only for a decision that will constrain multiple implementation points or future work: ownership boundaries, public contracts, durable formats, security policy, storage/cache consistency, long-lived dependencies, or supersession of an accepted approach.

Write the record to the configured ADR directory with status `Proposed`. Include context, decision, strongest alternatives, consequences, constraints, and relationships to existing ADRs. Use `Supersedes` only when the new decision actually replaces the old one; use `Depends on` for a governing decision that remains active.

Do not promote local implementation details or an index of several ADRs into an ADR. The command is complete when each material open decision is either represented by one Proposed ADR or explicitly classified as not ADR-worthy.
