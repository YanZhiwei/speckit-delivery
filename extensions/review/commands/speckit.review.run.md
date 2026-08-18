---
description: "Review a verified base/head diff against standards, specification, architecture, correctness, and risk"
---

# Delivery Review

Resolve and record the live base, head, merge-base, outgoing commits, and changed files. Revalidate scope if the branch changes during review. Read applicable agent instructions, Constitution, Spec, Plan, accepted/proposed ADRs, and tests.

Review these axes:

1. Standards and project governance.
2. Spec behavior and acceptance conditions.
3. Architecture and ADR consistency.
4. Correctness, ownership, lifecycle, concurrency, and failure paths.
5. Security, data boundaries, and compatibility.
6. Test strength on the real entry path.

Prioritize defects over style. Inspect consumers and callers, not only changed functions. A finding contains severity, location, defect, impact, evidence, remediation, and architecture impact.

Return `pass` only when no blocking finding remains. Convert blocking findings to `tasks.md` entries before further implementation; rerun analyze and Ralph rather than allowing review prose to become a second task queue.
