---
description: "Verify that an implemented simplification reduced surface area and preserved required behavior"
---

# Verify Simplification

Compare the final base/head diff, accepted candidate, callers, tests, public contracts, documentation, and ADRs. Confirm required behavior remains, ambiguous consumers were resolved, obsolete tests/docs/config were removed or updated, and the change produces net deletion or a demonstrably smaller ownership model.

Fail when complexity was moved behind a wrapper, a supported consumer was dropped without a decision, compatibility residue still exposes the removed contract, or evidence covers only mocks rather than the production entry path.
