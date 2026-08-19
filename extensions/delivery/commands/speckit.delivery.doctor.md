---
description: "Check delivery component installation, policy coverage, and workflow readiness before implementation"
---

# Delivery Doctor

Read `.specify/extensions.yml`, extension and workflow registries, installed
component manifests, `delivery-config.yml`, `quality-config.yml`, and the
active integration. Verify that Delivery, Decision, Ralph, Review, Simplify,
Evidence, Quality, and Docs Sync are installed when their selected lane needs
them. Verify that Feature, Bugfix, and Lightweight workflows reference the
installed commands rather than an obsolete copy.

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
