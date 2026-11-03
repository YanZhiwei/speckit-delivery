---
description: "Create or revise Proposed ADRs after a Spec Kit plan establishes an implementation baseline, and record Delivery's pre-gate design snapshot when requested"
---

# Propose Architecture Decision

## Input

```text
$ARGUMENTS
```

Read the current Spec, clarified requirements, Plan, decision context, and existing same-topic ADRs. Create an ADR only for a decision that will constrain multiple implementation points or future work: ownership boundaries, public contracts, durable formats, security policy, storage/cache consistency, long-lived dependencies, or supersession of an accepted approach.

Write the record to the configured ADR directory with status `Proposed`. Include context, decision, strongest alternatives, consequences, constraints, and relationships to existing ADRs. Use `Supersedes` only when the new decision actually replaces the old one; use `Depends on` for a governing decision that remains active.

Do not promote local implementation details or an index of several ADRs into an ADR. When the Feature workflow supplies `delivery_run` and the canonical `exploration` packet, after establishing the Proposed ADR baseline, act as the Delivery coordinator described by the installed Plan checkpoint: record the final presented fingerprint/method/input manifest in that packet and prepare the same design/ADR/constraint presentation for the existing plan gate. This does not accept an ADR, add a gate, or infer approval. The command is complete when each material open decision is either represented by one Proposed ADR or explicitly classified as not ADR-worthy, and any requested coordinator snapshot is recorded or blocked with its exact missing input.
