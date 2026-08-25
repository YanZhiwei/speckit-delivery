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

## Preconditions and safety

Before changing branches or files:

1. Locate the active feature and its `tasks.md`. Parse phases, `Txxx`
   identifiers, `[P]` markers, user-story labels, dependencies, file targets,
   acceptance criteria, and verification instructions.
2. Confirm that the project is a Git worktree and that `git` is available.
3. Run `git status --short --untracked-files=all`. If the worktree is dirty,
   report the exact paths and stop. Never stash, reset, clean, or stage changes
   that existed before this run.
4. Resolve the feature slug and the target branch. By default it is
   `ralph/<feature-slug>`; use the configured `branch_prefix` when present.
   If the target branch is current, reuse it. Otherwise, with a clean
   worktree, switch to the existing branch or create it from the current
   `HEAD`. Never silently switch away from unrelated uncommitted work.
5. Record the starting `HEAD`, branch name, and baseline path set. These are
   the boundaries for every task result and commit.

If the host cannot provide Git or cannot create the target branch safely, stop
with an exact blocker. Do not claim task completion without a task commit.

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
3. Invoke `speckit.quality.brief` for the task's target paths and scope. Include
   the returned Quality Brief, acceptance condition, allowed paths, relevant
   Spec/Plan/ADR excerpts, and expected checks in the worker packet.
4. Implement only that task. A delegated worker reports changed paths,
   commands, results, residual risk, and blockers; it does not edit the task
   checkbox and does not create the closure commit.
5. Run the task's stated checks and invoke both `speckit.quality.check` and
   `speckit.review.standards` for the same task scope. A missing configured
   check, unavailable required tool, stale `HEAD`, out-of-scope path, or
   blocked verdict leaves the task open.
6. If either verdict is not `pass`, persist the blocker, leave `[ ]` unchanged,
   and stop or continue only with another independent ready task. Never commit
   a failed task as complete.
7. If both verdicts pass, verify the diff contains only the task's allowed
   paths plus declared task-state files. Update the matching task to `[X]` and
   persist the Quality and Standards reports in
   `.specify/delivery/<feature>/task-verdicts.yml`.
8. Append a concise iteration record to the configured progress file when one
   is enabled. Include the task id, commit subject, changed paths, checks, and
   the next task focus.
9. Stage only the verified task paths and declared task-state/progress files.
   Do not use `git add -A`, `git add .`, or a broad wildcard. Create exactly
   one commit for the completed task using:

   ```text
   feat(ralph): <task-id> - <task-title>
   ```

10. Verify that `HEAD` advanced, the commit contains the task result, and the
    worktree is clean. Record the resulting commit SHA in the local verdict
    receipt. If commit or verification fails, leave the task open and report
    the exact recovery blocker.

After a successful commit, begin the next iteration with fresh task focus and
re-read all durable artifacts. A task is not complete merely because source
files changed or tests passed; it is complete only after its Git commit and
receipt exist.

## Completion

When no incomplete task remains, verify that every task has a passing current
receipt, the active branch is the Ralph branch, and the worktree is clean. Only
then emit this exact machine-readable signal:

```text
<promise>ALL_TASKS_DONE</promise>
```

If incomplete tasks remain but none is dependency-ready, report the blocking
task ids and downstream tasks held by them. Do not emit the completion signal.
The command also stops without completion when the configured iteration limit
is reached.
