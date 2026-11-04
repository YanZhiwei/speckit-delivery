# Agent-native entry points

## Installed router and shortcut

Starting with Delivery `0.4.0`, the extension declares `sd` as an alias of
`speckit.delivery.route`. Installing the Bundle or Delivery extension renders
both names through the active host; no facade skill or manual command copy is
required:

| Host | Installed shortcut | Full entry |
| --- | --- | --- |
| OpenCode | `/sd <request>` | `/speckit.delivery.route <request>` |
| Codex Skills mode | `$speckit-sd <request>` | `$speckit-delivery-route <request>` |
| Claude Code | `/speckit-sd <request>` | `/speckit-delivery-route <request>` |

Spec Kit 1.2.3 prefixes skill names with `speckit-`, including aliases. OpenCode
keeps the declared command name and creates `.opencode/commands/sd.md`.
The alias and full command are rendered from the same router source and belong
to Delivery in the installation registry. Refreshing or removing the extension
refreshes or removes both entries; there is no second lifecycle prompt to
maintain.

Versions through `0.3.2` do not declare this alias. Follow the
[existing-Bundle upgrade steps](../README.en.md#upgrade-an-existing-bundle) to
replace the version-pinned catalogs and run `specify bundle update speckit-delivery`.
OpenCode reloads command files automatically; if an open command list is stale,
close and reopen it or run `/reload`.

Availability is a host-native command/skill surface, not a PATH executable.
Do not use `Get-Command speckit*` to check it.

## Optional exact `$sd` facade

For Codex users who specifically want `$sd` instead of the automatically
installed `$speckit-sd`, the existing facade skills remain optional.

Copy both router skill directories into a skill-discovery root without renaming
them:

```text
<skills-root>/
├── sd/
└── speckit-delivery/
```

Invoke `$sd <request>`. The `sd` facade reads its sibling
`speckit-delivery/SKILL.md`, which delegates to the installed
`speckit-delivery-route` skill in the active skills root. Install both facade
directories together, plus the Delivery extension; the facade adds no lifecycle
policy.

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
