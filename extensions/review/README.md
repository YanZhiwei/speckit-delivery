# Delivery Review

`speckit.review.run scope=task task=<id>` reviews one task;
`scope=outgoing-diff` reviews integrated changes. Both use the shipped
[Reviewer contract](templates/reviewer.md), the single policy owner for:

- Requirements, code quality, architecture/design standards, correctness,
  security/compatibility, and test effectiveness.
- Base/HEAD/merge-base and code/requirements fingerprints, including uncommitted
  and relevant untracked files; HEAD alone cannot establish freshness.
- Per-dimension verdicts, explicit coverage, actual reviewer independence, and
  `REVIEW_VERDICT: pass | blocked | incomplete` aggregation.
- Stable finding IDs and `open/fixed-pending-review/resolved/dismissed` states.
  Omitted findings do not become resolved; fixers cannot approve their own fixes.

Review is read-only. The coordinator prepares a focused packet and persists the
report under the actual delivery run's `reviews/<scope>/review.yml`, honoring
artifact policy. If independent review is unavailable, disclose self-review;
without the user's explicit acceptance it is incomplete, not pass.
`speckit.delivery.review-fix` owns one verified repair pass; Review then verifies
the repair and current coverage. Final review remains necessary after task passes.

`speckit.review.standards` is the task-or-batch closure review used immediately
after implementation. It reads only relevant policy sources, returns
`STANDARDS_VERDICT: pass | blocked`, and does not repeat mechanical quality
commands. It makes DRY, ownership, layer direction, public surface, comment
intent, and ADR impact explicit before Ralph may close a task.

Quality owns executable checks; Standards owns documented semantic rules. Reuse
current exact-scope receipts instead of repeating suites, but green checks cannot
replace the six-dimensional analysis or excuse a concrete Plan-mandated defect.

Install with `specify extension add --dev /absolute/path/to/extensions/review`
in a clean Spec Kit project or use the pinned Bundle. Invoke through the active
host. Source edits, commits, tracker mutation, publishing, and nested reviewers
are outside the reviewer's authority.
