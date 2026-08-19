---
description: "Execute dependency-ready Spec Kit tasks with verified orchestrator-owned completion"
---

# Ralph

## Input

```text
$ARGUMENTS
```

Locate the active feature's `tasks.md`. Parse phases, `Txxx` identifiers, `[P]` markers, user-story labels, dependencies, file targets, and verification instructions. Treat shared files, shared public contracts, migrations, and unresolved design decisions as blocking edges even when `[P]` is present.

Select dependency-ready tasks. Dispatch one task or a cohesive red/green/refactor bundle per worker when the active integration supports delegation. Otherwise execute the same packets sequentially with fresh task focus.

Before a worker edits source, invoke `speckit.quality.brief` with its target
paths and task scope, then include the returned Quality Brief in the worker
packet. Each packet includes the acceptance condition, allowed scope, relevant
Spec/Plan/ADR excerpts, expected verification, and the rule that the worker
reports rather than marks completion. For ignored Spec artifacts, inject these
excerpts explicitly; another worktree cannot be assumed to contain them.

For every result, verify changed paths, tests or other evidence, residual risk, and dependency effects. Invoke the installed `speckit.quality.check` with the task identifier, changed paths, and current base/head scope. Require `QUALITY_VERDICT: pass` at the current HEAD before marking `[X]`; a missing Quality extension, a blocked verdict, or a stale verdict leaves the task incomplete and blocks its dependents. Retry bounded failures only after their cause is corrected.

The command is complete when no dependency-ready task remains, or when it reports the exact blocker and downstream tasks held by it.
