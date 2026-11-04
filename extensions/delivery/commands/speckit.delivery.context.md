---
description: "Assemble a short, evidence-backed map of the implementation the current change touches"
---

# Delivery Code Context

Produce a brief that answers: which existing implementation owns this change,
who calls it, and which tests already cover it. It is planning and diagnosis
input, not a correctness proof.

## Input and run/output binding

```text
$ARGUMENTS
```

For a direct delivery workflow, require explicit
`lane=feature|bugfix|lightweight` and `delivery_run=<id>`. Validate the run as a
safe single path segment and use the exact canonical paths
`.specify/delivery/<delivery_run>/exploration.md` and
`.specify/delivery/<delivery_run>/code-context.md`; the run id is not a Feature
slug. A standalone invocation without `delivery_run` may use the current
outgoing diff, but returns the brief inline, reports `CODE_CONTEXT_PATH: inline`,
and must not infer another active Feature or create a directory. Never relocate
the Explore packet when a Feature or Bug identity becomes known.

Per-run operational state/results belong under
`.specify/delivery/<delivery_run>/runtime/`, while the code-context report stays
at the run root. Use `.specify/extensions/delivery/templates/runtime.md` as the
central owner. When either `runtime_stage` or `runtime_result` is supplied, require the
canonical `delivery_run`, read `.specify/extensions/delivery/templates/runtime.md`
in full, and follow that runtime contract; do not invent helper flags, paths, or
result schemas. With neither argument, do not create runtime state here.

`$ARGUMENTS` may also name a feature, bug report, symbol, or path. When it is
empty, use the current outgoing diff and say so.

## Configuration

Read `.specify/extensions/delivery/delivery-config.yml` when it exists:

- `code_context: auto` (default) uses the local index when present.
- `code_context: off` skips the lookup and reports `CODE_CONTEXT: off`.

Never run `codegraph init`. Creating an index is the project owner's decision,
not a side effect of delivery.

## Procedure

1. Record the current `HEAD`, lane, and (when supplied) `delivery_run`.

2. When a run is supplied, read the exact canonical Explore packet at
   `.specify/delivery/<delivery_run>/exploration.md` and verify its recorded run
   identity, reviewed HEAD/working-tree snapshot, mapped paths, and gaps. A
   missing or mismatched packet is a blocker; do not discover another Feature or
   move the packet. In a standalone no-run invocation, use only the supplied
   request/current diff and return inline.

3. Reuse the current Explore mapping for entry points, owners, callers, affected
   paths, and known tests when its inputs are still current and it contains no
   concrete unresolved gap. Do not repeat broad discovery merely because Code
   Context was invoked as a later workflow step.

4. Only when the Explore mapping has a concrete relationship gap, stale HEAD or
   changed-path identity, or an explicitly requested missing area, refresh the
   narrow affected portion. Detect an index at `.codegraph/`; when absent,
   report `INDEX: absent` and use the project's own source/import/test tools.
   Never run `codegraph init`. If an index is stale, run `codegraph sync` once
   and re-check; if it fails or remains stale, set `INDEX: stale` and list the
   affected uncertainty in `GAPS`.

5. For a needed graph refresh, derive domain search terms from the Explore
   packet, input, changed paths, and named Spec/plan/bug symbols. Use the graph
   in this order: `codegraph explore "<terms>"`, then callers for relevant
   symbols, then affected tests for changed paths. Keep the five most relevant
   entry points and callers plus every affected test mapping. Do not paste whole
   file bodies or unrelated neighbors.

6. Without an index, search changed paths and direct importers with project tools.
   Report `CODE_CONTEXT: partial` and name relationships not verified. A name or
   grep match is not a call edge.

7. When a run is supplied, write or update only
   `.specify/delivery/<delivery_run>/code-context.md`; do not write a Feature- or
   Bug-named alternative. With no run, return the brief inline and do not create
   any directory. Record runtime operational results only through the central
   runtime contract.

8. Return the result block.

## Output

```text
CODE_CONTEXT: found | partial | unavailable | off
LANE: <feature|bugfix|lightweight|standalone>
DELIVERY_RUN: <id or none>
CODE_CONTEXT_PATH: <.specify/delivery/<id>/code-context.md or inline>
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
- The current Explore mapping is the default source of code-context structure;
  refresh only a concrete gap or stale input and state what changed.
- Do not write `tasks.md`, source, tests, or another run's packet. The only
  canonical report write is the supplied run's `code-context.md`.

## Completion

The command is complete when `HEAD`, index state, entry points, callers,
affected tests, and gaps are reported, and every relationship either cites a
graph result or is explicitly marked unverified.
