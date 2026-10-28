---
description: "Assemble a short, evidence-backed map of the implementation the current change touches"
---

# Delivery Code Context

Produce a brief that answers: which existing implementation owns this change,
who calls it, and which tests already cover it. It is planning and diagnosis
input, not a correctness proof.

## Input

```text
$ARGUMENTS
```

`$ARGUMENTS` names a feature, bug report, symbol, or path. When it is empty,
use the current outgoing diff and say so.

## Configuration

Read `.specify/extensions/delivery/delivery-config.yml` when it exists:

- `code_context: auto` (default) uses the local index when present.
- `code_context: off` skips the lookup and reports `CODE_CONTEXT: off`.

Never run `codegraph init`. Creating an index is the project owner's decision,
not a side effect of delivery.

## Procedure

1. Record the current `HEAD`.

2. Detect an index at `.codegraph/`. When it is absent, continue with the
   fallback in step 6 and report `INDEX: absent`.

3. Run `codegraph status`. When the index is stale, run `codegraph sync` once
   and re-check. If the sync fails or the index stays stale, keep the result,
   set `INDEX: stale`, and list what may have moved in `GAPS`.

4. Derive search terms from the input, the changed paths, and the symbols named
   by the Spec, plan, or bug report. Prefer domain names over generic words.

5. Use the graph to collect, in this order:

   - `codegraph explore "<terms>"` for entry points and owners;
   - `codegraph callers <symbol>` for direct consumers;
   - `codegraph affected <path>` for tests the change can reach.

   Keep the five most relevant entry points, five callers, and every affected
   test that maps to a changed path. Do not paste the whole graph, file bodies,
   or unrelated neighbors.

6. Fallback without an index: search the changed paths and their direct
   importers with the project's own tools. Report `CODE_CONTEXT: partial` and
   name the relationships you could not verify. Never present a grep match as a
   call edge.

7. When `.specify/delivery/<feature-or-bug>/` exists, write the brief to
   `code-context.md` there. Otherwise return it inline. Never create a feature
   directory just to hold this file.

8. Return the result block.

## Output

```text
CODE_CONTEXT: found | partial | unavailable | off
HEAD: <sha>
INDEX: fresh | stale | absent | off
ENTRY_POINTS:
- <symbol> @ <file:line> — <ownership or behavior>
CALLERS:
- <symbol> @ <file:line> — <contract it depends on>
AFFECTED_TESTS:
- <path> — <how it reaches the change>
GAPS:
- <unverified relationship, ambiguity, or stale area>
```

Follow the block with at most three sentences of guidance for the next command:
what to read, what to change, and what to verify.

## Guardrails

- The graph proves structure, never correctness, types, or passing tests.
- A name match is not a call edge. Ambiguous symbols go to `GAPS`, not into a
  fabricated call path.
- Do not upload code, query a remote service, or commit `.codegraph/`.
- Do not expand scope: report the owners the change touches, not the whole
  repository.
- A missing tool is a downgrade, not a blocker: `unavailable` with the fallback
  evidence is a valid result.

## Completion

The command is complete when `HEAD`, index state, entry points, callers,
affected tests, and gaps are reported, and every relationship either cites a
graph result or is explicitly marked unverified.
