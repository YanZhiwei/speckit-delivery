# Ralph slice execution

This is the detailed slice-boundary contract for the installed Ralph command.
When `speckit.ralph.run` receives `slices=<path>`, it must read this file before
preflight and apply the sequence below. The command remains the execution owner;
this template adds no runtime, extension, or state engine. Existing Delivery run
workspace receipts are the only durable execution records.

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
2. Read the exact run packet, approved Spec/Plan, `tasks.md`, the Delivery
   configuration, and the installed Delivery slice contract. Resolve one active
   Feature from those artifacts; ambiguity or a run collision blocks execution.
3. Require the actual gate choice (`approve`, or the persisted equivalent
   `approved`) and a canonical approval record with `SLICE_APPROVAL: approved`.
   Verify the plan's `Approved mode / snapshot` and baseline still match the
   current plan, requirements, policy inputs, task mapping, and relevant
   working-tree contents. A missing, changed, stale, or context-only approval
   blocks direct execution; do not replace a fingerprint to make it fit.
4. Read the plan's approved `Merge mode` and accept only `single`, `stacked`, or
   `integration`. `undecided`, an unknown slice classification, an incomplete
   task map, or a task mapped to more than one slice blocks execution; every
   `tasks.md` task must be mapped exactly once. A `single` plan has one slice and
   uses the ordinary Ralph branch/queue contract.

When `slices` is absent, preserve the existing non-sliced Ralph behavior: the
ordinary feature branch, the active Feature's `tasks.md`, one ready task per
iteration, task-scoped Quality/Standards/Review, and per-task commits. Do not
invent a slice plan or receipt for that path.

## Slice branch and clean preflight

Before selecting a task, and again before every new slice, require a clean Git
worktree. Record the current branch, starting `HEAD`, relevant baseline paths,
and the approved slice base. Never stash, reset, clean, or stage pre-existing
changes; never silently switch away from unrelated work.

Resolve `branch_prefix` from the Ralph configuration, defaulting to `ralph/`,
and compose branches as follows:

- no slice or `single`: `<branch_prefix><feature-slug>`;
- `stacked`: `<branch_prefix><feature-slug>/<slice-id>`;
- `integration`: `<branch_prefix><feature-slug>/<slice-id>`.

Use the target branch named by the slice plan. The first stacked slice starts
from that target; each later stacked slice starts from the previous slice's
verified `HEAD`. An integration slice starts from the declared integration
branch, never from the target merely because it is convenient. Create or reuse
the exact branch only after the clean check, then verify the active branch and
base SHA. A branch that exists with the wrong base is a blocker, not permission
to rebase or reset it.

For `single`, keep the existing ordinary feature branch and target-base behavior;
do not add a slice suffix. For every sliced mode, record the selected slice,
mode, branch, base, and approved snapshot before task selection.

## Queue and task sequence

`slices.md` supplies boundaries only. `tasks.md` is the sole queue and remains
the sole source of task identifiers, dependencies, order, acceptance criteria,
paths, and verification instructions. Never add, remove, reorder, or synthesize
a task because a slice needs one. A task spanning slices, a task missing from
the approved map, or an appended task not assigned to an existing approved slice
blocks and returns to task/slice planning.

Within the current slice, repeatedly use the command's normal one-task sequence:

1. Re-read the Spec/Plan/ADR context, task receipts, and `tasks.md`.
2. Select exactly one incomplete dependency-ready task mapped to this slice,
   preferring task-file order and then the explicit priority. Tasks belonging to
   a later slice wait; do not select them early.
3. Emit the normal task packet, including `docs_refresh_required` and the
   current `DOCS_REFRESH` receipt or reason, run the Quality Brief, and implement
   only that task. The worker does not edit `[ ]` or create the closure commit.
4. Run the task checks, `speckit.quality.check`, `speckit.review.standards`, and
   independent `speckit.review.run scope=task task=<id>`. Preserve the existing
   review-fix budget and finding IDs; a fixer cannot self-approve a finding.
5. Require the existing `RALPH_TASK_GATE: PASS`, including acceptance evidence,
   current Quality/Standards/Review passes, six-dimensional review coverage,
   unchanged content/requirements snapshot, unchanged task-start `HEAD`, allowed
   paths, a current non-blocked `DOCS_REFRESH` when required (otherwise an explicit
   not-applicable reason), and available policy/check tools.
6. Only then mark `[X]`, persist the task receipt including applicable
   `DOCS_REFRESH`, stage only verified task and declared state paths, create
   exactly the existing per-task commit, and verify the new `HEAD` and a clean
   worktree.

If the current slice still has incomplete tasks, begin another iteration only
from that clean committed state. If its tasks are complete, stop task selection
and execute the boundary below before considering any later slice.

The configured Ralph iteration/retry limits and Delivery review-repair budget
remain in force. Slice handling does not create another closure loop or waive
Quality, Standards, independent six-dimensional Review, task receipts, or
per-task Git semantics.

## Slice boundary verification

Run this only after every task mapped to the current slice has a passing,
commit-associated task receipt and the worktree is clean. Re-read the canonical
slice plan and approval before checking it; a changed plan or snapshot blocks.

- `standalone`: use an isolated temporary worktree or throwaway branch from the
  target, apply the approved cumulative `target..current-slice HEAD` commit range
  (all lower verified slices, not only the current slice), and run the exact
  declared target-branch build/test commands. Record the base, head, and commit
  set. A failed check is
  `SLICE_PREFIX_CHECK: blocked`; write the blocked receipt, do not emit
  `SLICE_READY`, and return to slice planning for reclassification or a real
  flag/abstraction.
- `flagged`: verify the named flag, its default and kill switch, flag-off
  behavior, the flag-off regression test, and then the flag-on path. Missing or
  failed flag evidence blocks; do not infer safety from a passing task review.
- `integration-only`: run the exact declared checkpoints on the integration
  branch and record their results. Do not claim target-branch prefix safety.
- `unknown`: block. An approved execution mode may not continue with unknown
  boundary evidence.

Write or update the existing run workspace receipt at
`.specify/delivery/<delivery_run>/slice-verdicts.yml`, honoring `artifact_policy`.
The receipt records the slice id, approved mode, base and verified head, mapped
task IDs, classification-specific checks/results, merge mode, and verdict. A
successful boundary emits exactly `SLICE_READY: <slice-id>`. Select a later
slice only after that signal and a fresh clean branch preflight. A failed,
missing, stale, or unknown check never permits the next slice, and
`ALL_TASKS_DONE` is valid only when every task is closed and every slice receipt
is ready.

Ralph does not create, push, or merge a PR, mutate a remote, or silently extend
the approved slice plan. Handoff and the separately authorized PR outcome own
those transitions.
