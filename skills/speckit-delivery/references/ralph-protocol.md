# Ralph protocol

Spec Kit is the structured source of truth; Ralph is the bounded execution
loop. The portable contract is one dependency-ready task per iteration in a
clean Git worktree. Parallel workers are allowed only when the provider gives
each worker an isolated worktree and an explicit integration contract.

Before the first edit, resolve the active feature, capture the clean baseline,
and create or reuse `ralph/<feature-slug>`. Never stash, reset, clean, or stage
pre-existing user changes. A missing Git repository, dirty baseline, or unsafe
branch transition is a blocker.

For each iteration, parse task identifiers, dependencies, `[P]` markers,
user-story labels, file targets, and verification instructions. Treat file
overlap, shared public contracts, migrations, and unresolved design decisions
as blocking edges even when tasks carry `[P]`. Give the worker exactly one
task, including the acceptance condition and relevant Spec/Plan/ADR excerpts.

The worker returns changed paths, commands, results, residual risk, and
blockers. It does not edit the task checkbox or create the closure commit. The
orchestrator runs the configured checks and both Quality and Standards verdicts.
Only after both pass may the orchestrator mark `[X]`, stage the verified task
paths and declared state files, and create exactly one commit:

```text
feat(ralph): <task-id> - <task-title>
```

The orchestrator verifies that `HEAD` advanced, the commit contains the task
result, and the worktree is clean before recording the commit identity. A
failed or blocked task remains open and blocks its dependents. Completion is
valid only when every task has a passing current receipt, the Ralph branch is
active, the worktree is clean, and the loop emits
`<promise>ALL_TASKS_DONE</promise>`.
