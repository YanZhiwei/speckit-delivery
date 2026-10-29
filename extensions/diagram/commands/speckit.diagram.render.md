---
description: "Turn a change into an evidence-backed diagram, Mermaid by default and an optional rendered asset"
---

# Delivery Diagram

Produce one diagram that answers a question about the current change. The
diagram is review evidence: it must be traceable to durable sources and must
never be invented to look complete.

## Input

```text
$ARGUMENTS
```

`$ARGUMENTS` names a feature, issue, pull request, architecture question, or
path. When it is empty or too vague, use the current outgoing diff and say so.

## Configuration

Read `.specify/extensions/diagram/diagram-config.yml` when it exists. Otherwise
use these defaults:

```text
format: mermaid | renderer: auto | output_dir: docs/diagrams
max_nodes: 15 | max_edges: 25
```

`format` selects the artifact. `renderer` selects an optional installed tool.
They are independent: an `svg` request without an installed renderer is a
recorded gap, not a reason to draw something else.

## Evidence

Use only durable sources:

- the Spec, plan, or ADR that owns the decision;
- `git diff --stat` and the changed paths at the current HEAD;
- the project architecture or boundary document that owns the component map.

Do not infer runtime topology from file, package, or symbol names. Omit an
unproven relationship instead of guessing. Never include secrets, tokens,
private URLs, customer identifiers, or unredacted payloads.

## Procedure

1. State the question in one sentence.

2. Choose exactly one view, using
   [view selection](../references/view-selection.md):
   - `before-after` when behavior, ownership, or a boundary changes;
   - `call-path` when control flow between components changes;
   - `impact` when dependents, compatibility, or migration is the risk;
   - `sequence` when ordering or failure handling across actors matters.

3. List the nodes and edges with their evidence source. Keep every node to one
   responsibility and every edge label to one short phrase. A node that cannot
   be traced to evidence is removed, not marked "unknown".

4. Emit Mermaid with `flowchart` for `before-after` and `call-path`, and
   `sequenceDiagram` for `sequence`. Use `classDef added` and
   `classDef changed` only when the view includes a before/after comparison.
   Stay within `max_nodes` and `max_edges`; split or narrow the view instead of
   exceeding them.

5. Validate the draft: no orphan nodes, no cycles that the evidence does not
   support, no duplicate edges, and no label longer than eight words.

6. Render only when `format` is `svg`, `png`, or `html`. For `mermaid`, skip
   this step and report `RENDERER: none`.

   - `none`: stop and report `RENDERER: none`.
   - `archify`: require `<skills-root>/archify/SKILL.md` and Node >= 18.
   - `fireworks`: require `<skills-root>/fireworks-tech-graph/SKILL.md`.
   - `auto`: use the first installed renderer in the order `archify`,
     `fireworks`; when none is installed, keep Mermaid and report the fallback.

   `<skills-root>` is the first existing directory among `.agents/skills`,
   `.claude/skills`, and `.github/skills`, unless `renderer_paths` overrides it.
   When the selected renderer cannot produce the requested format (for example
   `fireworks` with `html`), stop with `RENDERER: incompatible`, keep the
   Mermaid draft, and report the mismatch. Do not download, install, upgrade,
   or modify a renderer.

7. Write the artifact under `output_dir` using a stable slug:
   `<slug>.md` for Mermaid, or `<slug>.<format>` for a rendered asset. Create
   the directory when it is missing. Never overwrite an unrelated file.

8. Return the result block and the exact Markdown to paste into the pull
   request or ADR.

## Output

```text
DIAGRAM_QUESTION: <one sentence>
DIAGRAM_VIEW: <before-after | call-path | impact | sequence>
DIAGRAM_FORMAT: <mermaid | svg | png | html>
DIAGRAM_PATH: <repository-relative path | N/A>
RENDERER: <archify | fireworks | none | unavailable | incompatible>
EVIDENCE: <comma-separated durable sources>
```

Follow the block with one caption line and the embed:

- Mermaid: a fenced `mermaid` block;
- rendered asset: a Markdown image embed whose target is the artifact path, and
  a relative link for `html`.

## Guardrails

- A diagram is evidence, never a substitute for tests, review, or a passing
  quality gate.
- Return `DIAGRAM_PATH: N/A` with the reason when the change has no durable
  structure to show, for example a typo or a dependency bump.
- Do not add yourself to a workflow, hook, or CI step; this command is invoked
  deliberately.
- Do not edit the Spec, plan, or ADR to fit the picture.
- Keep generated HTML out of the pull-request body; link it instead.

## Completion

The command is complete when the question, view, format, path (or the reason
for `N/A`), renderer status, and evidence list are reported, and every node and
edge in the artifact traces to one of the cited sources.
