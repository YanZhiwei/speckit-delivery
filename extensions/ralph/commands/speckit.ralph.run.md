---
description: "Run Spec Kit tasks through a bounded Ralph loop with per-task Git commits"
---

# Spec Kit + Ralph bridge

## Input

```text
$ARGUMENTS
```

This command is the bridge between Spec Kit's structured artifacts and a
Ralph-style autonomous loop. It consumes the active feature's `tasks.md` and
executes exactly one dependency-ready task per iteration. The default portable
mode is sequential: do not dispatch parallel workers in the shared worktree.

When supplied, preserve `delivery_run=<id>` and its canonical Delivery run path
in task Review/repair packets and receipts, including nested converge invocations.
Never create a new report location or reset finding/attempt state on resume.

## Preconditions and safety

The following preflight is a mandatory control-flow gate, not a suggestion.
The active orchestrator must execute it on every invocation, including resume
runs, before selecting a task, creating a worker packet, invoking a quality
brief, or editing any file.

1. Locate the active feature and its `tasks.md` only far enough to resolve the
   feature slug. Do not select or start a task yet; parse the full task queue
   only after this preflight gate succeeds.
2. Confirm that the project is a Git worktree and that `git` is available.
3. Run `git status --short --untracked-files=all`. If the worktree is dirty,
   report the exact paths and stop. Never stash, reset, clean, or stage changes
   that existed before this run.
4. Resolve the feature slug and the target branch. By default it is
   `ralph/<feature-slug>`; use the configured `branch_prefix` when present.
   If the target branch is current, reuse it. Otherwise, with a clean
   worktree, switch to the existing branch or create it from the current
   `HEAD` using the equivalent of `git switch <target>` or
   `git switch -c <target>`. Never silently switch away from unrelated
   uncommitted work.
5. Immediately verify and record `git branch --show-current`, the starting
   `HEAD`, and the baseline path set. The recorded branch must equal the
   resolved Ralph target. These are
   the boundaries for every task result and commit.

Do not proceed to task selection until the branch switch/create command and
its verification output have completed. Stating that a branch “will be”
created is not sufficient. If the target branch cannot be created or reused,
stop with an exact blocker and make no task edits.

If the host cannot provide Git or cannot create the target branch safely, stop
with an exact blocker. Do not claim task completion without a task commit.

## Required governance reporting

After the preflight succeeds and before selecting a task, emit a concise run
summary. Use the relevant excerpts and source paths; do not dump every project
policy in full. The summary must include:

```text
RALPH_RUN_PREFLIGHT: PASS
feature: <feature-slug>
branch: <active-ralph-branch>
base_head: <starting-sha>
policy_sources: <Constitution, applicable ADRs, quality profile, standards rules>
required_closure_verdicts: QUALITY_VERDICT=pass; STANDARDS_VERDICT=pass; REVIEW_VERDICT=pass
stop_conditions: <dirty baseline, missing check, blocked verdict, unsafe scope, commit failure>
```

Do not emit `RALPH_RUN_PREFLIGHT: PASS` until the branch and baseline commands
have actually completed. If a policy source or required quality profile cannot
be located, report it as a blocker instead of silently applying generic rules.

## One-task iteration

Repeat the following sequence until every task is complete, a blocker holds
the remaining dependency graph, or the configured iteration limit is reached:

1. Re-read `tasks.md`, `spec.md`, `plan.md`, Constitution, applicable ADRs,
   and the task verdict receipt. Treat shared files, shared public contracts,
   migrations, and unresolved design decisions as blocking edges even when a
   task is marked `[P]`.
2. Select exactly one dependency-ready incomplete task. Prefer the first ready
   task in task-file order, then the lowest explicit priority number. Do not
   bundle unrelated tasks and do not start another task in parallel.
3. Before implementation, emit a `RALPH_TASK_PACKET` containing the selected
   task id, dependencies, acceptance criteria, allowed paths, applicable code
   style and architecture rules, relevant Spec/Plan/ADR excerpts, and the
   exact checks required for closure. Invoke `speckit.quality.brief` for the
   task's target paths and scope, and include its result in the packet. A
   brief is advisory context; it does not replace the closure checks.
4. Implement only that task. A delegated worker reports changed paths,
   commands, results, residual risk, and blockers; it does not edit the task
   checkbox and does not create the closure commit.
5. Run the task's stated checks and invoke both `speckit.quality.check` and
    `speckit.review.standards` for the same task scope. Then invoke
    `speckit.review.run scope=task task=<id>` using the installed Reviewer
    contract. Hand an independent reviewer the task brief/global constraints,
    approved exploration/Spec/Plan/ADRs, actual diff/caller context, test evidence,
    and prior finding state; do not send the whole implementation conversation.
    Capture all three verdicts against current HEAD plus content/requirements
    fingerprints, including staged, unstaged, and relevant untracked files.
    Tests/standards success does not replace the six-dimensional task review.

    For confirmed blockers, invoke `speckit.delivery.review-fix` with
    `lane=feature scope=task task=<id>` to dispatch a bounded repair of this same
    open task, not recursive Ralph. Refresh affected checks and independently
    re-review the repaired task, preserving finding IDs and the configured
    `max_review_fix_rounds` budget across resume. Missing evidence/coverage calls
    for investigation, not speculative repairs. At cap exhaustion, blocked or
    incomplete review, stale snapshot, unsafe scope, or missing tools, leave the
    task open. The fixer cannot waive blockers or mark its own findings resolved.
6. Before changing the task checkbox, run and report this closure checklist:
   - the task acceptance criteria are evidenced;
   - every task-declared check passed;
    - `QUALITY_VERDICT: pass` includes original per-check execution receipts for
      the current contents/configuration, task scope, and HEAD; do not stamp a
      reused old result with today's checkout fingerprint to imply it checked it;
    - `STANDARDS_VERDICT: pass` matches current contents, policy inputs, scope, and HEAD;
    - `REVIEW_VERDICT: pass` covers all six dimensions, current task content and
      requirements, accounted-for prior findings, and actual reviewer independence
      (or the user's recorded acceptance of self-review degradation);
   - `HEAD` is unchanged since the task started;
   - every changed path is within the task's allowed scope; and
   - no required check, policy source, or tool is missing or unavailable.

   Emit `RALPH_TASK_GATE: PASS` only when every item passes. This gate is
   separate from the advisory Quality Brief and is mandatory before `[X]`.
7. If the task gate is not `PASS`, persist the blocker, leave `[ ]` unchanged,
   and stop or continue only with another independent ready task. Never commit
   a failed task as complete.
8. If the task gate passes, verify the diff contains only the task's allowed
   paths plus declared task-state files. Update the matching task to `[X]` and
    persist the Quality, Standards, and Review report references/fingerprints in
   `.specify/delivery/<feature>/task-verdicts.yml`.
9. If a progress file is configured, append the concise iteration record now,
   including the task id, commit subject, changed paths, checks, and next task
   focus. Treat the checkbox, receipt, and progress writes as the final
   pre-commit state transition.
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
    contains the task result and `[X]`/receipt state, and the worktree is clean
    using the equivalent of `git show --stat HEAD` and
    `git status --short --untracked-files=all`. Record the resulting commit SHA
    in the local verdict receipt without modifying tracked task state after the
     clean commit. If commit or verification fails, reopen the task as `[ ]`,
     leave it uncommitted, and report the exact recovery blocker.

    The pre-commit review receipt must remain identified as such. Associate it
    with the resulting commit only after verifying identical reviewed production
    contents and requirement inputs; only declared checkbox/receipt/progress
    bookkeeping may differ. Do not relabel an old review as a review of new code.
    Evidence-only records must not create tracked post-commit dirtiness.

After a successful commit, begin the next iteration with fresh task focus and
re-read all durable artifacts. A task is not complete merely because source
files changed or tests passed; it is complete only after its Git commit and
receipt exist.

## Completion

When no incomplete task remains, verify that every task has a passing
snapshot-bound task receipt associated with its verified commit, the active
branch is the Ralph branch, and the worktree is clean. Earlier task receipts are
not relabeled as reviews of the final HEAD; the later outgoing-diff review owns
cross-task integration coverage. Only
then emit this exact machine-readable signal:

```text
<promise>ALL_TASKS_DONE</promise>
```

If incomplete tasks remain but none is dependency-ready, report the blocking
task ids and downstream tasks held by them. Do not emit the completion signal.
The command also stops without completion when the configured iteration limit
is reached.
