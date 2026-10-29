# Ralph

This extension bridges Spec Kit's `tasks.md` with a Ralph-style autonomous
loop. Spec Kit defines the destination; this extension consumes one task at a
time until the task queue is complete.

## Execution contract

The portable mode is deliberately sequential because each completed task owns
one Git commit in the shared worktree:

1. Before task selection or editing, require a clean Git worktree, create or
   reuse `ralph/<feature-slug>`, and verify that it is the active branch.
2. Report the applicable governance sources, closure gates, and stop conditions.
3. Select exactly one dependency-ready task and emit its task governance packet.
4. Read the task's Spec/Plan/ADR context and run `speckit.quality.brief`.
5. Implement the task and run its checks.
6. Run `speckit.quality.check`, `speckit.review.standards`, and independent
   `speckit.review.run scope=task task=<id>` across six dimensions.
7. Before changing `[ ]` to `[X]`, verify acceptance evidence, all three current
   passing verdicts, unchanged code/requirements snapshot (not HEAD alone), allowed
   paths, and available required checks.
8. When the task gate passes, mark `[X]` and write the receipt, then immediately
   commit the verified task paths with
   `feat(ralph): <task-id> - <task-title>`.
9. Verify the new `HEAD` and a clean worktree before starting the next task.
10. Emit `<promise>ALL_TASKS_DONE</promise>` only when every task is committed
   and has a passing snapshot-bound receipt associated with its verified commit.

Workers report their results; the orchestrator owns task closure and commits.
It never stashes, resets, cleans, or stages unrelated pre-existing changes.

Confirmed review findings return through `delivery.review-fix` to the same open
task, without recursive Ralph. Repairs use Delivery's configured budget and keep
attempts/IDs across resume. Only the independent reviewer verifies resolution;
missing evidence, unaccepted self-review, incomplete coverage, or exhausted
unresolved blockers keep the task open. Pre-commit review is associated with the
resulting commit only after content equivalence is checked; final integrated
Review still follows Ralph. See the [Reviewer contract](../review/templates/reviewer.md).

Parallel execution is not the default. It requires isolated worktrees and a
provider-specific integration contract; otherwise it can mix task changes and
break per-task commit ownership.

## Configuration

Copy `config-template.yml` to the target project's Ralph configuration when
customization is needed. The defaults are:

```yaml
provider: auto
max_parallel: 1
max_retries: 2
max_iterations: 100
artifact_policy: tracked
generic_fallback: sequential
branch_policy: create_or_reuse
branch_prefix: ralph/
commit_policy: per_task
commit_message: "feat(ralph): {task_id} - {task_title}"
completion_promise: "<promise>ALL_TASKS_DONE</promise>"
orchestrator_marks_completion: true
```

The command is still an agent-host prompt rather than a provider-specific
shell daemon. Git branch and commit behavior is therefore part of the command
contract and must be executed by the active agent host. A future provider
adapter may move these operations into a native loop without changing the
task-closure contract.
