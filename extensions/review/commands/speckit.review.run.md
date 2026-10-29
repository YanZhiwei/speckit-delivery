---
description: "Independently review task or outgoing changes across six dimensions, with snapshot-bound findings and coverage"
---

# Delivery Review

## Input

```text
$ARGUMENTS
```

Read the installed `.specify/extensions/review/templates/reviewer.md` (or
`templates/reviewer.md` under the resolved extension root). It is the single
reviewer contract for input preparation, six-dimensional analysis, findings,
coverage, snapshot identity, and the structured report. Do not replace it with
an implementer's self-review or a checklist of test successes.

1. Resolve the lane and scope. `scope=task task=<id>` is a focused task review;
   `scope=outgoing-diff` is the final integrated review. Default to outgoing-diff
   only when the actual base and complete change set are known, never HEAD~1 by
   assumption. Include committed, staged, unstaged, and relevant untracked files.
   `delivery_run=<id>` identifies the canonical `.specify/delivery/<id>/` run,
   using Delivery Explore's safe-id validation. The coordinator reads/writes its
   scope report and repair checkpoint there across processes; do not silently
   switch to a Feature path or forget previous findings when resuming.
2. The coordinator prepares the template's evidence packet, including approved
   requirements/design/exploration, applicable governance/ADRs, real diff and
   caller context, verification evidence, and previous finding state. A Bugfix
   uses its assessment; Lightweight uses its bounded request, not a forced Spec.
3. Prefer a fresh reviewer context independent of the implementer. Pass the
   packet and source paths, not the entire implementation conversation or
   instructions to suppress particular defects. A task needs one scoped reviewer,
   not a fan-out of nested reviewers. Final review remains broad across tasks.
   If independent execution is unavailable, report `independence: self-review`;
   it is incomplete unless the user explicitly accepted that degradation for
   this scope. Do not silently equate self-review with independent review.
4. The reviewer reads and returns the structured report from the template.
   Review is read-only: do not edit source, task state, index, branches, commits,
   or tracker resources. Do not dispatch additional reviewers from the reviewer.
   Reuse valid Quality/Standards evidence for exactly the same code and scope;
   independently judge all six dimensions instead of skipping quality/design.
5. The coordinator checks the report, records it, and presents findings and
   per-dimension verdicts to the user. Keep one current report and stable finding
   IDs at `.specify/delivery/<feature-or-run>/reviews/<scope>/review.yml` when an
   actual run location exists, honoring artifact policy; otherwise preserve it
   explicitly in context. Exclude only declared review/receipt bookkeeping from
   the reviewed-content fingerprint, not source/tests/spec/policy changes.
6. Reconcile every earlier unresolved finding explicitly. Missing from this
   output does not mean resolved. A changed HEAD, worktree content, requirements,
   or relevant caller invalidates reuse; same-HEAD reruns can still review new
   uncommitted contents. A malformed report, missing axis, coverage gap, stale
   snapshot, or required evidence/independence gap cannot return pass.
## Discipline checks

Apply these discipline checks to the changed code:

- **Behavior, not implementation.** A test must call the code the way its user
  does and assert what that user observes. If every changed function could
  return nothing and the new tests still pass, the tests do not cover the
  behavior.
- **Cause, not symptom.** A guard, retry, or fallback that only hides a
  reproduced failure is not a fix. Name the reproduced cause and the test that
  pins it.
- **Subtract before adding.** New branching, state, indirection, or an
  abstraction needs a reason the pre-change design could not express. When the
  change adds surface without removing any, ask why.
- **Verifiable units.** Each task must be independently checkable. A change
  that only works together with later work, or that cannot be verified at the
  reported HEAD, is a finding.

Prioritize defects over style. Inspect consumers and callers, not only changed
functions. With a fresh project `.codegraph/` index, use impact/caller analysis
and cite verified source. Report graph gaps and use targeted source/test fallback;
an unavailable index alone is not incomplete review if that fallback establishes
the required coverage. Use the Reviewer template's finding contract.

Return `REVIEW_VERDICT: pass | blocked | incomplete` using the template's
aggregation rules. Read-only review never fixes or closes a task. The coordinator
routes confirmed findings through `speckit.delivery.review-fix` and re-review;
Feature execution still has exactly one queue, `tasks.md`. A final review does
not pass merely because all individual tasks or mechanical checks passed.
