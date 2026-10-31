---
description: "Select, run, and report the narrowest credible verification for the actual outgoing diff"
---

# Delivery Evidence

Resolve the live base/head and outgoing diff. Read project verification configuration, CI definitions, hooks, and changed code. Map changed surfaces to evidence: build/typecheck for compiled code, focused tests for behavior, integration or migration checks for data boundaries, contract tests for APIs, browser evidence for user flows, documentation generation/link checks for docs, and security checks for trust-boundary changes.

Reuse passing hook evidence only when its original checked-input/configuration
identities, scope, and commit still match, following the installed Quality Check
execution-receipt contract. HEAD/path-only evidence cannot prove same-content
execution; rerun the affected check if identity is missing. Do not duplicate
expensive checks without a gap. Prove environment-specific failures rather than
dismissing them. Record command, working directory, relevant environment, exit
status, and concise result.

Write `.specify/delivery/<feature>/evidence.md` when a feature is active and render a durable summary for the PR. Evidence is the durable, self-contained record; `exploration.md`, `slices.md`, `receipts/`, `task-verdicts.yml`, `pull-request.md`, and review working reports are run workspace and follow `artifact_policy` (when it is ephemeral, keep them local instead of committing them).

Bind the evidence to the reviewed head that the pull request publishes, plus the pull-request reference. Do not invent or require a squash-merge commit that does not exist yet; `speckit.delivery.close` records the actual outcome afterwards. Re-resolve outgoing commits before handoff; new commits invalidate stale review or evidence scope.

Write the durable record before publication. After the pull request is merged or closed, run `speckit.delivery.close` with the actual outcome so the record says `delivered`, `abandoned`, or `superseded` instead of staying silently active.

The command is complete when every material changed surface has credible evidence or a clearly disclosed gap owned by CI/human follow-up.
