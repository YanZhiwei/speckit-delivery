# Agent-native skills

## Router skills

Copy both router directories into a skill-discovery root without renaming them:

```text
<skills-root>/
├── sd/
└── speckit-delivery/
```

In Codex, invoke `$sd <request>`. A host that renders user-invoked skills as
slash commands can expose the same entry as `/sd`.

`sd` is deliberately only a facade. It reads the canonical `speckit-delivery`
router through its relative sibling path, so install both directories together.

Codex renders installed Spec Kit extension commands as skills, not shell
executables. After `specify extension add`, the Delivery router appears as
`speckit-delivery-route` in the active skills root; do not use
`Get-Command speckit*` as a Codex availability check.

Claude Code exposes the same router as `/speckit-delivery-route`; OpenCode
exposes it as `/speckit.delivery.route`. Availability is a host-native
command/skill surface, not a PATH executable.

## Optional diagram renderers

`speckit.diagram.render` works with Mermaid alone. These two skills are
optional renderers and are **not** Bundle components; install one only when the
project wants a rendered asset:

| Directory | Upstream | Runtime | Output |
| --- | --- | --- | --- |
| `fireworks-tech-graph/` | [yizhiyanhua-ai/fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) `v1.2.0` | Python | SVG, PNG |
| `archify/` | [tt-a1i/archify](https://github.com/tt-a1i/archify) `v3.2.0` | Node.js >= 18 | interactive HTML |

Copy the whole directory into `<skills-root>/` and keep its `LICENSE` and
`SOURCE.md`. Both are MIT-licensed and unmodified; `SOURCE.md` records the tag,
commit, asset digest, and the single exclusion applied to `archify`.

They are never executed by installation, a hook, or a workflow. Invoking them
is an explicit choice made by `speckit.diagram.render` when
`diagram-config.yml` selects a renderer that is present.

Vendored trees are excluded from the repository Markdown-link and whitespace
checks because they are unmodified upstream copies with their own relative
links and formatting. Run the scoped check when reviewing this directory:

```bash
git diff --check -- . ':(exclude)skills/archify' ':(exclude)skills/fireworks-tech-graph'
```
