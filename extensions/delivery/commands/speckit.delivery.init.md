---
description: "Discover project governance and initialize project-local Spec Kit Delivery configuration"
---

# Initialize Delivery

Inspect existing agent instructions, Constitution, contribution docs, CI, build/test/lint configuration, documentation generators, issue tracker instructions, ADR locations, and Spec artifact policy. Prefer existing project facts over distributed defaults.

Create or update the installed `delivery.yml` configuration without replacing existing governance. Record artifact policy (`tracked` or `ephemeral`), context paths, ADR paths, verification entry points, documentation sync settings, loop bounds, and active integration capability.

When Constitution is missing, propose principles derived from existing project rules; require review before treating them as governance. When Spec artifacts are ephemeral, record local-only resume and cross-worktree injection requirements.

The command is complete when every configured path and command was verified or explicitly left unset with a reason.
