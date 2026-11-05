---
description: "Run Spec Kit tasks through a bounded Ralph loop with per-task Git commits"
---

# Spec Kit + Ralph bridge

## Input

```text
$ARGUMENTS
```

This command is the Feature execution owner between Spec Kit's structured
artifacts and a bounded Ralph loop. It consumes the active Feature's `tasks.md`
and executes exactly one dependency-ready task per iteration. The default
portable mode is sequential: do not dispatch parallel workers in the shared
worktree.

For an SD Feature invocation, read the installed
`.specify/extensions/delivery/templates/core-adapter.md` in full before crossing
a Core Tasks/Analyze/Converge handoff into execution. That adapter is the
SD-scoped compatibility layer around the installed Core prompts; it does not
edit generated Core commands. Core Tasks/Analyze/Converge remain their owners,
while a completed Ralph run is the Core Converge implementation-run
precondition. Standalone Core Implement remains supported outside SD. The
adapter's verified planning-commit transfer is mandatory: Ralph may execute
only from the checkpoint's verified `execution_base` containing the approved
`planning_commit`; it must not substitute the target branch or silently switch
bases.

When supplied, preserve `delivery_run=<id>` and its canonical Delivery run path
in task Review/repair packets and receipts, including caller-invoked Converge
handoffs. For a sliced invocation, the Feature workflow also passes the exact
`exploration=.specify/delivery/<id>/exploration.md`,
`slices=.specify/delivery/<id>/slices.md`, `slice_approval=approve`, and
`with_docs_sync=<true|false>` arguments. Preserve the documentation choice for
task-scope repairs and affected README refresh; never infer or re-enable it.
Never create a new report location or reset finding/attempt state on resume.

If either `runtime_stage` or `runtime_result` is supplied, require the canonical
`delivery_run` and read the installed
`.specify/extensions/delivery/templates/runtime.md` in full at the runtime
handoff. That central runtime contract, including its
`.specify/extensions/delivery/scripts/delivery_runtime.py` helper and local
`.specify/delivery/<delivery_run>/runtime/` state, owns runtime interpretation,
resume, locking, and bookkeeping. For an SD checkpoint, its native local
operational evidence is exactly
`.specify/delivery/<delivery_run>/runtime/core-handoff.md`; a current
`.specify/delivery/<delivery_run>/runtime/result-checkpoint.json` may be used
only to resolve that report reference. Keep `runtime/` local/ignored and do not
stage the handoff. Apply the runtime contract exactly; do not invent a runtime
CLI or duplicate its state schema. Owner-stage transport is optional only for a
standalone call without a Delivery run. An SD Feature invocation with
`delivery_run` must use the task-close transport even when `runtime_stage` and
`runtime_result` are absent on Ralph itself; those stage arguments are supplied
to its nested Quality/Standards/Review owners. Consume the existing run rather
than initializing a replacement.

If `slices=<path>` is present, read the installed
`.specify/extensions/ralph/templates/slice-execution.md` in full. That packaged
template is the sole detailed owner of slice path/approval, branch,
boundary-check, and slice receipt execution. A missing template or an unreadable
canonical slice plan is a blocker; do not proceed to preflight, task selection,
Quality Brief, or editing. If `slices` is absent, preserve the existing
non-sliced sequence below.

## Sliced invocation gate

Apply the packaged template's sliced sequence before the preflight below. In
particular, a sliced invocation must use the exact
`.specify/delivery/<delivery_run>/slices.md` under the supplied run id, require
`SLICE_APPROVAL: approved` plus the unchanged approved mode/snapshot, and accept
only `single`, `stacked`, or `integration`. `tasks.md` remains the sole queue.
`single` keeps the ordinary feature branch; `stacked` and `integration` use the
configured `branch_prefix` plus the feature and slice id, with the declared
bases and the checkpoint's verified planning baseline defined by the template.
A failed or unknown boundary check stops before the next slice; only its
recorded receipt, completed receipt-persistence transition, clean preflight,
and `SLICE_READY: <slice-id>` permit continuation.

## Preconditions and safety

The following preflight is a mandatory control-flow gate, not a suggestion.
The active orchestrator must execute it on every invocation, including resume
runs, before selecting a task, creating a worker packet, invoking a quality
brief, or editing any file.

1. Locate the active Feature and its `tasks.md` only far enough to resolve the
   Feature slug. For a sliced invocation, use the exact run and slice paths and
   resolve the current slice before selecting a task. Do not parse the full task
   queue until this preflight gate succeeds.
2. Resolve receipt identity before reading or writing a task result. With
   `delivery_run=<safe-id>`, use exactly
   `.specify/delivery/<delivery_run>/task-verdicts.yml` and, when sliced,
   `.specify/delivery/<delivery_run>/slice-verdicts.yml`; reject any
   Feature-derived receipt path. Without a run, allow only a non-sliced legacy
   standalone Feature with an explicit `feature=<safe-id>` mapping and a
   matching unambiguous active-Feature record, using the legacy Feature receipt
   path described by `.specify/extensions/delivery/templates/core-adapter.md`.
   A bare branch, directory scan, newest record, or inferred Feature is not a
   mapping. A sliced invocation without `delivery_run` is a blocker.
3. For an SD Feature invocation (`lane=feature` or a supplied Core-stage
   context), read exactly
   `.specify/delivery/<delivery_run>/runtime/core-handoff.md`, or read the
   current `.specify/delivery/<delivery_run>/runtime/result-checkpoint.json`
   only to resolve its report reference to that exact file. Verify the
   `SD_CORE_HANDOFF: PASS` planning-to-execution checkpoint from that handoff
   and the installed `.specify/extensions/delivery/templates/core-adapter.md`.
   Verify its current `planning_commit`, `execution_base`, exact approved paths
   and producing owners/native-output manifest, task IDs/order, target/slice
   base and prefix, and branch identity against Git and the artifacts before
   task selection. For tracked planning paths, `planning_commit` must be a
   concrete SHA and an ancestor of `execution_base`; for explicitly
   ephemeral/ignored planning artifacts, `planning_commit: none` is accepted only
   with the project's recorded authorization, `execution_base` equal to the
   verified base HEAD, and the bound artifact identities unchanged. Do not infer
   a stage or create a planning commit inside Ralph. Keep `runtime/`
   local/ignored and do not stage the handoff. If the evidence is missing, stale,
   mismatched, or tracked planning paths are dirty without project Git
   authorization, stop with the exact paths and the adapter's concrete recovery;
   do not relabel the dirty entry as execution-ready.
4. Confirm that the project is a Git worktree and that `git` is available.
5. Run `git status --short --untracked-files=all`. If the worktree is dirty,
   report the exact paths and stop. Ignore only declared run operational records
   under `.specify/delivery/<delivery_run>/` (`runtime/`, `reviews/`, `receipts/`,
   `task-verdicts.yml`, `slice-verdicts.yml`, `evidence.md`,
   `pull-request*.md`) and Spec Kit's `.specify/workflows/runs/` ledger; they may
   remain local or be committed separately under artifact policy. Any source,
   Spec/Plan/Tasks, test, policy, config, or other dirty path blocks. Never stash,
   reset, clean, discard, or stage changes that existed before this run, and never
   use a dirty-worktree bypass for execution-relevant files.
6. Resolve the Feature slug and exact branch from the checkpoint/template's
   configured `branch_prefix` (the default is `ralph/`). Without slices, or for
   `single`, the target is `<branch_prefix><feature-slug>`. For `stacked` or
   `integration`, use the current slice branch
   `<branch_prefix><feature-slug>/<slice-id>`. If the target branch is current,
   reuse it only after proving that its HEAD contains the checkpoint's
   `planning_commit` and verified `execution_base`. If an existing target branch
   is not current, inspect that ref first and switch to it only when the same
   containment and declared-base checks pass; otherwise block it as wrong-base.
   If the exact branch does not exist, create it from that exact verified
   `execution_base`. Never substitute the target, a previous slice, or the
   integration branch merely because it is convenient. Preserve the declared
   slice base and prefix policy, and never silently switch away from unrelated
   uncommitted work.
7. Immediately verify and record `git branch --show-current`, the starting
   `HEAD`, the checkpoint's `planning_commit` and `execution_base`, the native
   manifest identity, the baseline path set, and (when sliced) the slice, mode,
   prefix, and approved base. Re-run the adapter's ancestry and artifact
   identity checks after the branch switch/create. The recorded branch and base
   must equal the resolved Ralph target and slice plan. These are the boundaries
   for every task result and commit.

Do not proceed to task selection until the branch switch/create command, the
planning-commit transfer checks, and their verification output have completed.
Stating that a branch “will be” created is not sufficient. If the target branch
cannot be created or reused at the verified execution base, stop with the exact
expected/observed SHAs and the adapter's concrete recovery; make no task edits,
cherry-picks, source copies, rebases, or resets.

If the host cannot provide Git or cannot create the target branch safely, stop
with an exact blocker. Do not claim task completion without a task commit.

## Required governance reporting

After the preflight succeeds and before selecting a task, emit a concise run
summary. Use the relevant excerpts and source paths; do not dump every project
policy in full. The summary must include:

```text
RALPH_RUN_PREFLIGHT: PASS
feature: <feature-slug>
delivery_run: <id or none>
receipt_root: <.specify/delivery/<delivery_run> or explicit legacy Feature mapping>
core_stage: <initial | converge | simplify | outgoing-repair | standalone>
planning_checkpoint: <SD_CORE_HANDOFF identity and status>
core_handoff_evidence: <exact .specify/.../runtime/core-handoff.md or current checkpoint report reference>
mode: <non-sliced | single | stacked | integration>
slice: <slice-id or none>
branch: <active-ralph-branch>
target_head: <approved target SHA or declared integration base>
base_head: <declared approved base SHA>
planning_commit: <approved planning baseline SHA>
execution_base: <verified branch creation/reuse SHA>
native_output_manifest: <exact manifest identity and owners>
policy_sources: <Constitution, applicable ADRs, quality profile, standards rules>
required_closure_verdicts: QUALITY_VERDICT=pass; STANDARDS_VERDICT=pass; REVIEW_VERDICT=pass
stop_conditions: <dirty baseline, stale approval, missing check, blocked verdict, unsafe scope, commit failure>
```

Do not emit `RALPH_RUN_PREFLIGHT: PASS` until the receipt identity, exact local
Core handoff evidence or its current checkpoint-result reference, the
`SD_CORE_HANDOFF: PASS` status, all required planning-commit/path/branch/base
checks, exact planning-commit transfer, branch switch/create command,
post-branch manifest/ancestry checks, and baseline commands have actually
completed. If a policy source or required quality profile cannot be located,
report it as a blocker instead of silently applying generic rules.

## One-task iteration

Repeat the following sequence until every task is complete, a blocker holds
the remaining dependency graph, or the configured iteration limit is reached:

1. Re-read `tasks.md`, `spec.md`, `plan.md`, Constitution, applicable ADRs,
   and the exact task receipt resolved during preflight. Treat shared files,
   shared public contracts, migrations, unresolved design decisions, and a
   changed planning/slice fingerprint as blocking edges even when a task is
   marked `[P]`. `tasks.md` remains the sole queue.
2. Select exactly one dependency-ready incomplete task. Prefer the first ready
   task in task-file order, then the lowest explicit priority number. Do not
   bundle unrelated tasks, silently merge task IDs, reorder the queue, or start
   another task in parallel.
3. Before implementation, emit a `RALPH_TASK_PACKET` containing the exact
   TaskID as written in `tasks.md`, its task-file position and dependencies,
   acceptance outcome, allowed paths, applicable code style and architecture
   rules, relevant Spec/Plan/ADR excerpts, the vertical-task boundary, the
   project's risk-based test expectation, the meaningful checks required for a
   green closure, `docs_refresh_required` (true when the task changes a package
   root, manifest, or README-affecting public surface, or a review repair
   requires it; otherwise false with a reason), and the current
   `DOCS_REFRESH` receipt or `not-applicable` reason. A task is an independently
   verifiable reviewable green commit, not a TDD-only step; setup, red/green,
   and related docs belong together when needed for that outcome. Do not
   silently repair a generated task breakdown in this packet. Invoke
   `speckit.quality.brief` for the task's target paths and scope, including the
   supplied `delivery_run` and exact exploration/plan reference when present,
   and include its result in the packet. A brief is advisory context; it does
   not replace the closure checks.

   For an SD run, before editing execute the central runtime's `task-start`
   using the selected Task ID, the explicit approved execution branch, and
   repeated `--input <allowed-path>` arguments. Follow the task-close transport
   section in `.specify/extensions/delivery/templates/runtime.md`; it owns the
   machine record schema. A wrong branch, dirty entry, duplicate occurrence, or
   unfinished earlier task stops selection before any source edit.
4. Implement only that task. A delegated worker reports changed paths,
   commands, results, residual risk, and blockers; it does not edit the task
   checkbox and does not create the closure commit. If a tracked progress file
   is configured, include its exact path in the task packet/allowed paths and
   append the iteration intent, Task ID and planned commit subject before the
   checks and owner snapshots. Do not append to it after the task gate.
5. Run the task's stated, meaningful project checks according to its risk and
    invoke both `speckit.quality.check` and `speckit.review.standards` for the
    same task scope. Then invoke `speckit.review.run scope=task task=<id>`
    using the installed `.specify/extensions/review/templates/reviewer.md`
    contract. Hand an independent reviewer the task brief/global constraints,
    approved exploration/Spec/Plan/ADRs, actual diff/caller context, test
    evidence, and prior finding state; do not send the whole implementation
    conversation. Capture all three verdicts against current HEAD plus
    content/requirements fingerprints, including staged, unstaged, and relevant
    untracked files. Tests/standards success does not replace the
    six-dimensional task review, and a TDD ordering claim does not replace a
    green task check.

    In an SD run, transport each owner result through `begin`/`record` with
    runtime scope `task-<TaskID>` as defined by the central runtime contract.
    Use `delivery_runtime.py owner-result` with the native report and a stage
    data JSON to generate the machine receipt and normalized result instead of
    hand-writing their identity fields; add `--record-result` only when no
    adjacent workflow `record` step exists. Preserve immutable native report/
    check paths per task and ticket. Final `outgoing-diff` reports cannot stand
    in for a task's pre-commit passes.

    For confirmed blockers, invoke `speckit.delivery.review-fix` with
    `lane=feature scope=task task=<id>`, the supplied `delivery_run`, exact
    `exploration`/`slices` paths, and `with_docs_sync` value (when supplied) to
    dispatch a bounded repair of this same open task, not recursive Ralph.
    Refresh affected checks and independently re-review the repaired task,
    preserving finding IDs and the configured
    `max_review_fix_rounds` budget across resume. Carry a returned
    `DOCS_REFRESH_REQUIRED`/`DOCS_REFRESH` into the task packet/receipt before the
    closure gate. Missing evidence/coverage calls for investigation, not
    speculative repairs. At cap exhaustion, blocked or
    incomplete review, stale snapshot, unsafe scope, or missing tools, leave the
    task open. The fixer cannot waive blockers or mark its own findings resolved.
6. Before changing the task checkbox, run and report this closure checklist:
   - the exact TaskID is still the selected item from `tasks.md`, with its
     approved task-file position, dependencies, and allowed paths unchanged;
   - the task is one independently verifiable, reviewable vertical outcome and
     green commit, not a silently merged setup/red/green/docs sequence or a
     TDD-only step;
   - the task acceptance criteria are evidenced;
   - every task-declared check passed and every project risk-based check required
     for the changed surface was run with meaningful results;
   - `QUALITY_VERDICT: pass` includes original per-check execution receipts for
     the current contents/configuration, task scope, and HEAD; do not stamp a
     reused old result with today's checkout fingerprint to imply it checked it;
   - `STANDARDS_VERDICT: pass` matches current contents, policy inputs, scope, and HEAD;
   - `REVIEW_VERDICT: pass` covers all six dimensions, current task content and
     requirements, accounted-for prior findings, and actual reviewer independence
     (or the user's recorded acceptance of self-review degradation);
   - `HEAD` is unchanged since the task started;
   - every changed path is within the task's allowed scope;
   - when `docs_refresh_required` is true, a current non-blocked `DOCS_REFRESH`
     covers the combined task contents; otherwise an explicit `not-applicable`
     reason is present; and
   - no required check, policy source, or tool is missing or unavailable.

   For an SD run, invoke runtime `task-gate --task <TaskID> --file
   <run>/runtime/docs-refresh-<TaskID>.json` before emitting PASS. The central
   contract defines this explicit docs-refresh applicability record and checks
   current task-scoped Quality/Standards/Review against the unchanged branch,
   HEAD, queue, allowed paths, and reviewed Git tree.

   Emit `RALPH_TASK_GATE: PASS` only when every item and the machine gate pass.
   This gate is separate from the advisory Quality Brief and is mandatory before `[X]`.
7. If the task gate is not `PASS`, persist the blocker, leave `[ ]` unchanged,
   and stop or continue only with another independent ready task. Never commit
   a failed task as complete.
8. If the task gate passes, verify the diff contains only the task's allowed
   paths plus declared task-state files. Update the matching task to `[X]` and
   persist the Quality, Standards, Review, and applicable DOCS_REFRESH
   references/fingerprints in the exact task receipt resolved during preflight:
   `.specify/delivery/<delivery_run>/task-verdicts.yml` when a run is supplied,
   or the explicitly mapped legacy standalone Feature path only when no run is
   supplied. Never use a Feature-derived path when `delivery_run` is present.
9. Keep the already-reviewed progress file unchanged. Only the selected
   checkbox and declared run receipt bookkeeping may change after the gate;
   resulting commit/check details belong in local runtime association state.
   Do not stage coordinator/runtime bookkeeping; it remains local under the
   run's runtime area.
10. Immediately stop task work and stage only the verified task paths plus the
    declared task-state/progress files. Do not select the next task, dispatch
    another worker, or make unrelated edits before committing. Never use
    `git add -A`, `git add .`, or a broad wildcard. Execute the equivalent of:

   ```sh
   git add -- <verified-task-path> <task-state-path> [<progress-path>]
   git diff --cached --check
   git commit -m "feat(ralph): <task-id> - <task-title>"
   ```

11. Verify that `HEAD` advanced from the task's pre-commit `HEAD`, the commit
    contains the task result and `[X]`/receipt state, and the worktree is clean of
    execution-relevant paths using the equivalent of `git show --stat HEAD` and
    `git status --short --untracked-files=all`; only the declared run operational
    records from the preflight exception may remain local. Record the resulting commit SHA
    against the canonical run-scoped task receipt, or the explicitly mapped
    legacy receipt only when no run was supplied. If the association is
    coordinator bookkeeping, write it to the local run runtime state and do not
    modify tracked task state after the clean commit. If commit or verification
    fails, reopen the task as `[ ]`, leave it uncommitted, and report the exact
    recovery blocker.

    The pre-commit review receipt must remain identified as such. Associate it
    with the resulting commit only after verifying identical reviewed production
    contents and requirement inputs; only declared checkbox/receipt/progress
    bookkeeping may differ. Do not relabel an old review as a review of new code.
    Evidence-only records must not create tracked post-commit dirtiness. A
    Feature run with `delivery_run` must not write this association under a
    Feature-derived path.

    For an SD run, execute runtime `task-record --task <TaskID> --commit <SHA>`
    before selecting another task. It associates the preserved pre-commit
    owner receipts only after checking the actual commit parent, reviewed Git
    blobs/modes, selected checkbox transition, and clean execution worktree.
    A failed association leaves the task unclosed and requires recovery.

After a successful commit, begin the next iteration with fresh task focus and
re-read all durable artifacts. A task is not complete merely because source
files changed or tests passed; it is complete only after its Git commit and
receipt exist. When the commit completes the current approved slice, stop before
selecting any task from another slice and apply the slice-boundary protocol
in `.specify/extensions/ralph/templates/slice-execution.md`. That protocol
owns the authorization-aware persistence transition for a tracked
`slice-verdicts.yml`: if it needs a post-task coordinator commit, that commit
must contain only the exact run receipt, remain separate from the task closure
commit, preserve the checks' original execution identity, and be followed by a
clean-worktree verification. Continue only after its classification-specific
evidence and receipt transition are complete under the exact
`.specify/delivery/<delivery_run>/slice-verdicts.yml` and it emits
`SLICE_READY: <slice-id>`. A failed, stale, unknown, unauthorized, or dirty
boundary stops the run and never advances to the next slice; a non-sliced
invocation has no such handoff.

## Completion

For an SD run, run the runtime helper's `require --kind task-closure` before
claiming completion. Missing task records, stale/tampered native evidence,
unreachable or mismatched task commits, and checkbox-only completion block
`ALL_TASKS_DONE`. Workflow repeats this read-only audit after Ralph and before
Evidence so a missing internal helper call cannot silently pass downstream.

When no incomplete task remains, verify that every task has a passing
snapshot-bound receipt associated with its verified commit in the canonical
run-scoped `task-verdicts.yml`, or in the explicitly mapped legacy standalone
Feature receipt only when no run was supplied. The active branch must be the
Ralph branch and the worktree must be clean. Never substitute a Feature-derived
receipt when `delivery_run` is present. For a sliced invocation, also verify
that every approved slice has a passing receipt under the exact Delivery
run's `slice-verdicts.yml`, with the required target-prefix, flag, or
integration evidence and `SLICE_READY` recorded.
Earlier task receipts are not relabeled as reviews of the final HEAD; the later
outgoing-diff review owns cross-task integration coverage. In an SD Feature run,
this completion is the implementation-run result consumed by Core Converge; do
not invoke Core Implement or Converge from inside this command. Only then emit
this exact machine-readable signal:

```text
<promise>ALL_TASKS_DONE</promise>
```

If incomplete tasks remain but none is dependency-ready, report the blocking
task ids and downstream tasks held by them. Do not emit the completion signal.
The command also stops without completion when the configured iteration limit
is reached. Ralph never creates, pushes, or merges a PR and never mutates a
remote; Delivery Handoff and the separately authorized PR outcome own those
transitions.
