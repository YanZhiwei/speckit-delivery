---
description: "Review a task or batch diff against project standards and return a closure verdict"
---

# Standards Review

## Input

```text
$ARGUMENTS
```

Resolve the live base, HEAD, task or batch scope, and changed paths. Read only
the applicable policy sources configured in
`.specify/extensions/quality/quality-config.yml`, relevant ADRs, and the
changed code's owning-module documentation. Do not repeat executable checks
owned by `speckit.quality.check`.

Bind this semantic verdict to the actual reviewed contents (including staged,
unstaged, deleted, and relevant untracked paths) and applicable policy inputs.
Record deterministic fingerprint methods/manifests. Reuse only an original
exact-content/policy receipt; same HEAD/paths alone is insufficient. If reviewed
inputs change during analysis, refresh it or return blocked with the gap.

Exclude paths matching `excluded_paths` in the quality configuration and report
them as outside the governed scope; do not review them as production work.

Review semantic standards that require judgment: unnecessary duplicate logic,
ownership and directory boundaries, layer direction, single responsibility,
public-surface growth, comment intent, and whether the change alters an ADR.
Include these discipline checks:

- **Behavior, not implementation.** Tests must exercise the user-visible
  behavior. A test that still passes when every function returns nothing does
  not cover the change.
- **Cause, not symptom.** A guard or fallback that only hides a reproduced
  failure is blocking; the change must fix the cause and pin it with a test.
- **Subtract before adding.** New branching, state, or indirection without a
  reason the previous design could not express is a finding, not a style
  preference.
- **Verifiable units.** The task must be checkable on its own at the reported
  HEAD; work that only succeeds together with a later task is not closable.

Treat a documented project rule as blocking unless an approved, durable
exception applies. Treat a heuristic finding as blocking only when its impact
and remediation are evidenced; otherwise return it as a follow-up rather than
inventing a violation.

Return this exact report:

```text
STANDARDS_VERDICT: pass | blocked
HEAD: <sha>
SCOPE: <task-id, batch-id, or outgoing-diff>
PATHS: <repository-relative paths>
CONTENT_FINGERPRINT: <hash/method and reviewed-input manifest reference>
POLICY_FINGERPRINT: <hash/method for applicable policy inputs>
EXCLUDED_PATHS: <paths or none>
POLICY_SOURCES: <paths read>
FINDINGS:
- <id>: pass | blocked | follow-up — <rule, evidence, impact, remediation>
ADR_IMPACT: none | revise-proposed | propose | supersede
BLOCKERS:
- <id or none>: <reason>
FOLLOW_UP:
- <task, ADR action, or none>
```

For a task invocation, Ralph may close the task only when the verdict is
`pass`, the reported HEAD and original content/policy identities remain current,
and the scope covers every changed path. Never stamp current hashes on an old
verdict to imply its analysis covered new contents.
This command does not edit `tasks.md`; it reports its verdict to the
orchestrator.
