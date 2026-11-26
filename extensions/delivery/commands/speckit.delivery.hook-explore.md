---
description: "Spec Kit before_specify hook: reuse or prepare the active Feature run's decision discovery, exploration packet, and scope approval"
---

# Delivery Hook: before_specify

Event adapter for Spec Kit's `before_specify` extension hook. It keeps a direct
`/speckit-specify` invocation evidence-first for an active Feature Delivery run.
Read `.specify/extensions/delivery/templates/hooks.md` in full first; it owns
run resolution, event context, reuse, mutation limits, and the output block.
This adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run, a
   non-Feature lane, or an ambiguous selection, stop with the shared skipped or
   recovery output; do not initialize a run or explore without one.
2. Read the run's canonical `.specify/delivery/<delivery_run>/exploration.md`
   and the run's recorded `scope` approval.
3. **Reuse:** when the packet exists and the runtime records
   `scope: approve` against its current bytes (a portable workflow records this
   before Specify), report `ACTION: reused` and dispatch nothing. Do not repeat
   decision discovery, exploration, or the scope presentation.
4. **Prepare:** when the packet is missing, dispatch
   `speckit.decision.context` with `mode=discover lane=feature
   delivery_run=<id>` and then `speckit.delivery.explore` with
   `lane=feature delivery_run=<id>`, instructing it to persist the canonical
   packet and to create no Feature directory. Follow their installed commands;
   this adapter does not duplicate their investigation.
5. **Scope decision (direct path only):** when a packet exists but no scope
   approval is recorded, show the packet's current/candidate trees, evidence,
   exclusions, risks, and unknowns, then run
   `present --run <id> --name scope --input .specify/delivery/<id>/exploration.md`.
   Ask the user for an explicit scope decision. Only after an actual answer,
   record it with `decide --run <id> --name scope --choice approve|reject`.
   On rejection or a critical gap, report `ACTION: blocked`, stop the
   surrounding Specify, and route the user back to `/sd`.
6. A stale packet or changed scope after a recorded approval requires renewed
   exploration and presentation; never restamp the old choice onto new bytes.

## Completion

The adapter is complete when the run has a current packet with a recorded
actual scope choice (reused or newly recorded), or when it reports a
skipped/blocked result with its exact reason. It never emits `FEATURE_DIR`,
writes a Spec, or approves design.
