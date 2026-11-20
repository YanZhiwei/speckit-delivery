# Agent-native entry points

## Installed router and shortcut

Starting with Delivery `0.4.0`, the extension declares `sd` as an alias of
`speckit.delivery.route`. Installing the Bundle or Delivery extension renders
the native entries below; no facade skill or manual command copy is required.
Copilot's pinned Skills installer provides the full entry only:

| Host | Installed shortcut | Full entry |
| --- | --- | --- |
| OpenCode | `/sd <request>` | `/speckit.delivery.route <request>` |
| Codex Skills mode | `$speckit-sd <request>` | `$speckit-delivery-route <request>` |
| Claude Code | `/speckit-sd <request>` | `/speckit-delivery-route <request>` |
| GitHub Copilot (default Skills mode) | Use the full entry | `/speckit-delivery-route <request>` |
| Gemini CLI | `/sd <request>` | `/speckit.delivery.route <request>` |
| Cursor (`cursor-agent`) | `/speckit-sd <request>` | `/speckit-delivery-route <request>` |

Spec Kit `>=1.2.3` prefixes skill names with `speckit-`, including aliases. OpenCode
keeps the declared command name and creates `.opencode/commands/sd.md`; Gemini
creates `.gemini/commands/sd.toml` and uses the native `{{args}}` placeholder.
Where an alias is rendered, it and the full command share the same router source and belong
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

## Installation and execution coverage

The [installation probe](../scripts/test_bundle_install.py) owns the six tested
layouts: Codex, Claude Code, OpenCode, GitHub Copilot, Gemini CLI, and Cursor.
The [CI matrix](../.github/workflows/host-install.yml) derives its host axis from
that probe and requires each layout on Linux and Windows for PR validation and
before publishing. Release preparation runs all six against the stamped working
tree on Linux. All use Spec Kit `1.2.3` as the pinned validation fixture.

Keep three kinds of evidence separate:

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Workflow/catalog compatibility | The integration is admitted by the three workflows | Installation, dispatch, or model behavior |
| Clean-project installation probe | Built archives, rendered prompts, native arguments, entry ownership, installed workflows/runtime, upgrade/reinstall/removal, and configuration preservation | Authentication, actual host CLI execution, or semantic delivery quality |
| Recorded live-host smoke run | The observed host/version completed the recorded scenario | Other hosts, operating systems, or scenarios |

The Generic adapter remains available for custom command directories; it is not
part of the native six-host matrix. Copilot's legacy `--commands` layout is also
outside this matrix. Use default Skills mode for the documented Copilot path.
Spec Kit `1.2.3` does not render manifest aliases through Copilot's Skills
registration path, so use the canonical `/speckit-delivery-route` there. Its
probe verifies canonical entry ownership, Bundle update, reinstall/removal, and
configuration preservation; legacy alias adoption is checked on the other five.

Interactive IDE skills and process dispatch have different prerequisites.
Copilot and Cursor can install IDE skills without their CLIs; running
`specify workflow run` additionally needs the corresponding authenticated
`copilot` or `cursor-agent` executable. Other hosts likewise require their actual
CLI and authentication for process dispatch. `--ignore-agent-tools` in the
installation probe deliberately checks distribution without invoking models.

The portable execution baseline needs file access, the project's shell/Python,
and Git. The [Ralph contract](../extensions/ralph/README.md#execution-contract)
owns sequential execution and worktree requirements; the
[Reviewer contract](../extensions/review/templates/reviewer.md) owns independence
and accepted self-review limits. Installing a Skill does not supply those
capabilities or waive their gates. Missing capabilities must remain explicit.
Use the [live-host smoke protocol](../evals/README.md#live-host-smoke-protocol)
before claiming end-to-end support for a host.

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
