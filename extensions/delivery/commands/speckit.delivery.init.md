---
description: "Discover project governance and initialize project-local Spec Kit Delivery configuration"
---

# Initialize Delivery

Inspect existing agent instructions, Constitution, contribution docs, CI, build/test/lint configuration, documentation generators, issue tracker instructions, ADR locations, and Spec artifact policy. Prefer existing project facts over distributed defaults.

Create or update the installed `delivery-config.yml` configuration without replacing existing governance. Record artifact policy (`tracked` or `ephemeral`), context paths, ADR paths, verification entry points, documentation sync settings, loop bounds, and active integration capability.

Create or update `quality-config.yml` as a project-local draft. Discover candidate profiles in this order: existing quality policy, repository build/tool configuration, CI commands, local hooks, then documented developer commands. For each changed-code family, record only commands that were found and verified, plus the policy-source paths for architecture and style. For every documented rule, record an owner and credible mechanism: executable checks belong to Quality; DRY, ownership, and architecture belong to Standards Review, Simplify, or ADR. Leave unknown profiles or checks explicitly unset; do not guess a language toolchain. Set `unprofiled_changed_paths: block` unless the project deliberately reviews and changes that policy.

When Constitution is missing, propose principles derived from existing project rules; require review before treating them as governance. When Spec artifacts are ephemeral, record local-only resume and cross-worktree injection requirements.

The command is complete when every configured path and command was verified or explicitly left unset with a reason, every policy has an owner and mechanism or an explicit governance gap, and the owner has a reviewable quality-profile gap list.
