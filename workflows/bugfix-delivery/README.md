# Bugfix Delivery Workflow

Uses Spec Kit's official `bug` extension for assessment, remediation, and regression
validation. Doctor, ADR discovery, and `speckit.delivery.explore` establish the
relevant code/directory structure and Issue/PR/commit history first. Assessment
consumes that packet and owns reproduction, root-cause diagnosis, and red evidence;
it does not repeat structural research or require a full Feature spec.

Supply required `delivery_run=<safe-id>` and a separate normalized `bug_slug`,
reusing both on resume. Explore persists the canonical packet and expected Bug
reference before exit. Official Assess writes only its Bug assessment, not the
external packet. The coordinator verifies the exact expected assessment and
records its actual reference/hash and the real assessment-gate choice. A fresh
run stops on slug/output collision; it never guesses another or latest Bug.

```bash
specify workflow run bugfix-delivery --input delivery_run=retry-fix-01 --input bug_slug=duplicate-retry --input report="Retries duplicate notifications"
```

The assessment gate shows current/candidate directory trees, fault path, evidence,
repair/test scope, exclusions, and risks before approval. Missing reproduction or
critical evidence blocks fixing. New capability, material architecture, or durable
contract changes stop this workflow and resume Feature with the same evidence;
multiple files alone do not require escalation. See the
[Delivery contract](../../extensions/delivery/README.md).

Final six-dimensional Review uses up to three safe review/repair slots, the lower
configured repair budget, final review, and an aborting gate. Repair stays with
the approved assessment, not forced Feature tasks. After the initial official
`bug.fix/test`, the [continuation adapter](../../extensions/delivery/templates/bugfix-review-repair.md)
preserves those reports and appends versioned per-round repair/regression records;
it does not re-invoke their automated-overwrite refusal paths. Current
complete pass makes remaining slots no-ops; blocked/incomplete stop delivery.
Attempts and finding IDs persist across resume/new HEAD; decision checks require
a freshness review before evidence/handoff. YAML gates are guided checkpoints,
not automatic semantic validation. See the
[Reviewer contract](../../extensions/review/templates/reviewer.md).

Continuation preserves all applicable pre/post fix/test hooks. Mandatory hooks
must actually finish using the current round's context/report paths; stale
original-report assumptions, failures or unavailable required hooks block rather
than silently passing or overwriting evidence.
