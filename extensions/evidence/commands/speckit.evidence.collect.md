---
description: "Select, run, and report the narrowest credible verification for the actual outgoing diff"
---

# Delivery Evidence

Resolve the live base/head and outgoing diff. Read project verification configuration, CI definitions, hooks, and changed code. Map changed surfaces to evidence: build/typecheck for compiled code, focused tests for behavior, integration or migration checks for data boundaries, contract tests for APIs, browser evidence for user flows, documentation generation/link checks for docs, and security checks for trust-boundary changes.

Reuse passing hook evidence when its scope and commit still match. Do not duplicate expensive checks without a gap. Prove environment-specific failures rather than dismissing them. Record command, working directory, relevant environment, exit status, and concise result.

Write `.specify/delivery/<feature>/evidence.md` when a feature is active and render a durable summary for the PR. Re-resolve outgoing commits before handoff; new commits invalidate stale review or evidence scope.

The command is complete when every material changed surface has credible evidence or a clearly disclosed gap owned by CI/human follow-up.
