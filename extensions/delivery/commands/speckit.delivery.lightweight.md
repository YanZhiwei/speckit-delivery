---
description: "Implement a narrowly scoped mechanical or behavior-preserving change with targeted verification"
---

# Lightweight Delivery

## Input

```text
$ARGUMENTS
```

Fix the live base/head scope and confirm the requested outcome is mechanical, documentation-only, or behavior-preserving. If requirements, public behavior, compatibility, durable data, security, or architecture are unclear, stop and recommend Feature or Bugfix instead.

State the relevant file paths and intended small scope before editing. Do not
require full exploration, GitHub research, or two approval rounds for a mechanical
change. Implement the narrow change, preserve unrelated user work, and run the
smallest credible local check. Report changed paths, result, risk, and any reason
the lane must escalate. The command is complete when the requested small outcome
is visible and its targeted evidence passes.
