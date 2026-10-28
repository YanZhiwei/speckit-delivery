# Delivery Diagrams

Turns a reviewed change into one diagram that answers a specific question. It
is deliberately small: a command, a configuration file, and a view guide. No
renderer is bundled, so the extension works in any project.

## What it enforces

- One view per diagram, chosen from `before-after`, `call-path`, `impact`, or
  `sequence`.
- Every node and edge traced to a durable source; unproven relationships are
  omitted rather than guessed.
- Mermaid by default, so GitHub renders it in the pull-request body and the
  source stays reviewable.
- A rendered asset (`svg`, `png`, `html`) only when the project configured a
  renderer and the renderer is installed.
- `N/A` when the change has no durable structure to show.

It does not run tests, replace review, or add itself to a workflow. A diagram
is evidence, not a gate.

## Commands

| Command | Purpose |
| --- | --- |
| `speckit.diagram.render` | Choose one view, validate it against evidence, and emit Mermaid or a rendered asset. |

## Configuration

`diagram-config.yml` owns the format, renderer, output directory, and size
limits:

```yaml
format: mermaid
renderer: auto
output_dir: docs/diagrams
max_nodes: 15
max_edges: 25
renderer_paths:
  archify: ""
  fireworks: ""
```

`auto` discovers an installed skill under `.agents/skills`, `.claude/skills`,
or `.github/skills`, in the order `archify`, `fireworks`. When neither is
installed it keeps Mermaid and reports the fallback. `renderer: none` disables
rendering entirely.

## Renderers

| Renderer | Runtime | Output | Use |
| --- | --- | --- | --- |
| Mermaid (default) | none | fenced Markdown | pull-request body, ADR, quick review |
| `fireworks` | Python | SVG, PNG | committed architecture figure rendered inline |
| `archify` | Node >= 18 | interactive HTML | design review, explainer, demo link |

The optional skill copies live under `skills/` in this repository and are
installed per project, not by the Bundle. See
[skills/README.md](../../skills/README.md) for provenance and pinned versions.

## Handoff

`speckit.delivery.handoff` includes a **Design** section and accepts a Mermaid
block or an artifact link. When no diagram exists it writes `N/A` and why; it
never fabricates one.
