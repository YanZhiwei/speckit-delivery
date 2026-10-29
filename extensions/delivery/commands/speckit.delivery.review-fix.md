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
4. Respect `max_review_fix_rounds` from Delivery configuration (default 3).
   The portable YAML supplies `repair_slots=<n>` (1–3): use the lower bound of
   configured rounds and that actual slot ceiling, not an assumed 3. Task-scoped
   Ralph repair uses the configured bound.
   A round is one attempted repair pass, not one finding or one no-op call.
   Preserve attempts across resume and reviewer reruns for the same run/scope;
   a new HEAD does not reset the budget. Record the next attempt before editing.
   At the cap, leave blockers open and return `blocked`; never downgrade to pass,
   invent an approval, or start a hidden loop inside this command.
5. Apply/dispatch only authorized confirmed repairs through the lane owner:
   - **Feature, task scope:** return the verified findings to the active Ralph
     implementer for this same open task. Do not invoke Ralph recursively, change
     its checkbox, or create its closure commit. Ralph owns checks and re-review.
   - **Feature, outgoing-diff:** add/reopen repair tasks in `tasks.md`, retaining
     finding-ID references; run analyze and then Ralph. Preserve Ralph's clean
     preflight: if tracked queue changes need a planning-state commit, follow
     existing project Git authorization and commit only this run's declared
     planning paths before Ralph. If that is not authorized or unrelated work
     prevents a clean entry, stop with recovery instructions; never stash/reset,
     auto-commit production code, or stage pre-existing changes to bypass it.
   - **Bugfix:** follow the installed
     `.specify/extensions/delivery/templates/bugfix-review-repair.md` continuation
     adapter. The initial official fix/test commands refuse automated overwrite
     of existing reports; do not re-invoke them, delete reports, or invent consent.
     Preserve the approved assessment and original fix/test evidence, use one
     versioned repair/regression record per attempt, and require independent
     re-review. Do not require Feature spec/tasks to track review findings.
   - **Lightweight:** use `speckit.delivery.lightweight` for the same mechanical
     scope. Escalate rather than silently changing behavior or architecture.
6. After repairs, refresh the affected task/lane verification plus Quality and
   Standards for the new contents. Reuse unchanged evidence only when exact
   contents/scope/requirements match. Update findings to `fixed-pending-review`,
   preserve unresolved IDs, and return control for independent `review.run`.
   A fixer cannot mark its own changes resolved or return REVIEW_VERDICT: pass.

Return `REVIEW_FIX_STATUS: no-op | re-review-required | blocked`, actual attempt
count/cap, scope, report location, changed/task paths, evidence, and unresolved
IDs. No-op alone is not a pass verdict. On blocked/incomplete/cap exhaustion the
workflow may finish its safe no-op slots, but the final review gate must stop
delivery. Reviewer, model, and shell exit success are not authority to publish,
merge, create tracker resources, or silently waive findings.
