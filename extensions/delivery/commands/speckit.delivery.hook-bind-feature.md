---
description: "Spec Kit after_specify hook: bind the actual Core Feature directory to the active Delivery run"
---

# Delivery Hook: after_specify

Event adapter for Spec Kit's `after_specify` extension hook. It binds the
Feature Core just created to the active Feature Delivery run so later owners
consume the same canonical paths. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run, a
   non-Feature lane, or an ambiguous selection, stop with the shared output;
   never guess a Feature from `specs/` recency.
2. **Reuse:** when the run's bindings already name `spec`, `plan`, and `tasks`
   under one Feature directory and the bound `spec.md` exists at that exact
   path, report `ACTION: reused`. Do not rebind or relocate anything.
3. **Bind from the packet:** when the canonical exploration packet contains
   exactly one `FEATURE_DIR:`/`FEATURE_PATH:` marker emitted by Core Specify,
   run
   `bind --run <id> --feature-from-packet .specify/delivery/<id>/exploration.md`.
4. **Bind from actual event context:** otherwise use the Feature directory Core
   Specify actually reported in this session and run
   `bind --run <id> --feature-dir <actual-project-relative-directory>`.
   The helper rejects relocation and lane mismatches; do not retry with a
   different directory to make the error disappear.
5. When neither the packet marker nor an actual reported directory exists,
   report `ACTION: blocked` with the missing identity and ask the user to
   supply the exact Feature path; create nothing.

## Completion

The adapter is complete when the run binds the actual Feature's
`spec.md`/`plan.md`/`tasks.md` paths (reused or newly bound), or when it
reports a skipped/blocked result. Binding is identity transport only: it is not
clarification, design approval, or permission to plan or implement.
