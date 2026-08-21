# Agent-native router skills

Copy both sibling directories into a skill-discovery root without renaming them:

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
