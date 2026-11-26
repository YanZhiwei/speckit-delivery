---
description: "Spec Kit after_implement/after_bug_test hook: run or reuse a read-only simplification scan for the active run"
---

# Delivery Hook: after_implement / after_bug_test

Event adapter for Spec Kit's `after_implement` and the Bug extension's
`after_bug_test` hooks (both registered as optional). It offers a read-only
simplification scan after direct Core/Bug execution. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run or an
   ambiguous selection, stop with the shared output. During a Bugfix
   review-repair continuation, use the current round's repaired contents and
   reports, not the original `fix.md`/`test.md`.
2. **Immutable proposal guard:** when the runtime records
   `simplify: approve`, report `ACTION: reused` and keep the accepted proposal
   byte-identical; verification belongs to `speckit.simplify.verify` through
   its owning workflow, not to a fresh scan.
3. **Reuse:** when `.specify/delivery/<id>/simplifications.md` already reports
   the current diff's scan and its inputs are unchanged, report
   `ACTION: reused` with its candidate IDs; do not rescan the same contents.
4. **Scan:** otherwise dispatch `speckit.simplify.scan` with the actual lane,
   `delivery_run=<id> scope=diff`, the canonical exploration/assessment
   references for that lane, and no `runtime_stage`/`runtime_result`. It writes
   only this run's canonical `simplifications.md` (or reports `none`); a
   portable workflow's explicit simplify step reuses that native report and
   still performs its own runtime transport.
5. Report the candidate IDs or the no-candidate result and stop. The adapter
   never presents or records the simplify decision, applies a candidate, edits
   source/`tasks.md`/Bug reports, or starts another verification pass. The
   existing simplify gate and lane-owned application remain with the workflow
   or `/sd`; rejecting candidates there continues the lane unchanged.

## Completion

The adapter is complete when a current read-only scan is reused or written (or
an immutable accepted proposal is left untouched), or when it reports a
skipped/blocked result. Candidates are proposals only, never approved edits.
