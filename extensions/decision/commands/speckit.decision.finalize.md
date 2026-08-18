---
description: "Finalize Proposed ADRs against reviewed implementation at repository HEAD"
---

# Finalize Architecture Decision

## Input

```text
$ARGUMENTS
```

Run after implementation, convergence, simplification, and blocking review fixes. Re-read the Proposed ADR, relevant code, tests, configuration, public contracts, and final review result. Reconcile the record with what exists at HEAD.

Update status to `Accepted` only when the implementation and evidence support the decision. Revise the Proposed record while it is still proposed when implementation details changed without changing the decision. Reject it and create an accurate replacement when the chosen architecture materially changed.

Remove references to ignored feature artifacts, task IDs, review chronology, conversation turns, and temporary file locations. Preserve durable rationale, alternatives, consequences, compatibility obligations, and conditions for reconsideration.

The command is complete when a future reader can understand the final decision from tracked repository content alone.
