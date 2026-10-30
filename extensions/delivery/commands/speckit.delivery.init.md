---
description: "Discover project governance and initialize project-local Spec Kit Delivery configuration"
---

# Initialize Delivery

Inspect existing agent instructions, Constitution, contribution docs, CI, build/test/lint configuration, documentation generators, issue tracker instructions, ADR locations, and Spec artifact policy. Prefer existing project facts over distributed defaults.

Create or update the installed `delivery-config.yml` configuration without replacing existing governance. Record artifact policy (`tracked` or `ephemeral`), context paths, ADR paths, verification entry points, documentation sync settings, loop bounds, and active integration capability.

Also discover and record the delivery slicing policy: whether the project can use native stacked pull requests, a merge queue, feature flags/kill switches, and branch protection that requires linear history. Draft `pr_slicing`, `slice_warn_files`, `slice_warn_lines`, `slice_requires_approval`, `stack_provider`, and `merge_policy` from verified project facts. Default to `pr_slicing: auto` with `slice: squash`, `final: merge-commit`, and `sync: merge`; leave a capability unset or explicitly `manual` when it cannot be verified. Do not assume GitHub stack support, flag infrastructure, or a merge queue exists.

Discover the project's existing GitHub PR template (`pull_request_template`), if any, and record its path. If none exists, ask whether to install the packaged static fallback at `.github/pull_request_template.md`; only with explicit approval and `install_pull_request_template: true` may you create it. Never overwrite an existing template. State clearly that this static template affects the GitHub UI, while `speckit.delivery.handoff` still writes the per-change body and the `--body-file` command that must be used to submit it.

Create or update `quality-config.yml` as a project-local draft. Discover candidate profiles in this order: existing quality policy, repository build/tool configuration, CI commands, local hooks, then documented developer commands. For each changed-code family, record only commands that were found and verified, plus the policy-source paths for architecture and style. For every documented rule, record an owner and credible mechanism: executable checks belong to Quality; DRY, ownership, and architecture belong to Standards Review, Simplify, or ADR. Leave unknown profiles or checks explicitly unset; do not guess a language toolchain. Set `unprofiled_changed_paths: block` unless the project deliberately reviews and changes that policy.

When Constitution is missing, propose principles derived from existing project rules; require review before treating them as governance. When Spec artifacts are ephemeral, record local-only resume and cross-worktree injection requirements.

The command is complete when every configured path and command was verified or explicitly left unset with a reason, every policy has an owner and mechanism or an explicit governance gap, and the owner has a reviewable quality-profile gap list.
