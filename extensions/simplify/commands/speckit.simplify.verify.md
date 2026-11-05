---
description: "Verify that an implemented simplification reduced surface area and preserved required behavior"
---

# Verify Simplification

## Input and run/output binding

```text
$ARGUMENTS
```

A direct Delivery invocation must supply explicit
`lane=feature|bugfix|lightweight` and `delivery_run=<id>`. Validate the run as
one safe path segment and read only the canonical
`.specify/delivery/<delivery_run>/simplifications.md`; the run id is not a
Feature or Bug slug. For Bugfix, use the coordinator's approved assessment and
accepted candidate identities. For Lightweight, use the bounded request and do
not look for Feature tasks or `forcedTasks`.

Per-run operational state/results belong under
`.specify/delivery/<delivery_run>/runtime/`; the candidate report remains at the
run root. Follow the central owner at
`.specify/extensions/delivery/templates/runtime.md`. When either
`runtime_stage` or `runtime_result` is supplied, require the canonical
`delivery_run`, read that file in full, and follow its runtime contract; do not
invent helper flags, paths, or result schemas. Use the runtime `owner-result`
helper with the native verification report and a stage data JSON, or write the
exact machine `native_receipt` and normalized envelope the contract defines,
covering exactly the runtime-accepted candidate IDs. With
neither argument, do not create runtime state here.

A standalone invocation without `delivery_run` may compare the supplied diff and
report inline, but must not infer another active Feature, create a directory, or
write a guessed report path. Use `SIMPLIFICATIONS_PATH: inline` in that case.

## Verification scope

Read the final base/head diff, accepted candidate records, callers, tests, public
contracts, documentation, and applicable ADRs. Verify only candidates explicitly
accepted by the owning lane's approval, with that acceptance recorded in the
canonical report or an authoritative same-run runtime gate receipt. Proposed,
rejected, deferred, or merely observed candidates are not verification
obligations and must not be silently treated as accepted.

If the canonical report is absent, malformed, or says `SIMPLIFY_SCAN: none`,
and no candidate was accepted, return a valid no-op
`SIMPLIFY_VERIFY: not-applicable`; do not fail because there is nothing to
verify and do not invent a candidate. The same conditional no-op applies when a
report contains candidates but the approval records that none were accepted.
A missing report is a blocker only when the workflow claims an accepted
candidate exists or the run's recorded checkpoint requires that report.

For each accepted candidate, confirm required behavior remains, ambiguous
consumers were resolved, obsolete tests/docs/config were removed or updated,
and the result produces net deletion or a demonstrably smaller ownership model.
Fail when complexity was moved behind a wrapper, a supported consumer was
dropped without a decision, compatibility residue still exposes the removed
contract, evidence covers only mocks rather than the production entry path, or
the accepted lane route was not followed. Bugfix candidates must remain within
the approved assessment/continuation; Lightweight candidates must remain within
the bounded request and must not grow a Feature queue.

This command is read-only. It does not edit source, tests, docs, queues,
assessments, or candidate approval; it may report its operational result through
the central runtime contract only.

## Output

```text
SIMPLIFY_VERIFY: pass | fail | not-applicable | blocked
LANE: <feature|bugfix|lightweight|standalone>
DELIVERY_RUN: <id or none>
SIMPLIFICATIONS_PATH: <.specify/delivery/<id>/simplifications.md or inline>
ACCEPTED_CANDIDATES: <ids or none>
EVIDENCE:
- <candidate id or none>: <production caller, deletion/smaller ownership, behavior and test evidence>
BLOCKERS:
- <id or none>: <concrete recovery>
NEXT_ACTION: <verify accepted work, route the blocker, or none>
```

The command is complete when every accepted candidate is conditionally verified
against production behavior and current contracts, or an explicit no-candidate/
none-accepted no-op is reported. Never report a terminal Delivery outcome from
Simplification Verify.
