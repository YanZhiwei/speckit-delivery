# Ralph protocol

Spec Kit is the structured source of truth; Ralph is the bounded execution
loop. The portable contract is one dependency-ready task per iteration in a
clean Git worktree. Parallel workers are allowed only when the provider gives
each worker an isolated worktree and an explicit integration contract.

Before task selection, worker dispatch, quality briefing, or the first edit,
resolve the active feature, capture the clean baseline, and execute the branch
gate: create or reuse `ralph/<feature-slug>` (or the configured prefix), then
verify that it is the active branch. Stating that the branch will be created is
not execution. Never stash, reset, clean, or stage pre-existing user changes. A
missing Git repository, dirty baseline, or unsafe branch transition is a
blocker.

After the branch gate, Ralph emits a concise run-level governance summary
before task selection. It names the active feature, branch, base `HEAD`,
applicable Constitution/ADR/quality/standards sources, closure gates, and stop
conditions. It reports only relevant excerpts and paths rather than dumping all
policy text. Each iteration then emits a task governance packet containing the
task acceptance criteria, allowed paths, applicable code style and architecture
rules, and exact checks. Missing policy or quality-profile sources are blockers;
Ralph must not silently fall back to generic rules.

For each iteration, parse task identifiers, dependencies, `[P]` markers,
user-story labels, file targets, and verification instructions. Treat file
overlap, shared public contracts, migrations, and unresolved design decisions
as blocking edges even when tasks carry `[P]`. Give the worker exactly one
task, including the acceptance condition and relevant Spec/Plan/ADR excerpts.

The worker returns changed paths, commands, results, residual risk, and
blockers. It does not edit the task checkbox or create the closure commit. The
orchestrator runs the task checks, Quality, Standards, and independent task Review. Before
the checkbox changes, it verifies acceptance evidence, all declared checks,
current `QUALITY_VERDICT: pass`, `STANDARDS_VERDICT: pass`, and `REVIEW_VERDICT: pass`,
unchanged code/requirements snapshot including uncommitted and relevant untracked
contents, unchanged `HEAD`, allowed paths, and availability of required checks and policy
sources. It reports `RALPH_TASK_GATE: PASS` only when every item passes. Only
then may the orchestrator mark `[X]` and persist the receipt.
That state transition is immediately followed by staging the verified task
paths and declared state files and creating exactly one commit; no next-task
work or unrelated edit may occur between the checkbox and commit:

```sh
git add -- <verified-task-path> <task-state-path> [<progress-path>]
git diff --cached --check
git commit -m "feat(ralph): <task-id> - <task-title>"
```

The orchestrator verifies that `HEAD` advanced, the commit contains the task
result and task-state transition, and the worktree is clean before recording
the commit identity; it does not modify tracked task state after that clean
commit. A failed or blocked task remains open and blocks its dependents.
Completion is valid only when every task has a passing snapshot-bound receipt
associated with its verified commit, the
Ralph branch is active, the worktree is clean, and the loop emits
`<promise>ALL_TASKS_DONE</promise>`.

Use the installed Ralph command as the execution owner, the installed Review
template for six dimensions/independence/finding policy, and Delivery review-fix
for one bounded repair pass. Task repairs stay in the same open task, never
recursive Ralph. Attempts survive resume; fixers cannot resolve their own findings.
Final Review still checks integration after task-level passes.
