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
HEAD, scope, original checked contents, and check configuration exactly match
the current inputs. A HEAD/path-only receipt cannot establish this: rerun the
check rather than relabeling old results with a new fingerprint. Expand `{changed_files}` and
`{affected_tests}` only when their values are known; never execute a literal
placeholder or invent a package-manager command.

Before matching, remove paths matching `excluded_paths` in the configuration.
List them in `EXCLUDED_PATHS`; do not execute a profile, report a pass, or raise
a profile gap for them. Exclusion is scope control, never a quality pass.

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
   `speckit.review.run`, or the ADR lifecycle—unless the project explicitly
   configures a credible checker for a narrow structural rule such as test
   layout. This command checks that configured mechanism; it does not silently
    waive semantic review.

## Execution identity and reuse

Capture each check's actual input identity before execution and verify it again
afterwards. Hash a deterministic manifest of relevant paths/modes/bytes, including
index/worktree distinctions, deletions, and relevant untracked files. Include
production dependencies, test inputs/fixtures, and generated inputs consumed by
that check; changed filenames alone are not its checked-input set. Record the
manifest/hash method and justified exclusions. Use a conservative relevant tree
when dependencies cannot be narrowed; if identity is unavailable, do not reuse.

Separately fingerprint the check definition/configuration: resolved command,
quality profile and policy/tool config, working directory, relevant non-secret
environment/tool versions, and test selection. A staged-only hook is reusable
only when its tested staged bytes also match current reviewed worktree bytes.
Output files/caches may be excluded explicitly; production/test/config changes
may not. Do not expose secrets in fingerprints' human-readable manifests.

The original execution receipt records its checked-input/config fingerprints,
scope, command, start/end identity, and exit status. Reuse only that exact passing
receipt when all identities match; otherwise execute the affected check. A new
checkout hash attached to an old hook result is not evidence of execution on new
contents. Input changes during execution make the result blocked until a stable
check is established. Missing identity/tools cannot produce a closure pass.

Return a compact, machine-readable report in this exact shape:

```text
QUALITY_VERDICT: pass | blocked
HEAD: <sha>
SCOPE: <task-id or outgoing-diff>
PATHS: <repository-relative paths>
CONTENT_FINGERPRINT: <hash/method and checked-input manifest reference>
CHECK_CONFIG_FINGERPRINT: <hash/method for effective check configuration>
EXCLUDED_PATHS: <paths or none>
PROFILES: <matched profile ids>
CHECKS:
- <profile/check>: pass | fail | not-applicable | unavailable — <evidence>
CHECK_RECEIPTS:
- <profile/check>: <original execution receipt; checked-input/config hashes, command, scope, start/end identity, exit status, executed/reused and source>
BLOCKERS:
- <id or none>: <reason>
FOLLOW_UP:
- <task, config change, or none>
```

For a task invocation, the caller may mark the task complete only when
`QUALITY_VERDICT: pass`, the original check receipts still match current contents
and effective configuration, HEAD is current, and scope covers the task's changed
paths. Otherwise leave the task open and block
dependents as appropriate.

The command is complete only after it returns that report; it never edits
`tasks.md`.
