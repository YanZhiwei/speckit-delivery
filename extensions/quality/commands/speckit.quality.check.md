---
description: "Run applicable project quality profiles and return a task-closure verdict"
---

# Project Quality Check

## Input

```text
$ARGUMENTS
```

Determine the repository HEAD, base/head diff, changed paths, and (when
provided) the task identifier. Read
`.specify/extensions/quality/quality-config.yml` when present, then read only
the configured policy sources relevant to the changed paths.

Match every changed source path to one or more `profiles[].match` globs. A
profile's commands are project-owned facts: run only commands recorded in the
configuration or reuse a passing pre-commit/CI hook only when its repository
HEAD and changed-path scope exactly match. Expand `{changed_files}` and
`{affected_tests}` only when their values are known; never execute a literal
placeholder or invent a package-manager command.

Apply the following closure rules:

1. Run every applicable executable command. A failing command is `blocked`.
2. If a changed source path has no profile and `unprofiled_changed_paths` is
   `block`, return `blocked` with `quality-profile-missing`; do not infer a
   language default.
3. If a configured required command cannot run, return `blocked` with the
   command, reason, and the project change needed to make it executable.
4. Enforce profile rules only where the repository has a credible mechanism
   (for example a configured complexity checker). Otherwise report the rule
   as an explicit governance gap, never as a passing check.
5. Treat DRY, ownership, public-surface, directory-boundary, and architecture
   concerns as semantic findings for `speckit.simplify.scan`,
   `speckit.review.run`, or the ADR lifecycle. This command checks their
   configured mechanical policy; it does not silently waive semantic review.

Return a compact, machine-readable report in this exact shape:

```text
QUALITY_VERDICT: pass | blocked
HEAD: <sha>
SCOPE: <task-id or outgoing-diff>
PATHS: <repository-relative paths>
PROFILES: <matched profile ids>
CHECKS:
- <profile/check>: pass | fail | not-applicable | unavailable — <evidence>
BLOCKERS:
- <id or none>: <reason>
FOLLOW_UP:
- <task, config change, or none>
```

For a task invocation, the caller may mark the task complete only when
`QUALITY_VERDICT: pass`, the reported HEAD is still current, and the reported
scope covers the task's changed paths. Otherwise leave the task open and block
dependents as appropriate.

The command is complete only after it returns that report; it never edits
`tasks.md`.
