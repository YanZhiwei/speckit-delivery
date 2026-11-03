---
description: "Apply a configured design, diagnosis/testing, or review method within the owning SD phase"
---

# Delivery Method Adapter

## Input

```text
$ARGUMENTS
```

Accept `phase=design|diagnose|review`, explicit lane/run/scope, and the owner's
exact packet paths or preserved excerpts. The design phase also needs its actual
approved-plan path (or the explicitly supplied plan draft for a fresh
walkthrough). This helper runs inside an existing phase, not as another approval,
execution queue, or repair loop. It returns analysis to the owner without writing
source, reports, or shared state.

1. Read the installed `templates/method-adapter.md` and the one matching
   `templates/method-design.md`, `templates/method-diagnose.md`, or
   `templates/method-review.md`. The shared template owns configuration,
   provenance, fallback, permissions, input identity, and the result contract.
2. Resolve the selected method from project-local Delivery configuration. An
   absent configuration/phase defaults to `builtin`. Validate explicit external
   resources before reading their guidance; do not discover a different skill,
   install one, fetch mutable instructions, or execute its scripts.
3. Use the supplied phase packet in the current owner's context. For review,
   this is the single reviewer context already selected by Review's coordinator;
   this helper never dispatches another reviewer or claims independence itself.
4. Apply the selected profile's bounded method and return `METHOD_STATUS` plus
   the native result and provenance receipt. The owner persists it in its normal
   artifact and verifies it before advancing. An adapter result never authorizes
   task closure, a commit, an ADR status change, tracker mutation, or publication.

The command is complete when the owner receives a scope-bound result or an
explicit blocker/fallback reason. These are guided host instructions, not a
permission sandbox or an automatic semantic verdict engine.
