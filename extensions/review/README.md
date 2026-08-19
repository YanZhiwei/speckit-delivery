# Delivery Review

`speckit.review.run` is the final live base/head review: Standards, Spec,
architecture, correctness, security, test strength, and lifecycle.

`speckit.review.standards` is the task-or-batch closure review used immediately
after implementation. It reads only relevant policy sources, returns
`STANDARDS_VERDICT: pass | blocked`, and does not repeat mechanical quality
commands. It makes DRY, ownership, layer direction, public surface, comment
intent, and ADR impact explicit before Ralph may close a task.
