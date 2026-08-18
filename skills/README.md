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
