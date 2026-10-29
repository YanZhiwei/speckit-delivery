---
description: "Check delivery component installation, policy coverage, and workflow readiness before implementation"
---

# Delivery Doctor

Direct workflows require a user-assigned `delivery_run=<id>` before dispatch.
Validate the safe single-segment contract in Delivery Explore, check for an
unrelated-run collision, and verify the workflow persists its canonical packet,
passes exact paths and actual gate choices, and retains run identity in Review,
repair, nested Ralph, and handoff. Context-only handoff is valid only in a shared
router session, not separate CLI host processes. Do not invent a Feature path.

Direct Bugfix also requires an explicit `bug_slug`, normalized to lowercase
kebab-case and separately identified from the run. A fresh assessment needs an
unused output path; stop on a collision before invoking the official assessor,
whose automated fallback could otherwise choose a different slug. Resume uses
the same verified recorded identity and completed checkpoint, not a fresh assess
or an unrelated existing assessment. Verify the coordinator, not official Assess,
owns persistence of the external Delivery mapping and its approval receipt.

Read `.specify/extensions.yml`, extension and workflow registries, installed
component manifests, `delivery-config.yml`, `quality-config.yml`, and the
active integration. Verify that Delivery, Decision, Ralph, Review, Simplify,
Evidence, Quality, and Docs Sync are installed when their selected lane needs
them. For Bugfix, also verify the official Bug extension and its assess/fix/test
commands. Verify that Feature, Bugfix, and Lightweight workflows reference the
installed commands rather than an obsolete copy. Feature and Bugfix need the
installed `speckit.delivery.explore` command and its
`templates/exploration.md` resource. Check that Feature places exploration and
scope approval before specify, and that Bugfix consumes exploration before its
assessment/scope gate. The existing Feature plan gate must require presentation
of the finalized tree, responsibilities, interfaces, and tests. Report an old
installation missing these contracts as stale; do not modify it silently.

Also verify Review ships `templates/reviewer.md` and supports task/final scopes,
six dimension verdicts, independence/coverage, and content-bound findings; Delivery
ships `speckit.delivery.review-fix`; Ralph requires REVIEW_VERDICT before closing
a task. All three lane workflows need bounded review/repair slots, a final review,
and an aborting review gate before delivery. Verify configured repair bounds are
positive integers and explain the portable three-slot ceiling. A stale two-verdict
Ralph or report-less review path is a blocker, not compatibility by assumption.

Verify the Bugfix continuation adapter ships; initial official fix/test reports
must not be overwritten or their automated refusal bypassed during re-review.
Quality must emit original checked-input/configuration receipts; HEAD/path-only
hook reuse is stale, not compatible with snapshot-bound task closure.

CodeGraph, network access, and GitHub credentials are investigation capabilities,
not unconditional installation prerequisites. Exploration reports fallback or
research limitations and whether they block the actual scope decision.

For every configured changed-code family, verify a Quality profile matches it,
each required command is executable as written, and every listed rule has an
owner and credible mechanism. Mechanical rules belong to Quality; semantic
rules such as DRY, ownership, and architecture must name Standards Review,
Simplify, or ADR as their owner. A rule with no mechanism is a governance gap,
not a passing rule.

Return:

```text
SD_DOCTOR_VERDICT: pass | blocked
INTEGRATION: <active integration>
COMPONENTS:
- <component>: installed | missing | stale — <evidence>
WORKFLOWS:
- <workflow>: ready | stale | missing — <evidence>
POLICY_COVERAGE:
- <rule/profile>: covered | gap — <owner and mechanism>
BLOCKERS:
- <id or none>: <remediation>
```

Do not edit source code or silently install components. The command is complete
only after it reports concrete remediation for every blocker.
