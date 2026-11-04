---
description: "Apply one bounded, lane-aware repair pass for verified review findings, then require fresh checks and re-review"
---

# Delivery Review Fix

```text
$ARGUMENTS
```

This is a coordinator step, not a reviewer and not another execution queue. It
owns one repair pass; the caller/workflow owns the loop and final gate. Read the
latest report produced under the installed Review template and its saved scope,
snapshot, finding IDs, and previous repair attempts. Use the existing run's
`reviews/<scope>/review.yml` and checkpoint record, honoring artifact policy;
do not invent a run path. The reviewer stays read-only; only the coordinator may
persist reports or dispatch an authorized repair.

When `delivery_run=<id>` is supplied, validate the same safe run-id contract as
Delivery Explore and use `.specify/delivery/<id>/` as the canonical run directory.
Read/persist reports and the attempt checkpoint there across host processes;
never fall back to a new Feature-derived record or an empty budget. A missing
existing report/checkpoint is a recovery blocker, not permission to reset state.

1. Verify the report matches the current code, requirements, and scope, including
   uncommitted contents, not only HEAD. Missing/malformed/stale reports produce
   `REVIEW_FIX_STATUS: blocked`; request a fresh review without editing source.
2. If the report is a complete current pass, return `no-op` without editing,
   changing counters, rerunning suites, or starting Ralph. An incomplete report
   with no confirmed repairable finding calls for coverage/evidence collection
   and fresh review, not speculative code changes. Report that blocker explicitly.
3. Verify each proposed blocker before accepting it. Retain stable finding IDs;
   record false positives with evidence, never silently drop findings. Design
   defects, new public contracts, migrations, or material scope expansion return
   to scope/Plan/ADR approval. Do not use review as authority for new features.
4. Read `max_review_fix_rounds` from Delivery configuration. It must be an
   integer from 1 through 3, and `repair_slots` must be the same range; a
   malformed, zero, negative, or out-of-range value returns `blocked` rather than
   silently using 3. The portable YAML supplies `repair_slots=<n>`: use the lower
   bound of configured rounds and that actual slot ceiling, not an assumed 3.
   Task-scoped Ralph repair uses the configured bound.
   A round is one attempted repair pass, not one finding or one no-op call.
   Preserve attempts across resume and reviewer reruns for the same run/scope;
   a new HEAD does not reset the budget. With `attempt=<n>`, read the canonical
   runtime contract and verify this exact pending `review:<scope>` reservation;
   consume it without allocating or completing a second counter. The workflow
   completes it only after checks and independent re-review. Without a supplied
   attempt, reserve through the same helper before editing and return its number
   to the caller; never create a parallel attempt ledger. At the cap, leave
   blockers open and return `blocked`; never downgrade to pass,
   invent an approval, or start a hidden loop inside this command.
5. Apply/dispatch only authorized confirmed repairs through the lane owner. When
   a repair changes any README-affecting surface defined by package-readme
   (purpose, install/setup, public API/CLI/config/default, compatibility,
   dependencies, error behavior, development/test commands, release/versioning,
   ownership), follow `templates/repair-docs.md` before refreshing checks. Pass the already reserved attempt as `attempt=<n>`; do not allocate a
   second counter. An internal-only repair records `DOCS_REFRESH: not-applicable`
   with a reason. Preserve the caller's existing `with_docs_sync` choice for
   nested Feature repairs; never infer or re-enable disabled optional sync, or
   edit generated projections directly.
   - **Feature, task scope:** return the verified findings, including affected
     documentation work and the `templates/repair-docs.md` contract path, to the
     active Ralph implementer for this same open task. Require its `DOCS_REFRESH`
     in the task packet/receipt before closure checks. Do not invoke Ralph recursively,
     change its checkbox, or create its closure commit. Ralph owns checks and
     re-review.
   - **Feature, outgoing-diff:** require the explicit canonical `slices` path and
     recorded `SLICE_APPROVAL: approved` snapshot; missing context is blocked, not
     a reason to fall back to a non-sliced Ralph run. Have the Core task owner
     (append-only Converge or a Tasks regeneration) add/reopen repair tasks retaining
     finding-ID references; do not hand-edit, renumber, reorder, or invent Core task
     items. Map every changed TaskID to an approved slice. If any mapping, queue, or
     slice identity changed, run
     Delivery Slice for the renewed mapping, Analyze, the combined execution/slice
     gate, and its approval writer before execution; never edit the slice map from
     this repair or reuse the old approval. After a changed queue/map is approved,
     invoke Delivery Route `action=checkpoint stage=outgoing-repair
     checkpoint_id=outgoing-repair-<attempt>` with the same
     run/exploration/slices/design/slice approvals and `with_docs_sync`. This is a
     native nested checkpoint: the route writes a unique
     `runtime/planning-inputs-outgoing-repair-<attempt>.json`/native handoff and
     performs only an already authorized planning commit. Do not fabricate a
     runtime stage ticket or leave a pending checkpoint; Ralph consumes that native
     handoff and the same queue. If the
     queue is unchanged, apply the repair directly and run Analyze/Ralph only if
     the design/slice identity actually changed. Preserve Ralph's clean preflight:
     unrelated work, missing authorization, or a wrong checkpoint base stops with
     recovery; never stash/reset, auto-commit production code, or stage pre-existing
     changes to bypass it.
   - **Bugfix:** follow the installed
     `.specify/extensions/delivery/templates/bugfix-review-repair.md` continuation
     adapter. The initial official fix/test commands refuse automated overwrite
     of existing reports; do not re-invoke them, delete reports, or invent consent.
     Preserve the approved assessment and original fix/test evidence, use one
     versioned repair/regression record per attempt, and require independent
     re-review. Do not require Feature spec/tasks to track review findings.
   - **Lightweight:** use `speckit.delivery.lightweight` for the same mechanical
     scope. Escalate rather than silently changing behavior or architecture.
6. After repairs, have the lane owner refresh the affected task/lane verification
   plus Quality and Standards for the new contents (Ralph for a Feature task;
   the Bugfix continuation/Lightweight owner otherwise). Reuse unchanged evidence
   only when exact contents/scope/requirements match. Update findings to `fixed-pending-review`,
   preserve unresolved IDs, and return control for independent `review.run`.
   A fixer cannot mark its own changes resolved or return REVIEW_VERDICT: pass.
   Keep the documentation refresh inside the same reserved attempt and existing
   lane/run artifacts; do not add a repair round or a second queue.

Return `REVIEW_FIX_STATUS: no-op | re-review-required | blocked`, actual attempt
count/cap, scope, report location, changed/task paths, evidence, unresolved IDs,
`DOCS_REFRESH_REQUIRED: true | false` (with reason when false), and
`DOCS_REFRESH: refreshed | unchanged | not-applicable | blocked` with its affected
surfaces, actual results, reused identity, and gaps. No-op alone is not a pass
verdict. On blocked/incomplete/cap exhaustion, stop with the unresolved owner
and exact recovery; the final runtime requirement and native review gate must
block delivery. Reviewer, model, and shell exit success are not authority to publish,
merge, create tracker resources, or silently waive findings.
