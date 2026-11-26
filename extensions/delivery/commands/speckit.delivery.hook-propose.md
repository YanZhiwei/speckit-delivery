---
description: "Spec Kit after_plan hook: reuse or establish the active Feature run's Proposed ADR baseline and pre-gate design snapshot"
---

# Delivery Hook: after_plan

Event adapter for Spec Kit's `after_plan` extension hook. It keeps a direct
`/speckit-plan` invocation from skipping the Feature run's Proposed ADR
baseline and Delivery pre-gate design snapshot. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run, a
   non-Feature lane, or an ambiguous selection, stop with the shared output.
2. Require the canonical exploration packet, the exact bound `plan.md` Core
   just wrote, and the run's recorded scope approval. Missing inputs are
   `ACTION: blocked` with the exact gap; do not read another Feature's plan.
3. **Reuse:** when the packet already records the final presented
   fingerprint/method/input manifest for the current `plan.md` bytes and each
   material open decision already has a Proposed ADR or an explicit
   not-ADR-worthy classification, report `ACTION: reused`. A portable
   workflow's `decision-propose` step applies this same check instead of
   proposing twice.
4. **Prepare:** otherwise dispatch `speckit.decision.propose` with
   `delivery_run=<id> exploration=.specify/delivery/<id>/exploration.md`,
   reading the bound Spec, clarified requirements, exact plan, and decision
   context instead of the original request text. Follow its installed command:
   establish the Proposed ADR baseline and record the pre-gate design snapshot
   in the packet.
5. Present the resulting design, ADR baseline, Architecture constraints, and
   cooperation/context plan to the user as the next review subject, then stop.
   The adapter never runs `present --name design`/`decide --name design`,
   never accepts an ADR, and never treats this presentation as design approval;
   the existing plan gate in the workflow or `/sd` owns that decision.

## Completion

The adapter is complete when the current plan has a Proposed ADR baseline and a
recorded pre-gate snapshot (reused or newly prepared), or when it reports a
skipped/blocked result. It never edits `plan.md`, source, or `tasks.md`, and it
never grants design approval.
