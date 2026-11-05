# Ralph slice execution

This file is installed at `.specify/extensions/ralph/templates/slice-execution.md`
and is the detailed slice-boundary contract for the installed
`.specify/extensions/ralph/commands/speckit.ralph.run.md` command. When that
command receives `slices=<path>`, it must read this file in full before preflight
and apply the sequence below. The command remains the execution owner; this
template adds no runtime, extension, or state engine. The Delivery Slice command
owns derivation and validation of internal boundaries, execution mode,
publication mode, and publication groups; this template enforces the approved
snapshot.

For an SD Feature handoff, also read the installed
`.specify/extensions/delivery/templates/core-adapter.md` in full. It owns the
Core Tasks/Analyze/Converge adaptation, task shape, planning-to-execution
checkpoint, and canonical receipt identity. Refer to the installed Reviewer
contract at `.specify/extensions/review/templates/reviewer.md` for independence,
coverage, and finding policy; do not copy that policy here.

If `runtime_stage` or `runtime_result` is supplied, require the canonical
`delivery_run` and read the installed
`.specify/extensions/delivery/templates/runtime.md` in full. That central
contract owns the `.specify/extensions/delivery/scripts/delivery_runtime.py`
helper and local `.specify/delivery/<delivery_run>/runtime/` operational state.
For an SD checkpoint, read exactly
`.specify/delivery/<delivery_run>/runtime/core-handoff.md`, or use the current
`.specify/delivery/<delivery_run>/runtime/result-checkpoint.json` only to resolve
its report reference to that exact handoff file. Keep `runtime/` local/ignored;
do not stage the handoff. Apply the runtime contract's exact hook/result
contract without inventing a CLI or duplicating its state schema. With neither
runtime argument, do not create runtime state here.

Existing Delivery run workspace receipts remain the durable execution records;
coordinator-only runtime bookkeeping stays local and is never staged as a task
or planning change.

## Resolve the sliced invocation

The Feature workflow passes these control arguments:

- `delivery_run=<id>` — the user-assigned safe run id;
- `exploration=<path>` — the exact canonical exploration packet;
- `slices=<path>` — the exact canonical slice plan; and
- `slice_approval=approve` — the actual workflow gate choice.

For a sliced invocation:

1. Validate `delivery_run` as one safe path segment matching
   `[A-Za-z0-9][A-Za-z0-9._-]*`, then use only
   `.specify/delivery/<delivery_run>/` as the run root. Require `slices` to be
   exactly `.specify/delivery/<delivery_run>/slices.md`; when `exploration` is
   supplied, require the matching `.specify/delivery/<delivery_run>/exploration.md`.
   Do not fall back to a Feature-derived or most-recent run path.
2. Resolve the canonical receipts before task selection: use exactly
   `.specify/delivery/<delivery_run>/task-verdicts.yml` and
   `.specify/delivery/<delivery_run>/slice-verdicts.yml`. A sliced invocation
   never uses the legacy standalone Feature mapping, and no receipt may leak a
   Feature-derived path when this run id is supplied.
3. Read exactly
   `.specify/delivery/<delivery_run>/runtime/core-handoff.md`, or read the
   current `.specify/delivery/<delivery_run>/runtime/result-checkpoint.json`
   only to resolve its report reference to that exact file. Verify
   `SD_CORE_HANDOFF: PASS` from that handoff and the installed
   `.specify/extensions/delivery/templates/core-adapter.md`. Before task
   selection, verify the current `planning_commit`, `execution_base`, exact
   approved paths and producing owners/native-output manifest, task IDs/order,
   target/slice base and prefix, and branch identity against Git and the
   artifacts. Missing or stale handoff evidence, missing authorization, changed
   input, missing planning baseline, or a branch that does not contain that
   baseline blocks with the adapter's concrete recovery. Keep `runtime/`
   local/ignored and do not stage the handoff; do not create a planning commit,
   restamp a fingerprint, cherry-pick/copy source changes, or bypass clean Git
   in this execution command.
4. Read the exact run packet, approved Spec/Plan, `tasks.md`, the Delivery
   configuration, and the installed Delivery slice contract. Resolve one active
   Feature from those artifacts; ambiguity or a run collision blocks execution.
5. Require the actual gate choice (`approve`, or the persisted equivalent
   `approved`) and a canonical approval record with `SLICE_APPROVAL: approved`.
   Verify the plan's `Approved mode / snapshot` and baseline still match the
   current plan, requirements, policy inputs, task mapping, and relevant
   working-tree contents. A missing, changed, stale, or context-only approval
   blocks direct execution; do not replace a fingerprint to make it fit.
6. Read the plan's approved `Execution mode` and `Publication mode` (accept
   `Merge mode` only as the legacy execution-mode alias) and accept only
   `single`, `stacked`, or `integration` for each. If the legacy alias is
   present, it must equal `Execution mode`; do not choose between conflicting
   fields. Both modes, the requested `pr_slicing` value, and the complete
   publication-group map must be present in the approved snapshot; `undecided`,
   an unknown slice classification, an
   incomplete task map, or a task mapped to more than one slice blocks
   execution. A `single` plan may contain one or more internal review slices,
   but all use the ordinary Ralph branch/queue contract and one approved
   publication group. Do not infer remote PR count from slice count or amend the
   grouping at final handoff.

When `slices` is absent, preserve the existing non-sliced Ralph behavior: the
ordinary feature branch, the active Feature's `tasks.md`, one ready task per
iteration, task-scoped Quality/Standards/Review, and per-task commits. Do not
invent a slice plan or receipt for that path.

## Slice branch and clean preflight

Before selecting a task, and again before every new slice, require a clean Git
worktree and re-verify the current planning-to-execution checkpoint from
`.specify/extensions/delivery/templates/core-adapter.md`. Apply the command's
declared operational-record exception: only `.specify/delivery/<delivery_run>/`
runtime/review/receipt/verdict/evidence/PR-body records and
`.specify/workflows/runs/` may remain dirty/local; any source, Spec/Plan/Tasks,
test, policy, or unrelated path blocks. Record the current
branch, starting `HEAD`, `planning_commit`, `execution_base`, relevant baseline
paths, approved paths, declared prefix, and approved slice base. Re-run the
adapter's ancestry and native-output identity checks after any branch
create/reuse. Never stash, reset, clean, or stage pre-existing changes; never
silently switch away from unrelated work. A checkpoint does not waive this
clean-entry gate.

Resolve `branch_prefix` from the Ralph configuration, defaulting to `ralph/`,
and compose branches as follows:

- no slice or `single`: `<branch_prefix><feature-slug>`;
- `stacked`: `<branch_prefix><feature-slug>/<slice-id>`;
- `integration`: `<branch_prefix><feature-slug>/<slice-id>`.

Preserve the target/integration branch and the exact `branch_prefix` declared by
the slice plan. The first stacked slice has the approved target as its declared
base; each later stacked slice has the previous verified slice `HEAD` as its
declared base. An integration slice has the declared integration-branch `HEAD`,
never the target merely because it is convenient. The Core adapter's
`planning_commit` must be carried into the chosen `execution_base`; the
execution branch may be seeded from that planning HEAD only when the declared
base/target ancestry was verified. A later branch may use a receipt-only
coordinator descendant described below, but it must still contain the same
planning baseline and declared code base.

After the clean check, inspect an existing branch ref before switching and
reuse it only when its prefix, declared base, `execution_base`, planning
ancestry, and native-output identity pass. If the exact branch does not exist,
create it from the verified `execution_base`; do not switch to an existing
wrong-base branch. A wrong base is a blocker, not permission to rebase, reset,
merge a convenient target, cherry-pick, or copy planning/source changes. Report
the exact expected and observed SHAs and recover by rerunning the adapter
checkpoint after the project owner authorizes the exact branch creation/reuse
from the approved planning baseline. Do not advance to a slice task while that
blocker holds.

For `single`, keep the existing ordinary feature branch and target-base behavior;
do not add a slice suffix, even when the approved plan has multiple internal
review slices, and still require the planning baseline transfer. Execute those
slices sequentially on that branch and stop at each approved boundary; a single
branch does not remove per-slice classification or checkpoint evidence. For
every sliced mode, record the selected slice, execution mode, publication mode,
publication group, prefix, branch, declared base, execution base, planning
commit, and approved snapshot before task selection. Publication remains
pending separate user authorization.

## Queue and task sequence

`slices.md` supplies boundaries only. `tasks.md` is the sole queue and remains
the sole source of task identifiers, dependencies, order, acceptance criteria,
paths, and verification instructions. Every selected task must be one
independently verifiable, reviewable green commit; it is not a TDD-only step.
Setup, red/green behavior checks, implementation, and related docs may stay in
one vertical task when that is what makes the outcome independently reviewable.
Use the project's risk-based testing policy and meaningful checks for the
changed surface. Execute every applicable assembly, concurrency, or recovery
probe recorded for the current behavior-changing slice with its owning task;
the final rollup/outgoing review may confirm integration but cannot substitute
for that probe. The full probe assignment and validation rule lives in the
[Delivery Slice command](../../delivery/commands/speckit.delivery.slice.md); do
not copy or weaken it here. Never add, remove,
reorder, silently merge, or synthesize a task because a slice needs one. A task
spanning slices, a task missing from the approved map, or an appended task not
assigned to an existing approved slice blocks and returns to the Core/Delivery
planning sequence. If Converge reports any `appendedTaskIDs`, even a task
assigned to an existing slice requires the adapter's renewed Delivery Slice
mapping, Analyze result, combined gate, approval writer, and planning
checkpoint; a same-slice label does not preserve stale approval.

Within the current slice, repeatedly use the command's normal one-task sequence:

1. Re-read the Spec/Plan/ADR context, the exact run-scoped task receipt,
   and `tasks.md`. Confirm that the approved task IDs/order and slice mapping
   have not changed since the planning checkpoint.
2. Select exactly one incomplete dependency-ready task mapped to this slice,
   preferring task-file order and then the explicit priority. Tasks belonging to
   a later slice wait; do not select them early, reorder them, or merge them
   with another TaskID.
3. Emit the normal task packet, including the exact TaskID and task-file
   position, the independently verifiable vertical outcome, project risk-based
   test expectation, `docs_refresh_required`, and the current `DOCS_REFRESH`
   receipt or reason. Run the Quality Brief and implement only that task. The
   worker does not edit `[ ]` or create the closure commit.
4. Run the task's meaningful checks, `speckit.quality.check`,
   `speckit.review.standards`, and independent
   `speckit.review.run scope=task task=<id>` using
   `.specify/extensions/review/templates/reviewer.md`. Preserve the existing
   review-fix budget and finding IDs; a fixer cannot self-approve a finding.
5. Require the existing `RALPH_TASK_GATE: PASS`, including the independently
   verifiable green task outcome, acceptance evidence, all project risk-based
   checks, current Quality/Standards/Review passes, six-dimensional review
   coverage, unchanged content/requirements snapshot, unchanged task-start
   `HEAD`, allowed paths, a current non-blocked `DOCS_REFRESH` when required
   (otherwise an explicit not-applicable reason), and available policy/check
   tools.
6. Only then mark `[X]`, persist the task receipt including applicable
   `DOCS_REFRESH` under the exact `.specify/delivery/<delivery_run>/task-verdicts.yml`,
   stage only verified task and declared state paths, create exactly the existing
   per-task commit, and verify the new `HEAD` and a clean execution-relevant
   worktree (declared run operational records excepted). Do not stage
   local runtime/coordinator bookkeeping.

If the current slice still has incomplete tasks, begin another iteration only
from that clean committed state. If its tasks are complete, stop task selection
and execute the boundary below before considering any later slice.

The configured Ralph iteration/retry limits and Delivery review-repair budget
remain in force. Slice handling does not create another closure loop or waive
Quality, Standards, independent six-dimensional Review, task receipts, or
per-task Git semantics.

## Slice boundary verification

Run this only after every task mapped to the current slice has a passing,
commit-associated task receipt and the worktree is clean of execution-relevant
paths (declared run operational records excepted). Re-read the canonical
slice plan and approval before checking it; a changed plan or snapshot blocks.

- `standalone`: use an isolated temporary worktree or throwaway branch from the
  slice plan's declared cumulative verification base (the target only when the
  plan declares it), apply all lower verified slice commits plus the current
  slice, and run the exact declared target-branch build/test commands. Preserve
  the planning baseline and declared prefix/base while selecting that range;
  never substitute the target for an integration base. Record the base, head,
  and commit set. A failed check is
  `SLICE_PREFIX_CHECK: blocked`; write the blocked receipt, do not emit
  `SLICE_READY`, and return to slice planning for reclassification or a real
  flag/abstraction.
- `flagged`: verify the named flag, its default and kill switch, flag-off
  behavior, the flag-off regression test, and then the flag-on path. Missing or
  failed flag evidence blocks; do not infer safety from a passing task review.
- `integration-only`: run the exact declared checkpoints against the declared
  integration branch and record their results, even when `Execution mode:
  single` keeps task execution on the ordinary Ralph branch. Do not claim
  target-branch prefix safety or silently replace the integration checkpoint
  with the ordinary branch's task checks.
- `unknown`: block. An approved execution mode may not continue with unknown
  boundary evidence.

### Receipt persistence and the next-slice transition

Write or update only the exact run workspace receipt at
`.specify/delivery/<delivery_run>/slice-verdicts.yml`, honoring the already
approved `artifact_policy`; never write a Feature-derived slice path when
`delivery_run` is supplied. Capture the task-commit `verified_head`, approved execution/publication modes,
publication group, and the original check execution identity (commands, inputs,
fingerprints, and evidence) before writing. A receipt write is
coordinator-owned boundary bookkeeping, not a change to the task outcome.

For `artifact_policy: tracked`, use this authorization-aware transition after
every boundary receipt, including a blocked receipt:

1. Require pre-existing project Git authorization for a coordinator receipt
   commit. Ralph may not create that authorization, alter ignore rules, or turn
   a tracked receipt into an ignored/local file to silence the clean check.
2. Write only the exact `.specify/delivery/<delivery_run>/slice-verdicts.yml`
   path. After the last task commit, stage only that path, run the staged
   whitespace check, and create a separate coordinator commit containing only
   that exact run receipt. This is not the task-closure commit and must not
   include source, tests, `tasks.md`, planning artifacts, or runtime state.
3. Verify that the receipt commit advanced `HEAD`, contains only the exact run
   receipt, and leaves `git status --short --untracked-files=all` free of
execution-relevant dirt (declared operational records excepted). Record
   the receipt's original `verified_head`/check identity and the separate
   receipt-commit association; never relabel the checks as if they executed on
   the receipt commit. A receipt-only commit may be the next branch's
   coordinator descendant, but it does not replace the declared code base or
   the original checked HEAD.

If pre-existing authorization is missing, report the exact receipt path and
required project decision and stop. The concrete recovery is for the project
owner to authorize the exact receipt-only commit or to rerun with an already
approved ephemeral artifact policy; do not stage a broader path, add an ignore,
reset, stash, or continue to another slice. An explicitly approved ephemeral
policy may use its existing project-local receipt projection, but Ralph must
not switch policies during the run and the native clean-worktree preflight still
runs before the next slice.

Only after the receipt persistence transition and clean verification may a
successful boundary emit exactly `SLICE_READY: <slice-id>` and select a later
slice after a fresh clean branch preflight. A failed, missing, stale, unknown,
unauthorized, or dirty boundary never permits the next slice, and
`ALL_TASKS_DONE` is valid only when every task is closed and every slice receipt
is ready. Coordinator/runtime bookkeeping remains in the local run runtime
area and is not appended to this receipt merely to record a transition.

Ralph does not create, push, or merge a PR, mutate a remote, or silently extend
the approved slice/publication plan. Handoff consumes the approved publication
groups, and the separately authorized PR outcome owns remote transitions.
