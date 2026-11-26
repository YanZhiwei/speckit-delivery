---
description: "Spec Kit before_plan hook: reuse or prepare the active Feature run's ADR resolution and code context"
---

# Delivery Hook: before_plan

Event adapter for Spec Kit's `before_plan` extension hook. It prepares the
active Feature run's decision resolution and, only when a concrete gap remains,
its code-context brief before Core Plan runs. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run, a
   non-Feature lane, or an ambiguous selection, stop with the shared output.
2. Require the run's canonical exploration packet and bound Feature paths; a
   missing packet or binding is `ACTION: blocked` with the exact missing input,
   not permission to invent a Feature directory.
3. **Decision resolution:** when `.specify/delivery/<id>/decision-context.md`
   already resolves this run's approved exploration and clarified requirements
   and those inputs are unchanged, reuse it. Otherwise dispatch
   `speckit.decision.context` with `mode=resolve lane=feature
   delivery_run=<id> exploration=.specify/delivery/<id>/exploration.md`,
   reading the bound Spec and the actual clarification choice recorded for this
   run. Surface any scope-changing ADR conflict instead of silently planning
   around it.
4. **Code context:** dispatch `speckit.delivery.context` with
   `lane=feature delivery_run=<id>` and the standing instruction to reuse the
   current Explore map and write only this run's `code-context.md` when a
   concrete gap remains. Its native reuse rules decide; a current Explore
   mapping without a concrete gap means no new file and no repeated discovery.
5. Record nothing in the runtime: no stage tickets, no design presentation, no
   approval. Plan and the design gate remain with Core and the existing
   workflow/Route.

## Completion

The adapter is complete when decision context is current (reused or resolved)
and code context is either reused or written for a concrete gap, or when it
reports a skipped/blocked result. It never writes `plan.md`, proposes an ADR,
or approves design.
