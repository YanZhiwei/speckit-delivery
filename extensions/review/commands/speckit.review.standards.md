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

Review semantic standards that require judgment: unnecessary duplicate logic,
ownership and directory boundaries, layer direction, single responsibility,
public-surface growth, comment intent, and whether the change alters an ADR.
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
`pass`, the reported HEAD is current, and the scope covers every changed path.
This command does not edit `tasks.md`; it reports its verdict to the
orchestrator.
