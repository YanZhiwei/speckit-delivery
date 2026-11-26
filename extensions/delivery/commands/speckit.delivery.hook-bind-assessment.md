---
description: "Spec Kit after_bug_assess hook: bind the actual Bug assessment to the active Bugfix Delivery run"
---

# Delivery Hook: after_bug_assess

Event adapter for the Bug extension's `after_bug_assess` hook. It binds the
assessment Bug Assess just wrote to the active Bugfix Delivery run so the
coordinator, fix, and review consume the same exact report. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run, a
   non-Bugfix lane, or an ambiguous selection, stop with the shared output; a
   standalone Bug extension assessment stays valid without Delivery.
2. Use the actual `BUG_SLUG`/`BUG_DIR` and written `assessment.md` from this
   session's Bug Assess, together with the run's canonical exploration packet.
   The Delivery run id is never the Bug slug. When the assessment was not
   written (an early stop), report `ACTION: skipped` with that reason.
3. **Reuse:** when the run's bindings already name this exact assessment path,
   report `ACTION: reused`; never rebind to a different Bug or relocate the
   mapping.
4. **Bind:** otherwise run
   `bind --run <id> --assessment .specify/bugs/<actual-slug>/assessment.md`.
   The helper rejects a slug mismatch; stop on that error instead of selecting
   another Bug directory.
5. Tell the user the assessment and exploration packet are the next review
   subject, then stop. The adapter never runs `present`/`decide --name
   assessment`, never records the assessment approval, and never dispatches
   `speckit.bug.fix`; the existing assessment gate in the workflow or `/sd`
   owns the scope decision.

## Completion

The adapter is complete when the run binds the actual assessment (reused or
newly bound), or when it reports a skipped/blocked result. Binding is identity
transport, not reproduction evidence, root-cause confirmation, or permission
to fix.
