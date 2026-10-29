# Bugfix review-repair continuation adapter

Used only by `delivery.review-fix` after the initial official `bug.fix` and
`bug.test`. Those commands own initial remediation/validation and refuse automated
overwrites of `fix.md`/`test.md`. This adapter implements a bounded continuation
of their approved assessment, not an invocation that bypasses their preconditions.

1. Resolve the actual Bug slug from the run's persisted exploration/assessment
   reference or explicit bug identity; never use the Delivery run id as its slug.
   Read the approved `assessment.md`, original `fix.md` and `test.md`, all earlier
   repair attempts, and the current verified review finding IDs. Require the
   assessment's approval, repair scope, and reproduction/regression evidence.
   Record hashes of the original three reports; they remain immutable here.
2. Use the attempt already reserved by `delivery.review-fix`; do not allocate a
   second counter. Create the previously unused directory
   `.specify/bugs/<slug>/review-repairs/<delivery-run>/round-<n>/`. If that attempt
   exists, resume its explicit state without overwriting evidence or doing a
   second repair pass; ambiguous/interrupted state stops for recovery. Do not
   rename the bug, delete official reports, or change the approved assessment.
3. Apply only the confirmed finding's authorized correction in the assessment's
   allowed paths, including a meaningful regression assertion. Follow applicable
   `before_bug_fix` hooks and project verification policy from the installed
   official Bug commands, using the hook lifecycle below; do not dispatch
   `bug.fix`/`bug.test` again. Missing scope/red evidence or material design
   expansion stops for investigation/approval. No Feature tasks needed.
4. Write `fix.md` in this round directory: original assessment/report references
   and hashes, finding IDs, triggering case/red evidence, actual changed paths,
   correction, command results, and residual risk. This is a continuation record,
   not a replacement for the original official `fix.md`.
   Discover and execute applicable mandatory `after_bug_fix` hooks with this
   current round's fix report and repaired-content context; wait and record
   results before entering validation. Do not reuse initial-run post-hook results.
5. Perform the approved focused regression/validation and applicable pre-test
   `before_bug_test` hooks for the repaired contents. Write `test.md` beside the round fix record,
   binding commands, results, tested contents/configuration, findings, and any
   failures/limitations. An unchanged old `test.md` cannot validate the new repair.
   Discover and execute applicable mandatory `after_bug_test` hooks with the
   current round's test/fix reports; wait and record results before completion.
   Refresh affected Quality/Standards through their owners, then verify the three
   original report hashes are unchanged. Any unauthorized original-report change
   blocks continuation; preserve work and report it, do not silently undo it.
6. Update the coordinator's run checkpoint with the round record references and
   snapshot. Findings are `fixed-pending-review` only, not resolved. Return
   `re-review-required` when validation succeeds or `blocked` with exact evidence
   otherwise. Only an independent reviewer may verify resolution on current code.

## Hook lifecycle and current-round context

Honor all four official hook families in order: `before_bug_fix`, `after_bug_fix`,
`before_bug_test`, `after_bug_test`. Read `.specify/extensions.yml` and the installed
official commands' selection/dispatch rules at each phase; disabled hooks do not
run and optional hooks are offered rather than silently auto-executed. Actually
invoke each applicable mandatory hook and wait for its result; emitting an
`EXECUTE_COMMAND:` marker or a previously passing receipt is not execution.
Malformed registry, unavailable mandatory hook, or failed required outcome blocks
completion. Leave non-empty condition expressions to the supported HookExecutor;
do not invent an evaluator or silently assume a mandatory conditional hook passed
when applicability/execution cannot be established.

Explicitly pass actual Bug slug/directory, Delivery run, reserved attempt, phase,
current contents identity, and available round-local fix/test report paths to
each hook. Do not relabel round paths as original official reports. A hook that
can only read/overwrite the original `BUG_DIR/fix.md` or `test.md` needs an
authorized integration decision; stop rather than mutate originals or feed it
stale reports. Record hook identity, supplied context, command, outcome, and
checked snapshot in the round evidence. If a hook changes governed inputs,
refresh affected evidence on the final stable contents or block; old tests cannot
validate post-hook mutations. Do not start a hidden loop or exceed the reserved
repair budget to obtain success.

This adapter does not authorize commits, publication, report overwrites, new
requirements, a fresh repair budget, or a hidden nested loop. Durable summaries
must include the continuation outcome rather than claiming the original test
report covers repairs it predates.
