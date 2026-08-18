---
name: speckit-delivery
description: Route and orchestrate a complete Spec Kit delivery across feature, bugfix, and lightweight lanes, including ADR retrieval/finalization, tasks-based Ralph execution, convergence, simplification, review, evidence, and PR handoff. Use when the user asks to run the full SDD lifecycle or wants one entry point instead of invoking individual speckit commands.
---

# Spec Kit Delivery

Use the installed `speckit.delivery.route` command with the user's request.
That extension command is the canonical cross-integration owner of lane
routing, ADR lifecycle, Ralph orchestration, and completion conditions.

The native skill is a convenience surface only. Preserve the selected project's
existing workflow and report a missing Delivery extension as an installation
blocker. Do not publish, push, merge, or create external resources unless the
user separately authorized that action.
