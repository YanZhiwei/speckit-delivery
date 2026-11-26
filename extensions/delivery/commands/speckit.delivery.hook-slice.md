---
description: "Spec Kit after_tasks/after_converge hook: reuse the current slice plan or map newly generated/appended tasks for the active Feature run"
---

# Delivery Hook: after_tasks / after_converge

Event adapter for Spec Kit's `after_tasks` and `after_converge` extension
hooks. It keeps the active Feature run's slice plan mapped to the real Task IDs
when Core generates tasks or Converge appends new ones. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run, a
   non-Feature lane, or an ambiguous selection, stop with the shared output.
2. Require the bound `tasks.md`, approved plan, and canonical
   `.specify/delivery/<id>/exploration.md`. The runtime must record
   `design: approve`; without it, report `ACTION: blocked` and route the user
   to the existing design gate instead of planning slices over an unapproved
   design.
3. **Reuse:** when `.specify/delivery/<id>/slices.md` exists, its
   `SLICE_PLAN_FINGERPRINT` still matches the current approved plan/tasks
   identity, and every current Task ID is mapped exactly once, report
   `ACTION: reused`. This covers a Converge assessment that appended nothing
   and a workflow whose explicit slice step already ran.
4. **Prepare:** when tasks are unmapped or newly appended, dispatch
   `speckit.delivery.slice` with `lane=feature delivery_run=<id>
   exploration=<packet> slices=.specify/delivery/<id>/slices.md
   design_approval=approve`, reading the approved plan and actual queue. After
   Converge, instruct it to plan the renewed mapping for every actual appended
   Task ID while preserving prior receipt history and boundaries. It must not
   edit `tasks.md` or implement; `needs_decision` is returned to the user, not
   forced into a mode.
5. Stop after planning. The adapter never runs the slice approval writer,
   `present`/`decide --name execution`, Analyze, a planning checkpoint, or
   Ralph. A new or changed mapping stays pending until the existing combined
   execution/slice gate in the workflow or `/sd` approves it.

## Completion

The adapter is complete when every current Task ID has an exactly-once mapping
(reused or newly planned) or a `needs_decision`/blocked result is reported. A
planned mapping is not an approved execution boundary.
