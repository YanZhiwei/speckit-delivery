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

Prioritize defects over style. Inspect consumers and callers, not only changed functions. A finding contains severity, location, defect, impact, evidence, remediation, and architecture impact.

Return `pass` only when no blocking finding remains. Convert blocking findings to `tasks.md` entries before further implementation; rerun analyze and Ralph rather than allowing review prose to become a second task queue.
