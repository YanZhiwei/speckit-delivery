# Project Quality Gate

Turns project-local quality policy into a task-closure verdict. It is generic:
the target repository owns its tools, commands, path globs, and standards in
`quality-config.yml`; this extension supplies the execution and blocking
contract.

## What it enforces

- Applicable formatter, lint, type, test, complexity, and similar executable
  checks.
- A blocking result when changed source paths have no quality profile, or a
  configured required check cannot run.
- Reuse of a passing hook only when HEAD and changed-file scope match exactly.

It does not replace semantic design review. DRY, redundant APIs, unclear
ownership, and dependency boundaries remain findings for Simplify, Review, and
(when durable) ADRs. Directory layout becomes a mechanical gate only when the
project supplies an explicit checker (for example `pnpm check:test-layout`);
otherwise it remains a Standards Review finding.

## Configure a project

Run `speckit.delivery.init`, then review
`.specify/extensions/quality/quality-config.yml`. Add a profile for each
language or code family and use commands already proven by the repository's
CI, hooks, or documented local workflow. Do not copy the commented examples
unchanged: select the project package manager and test paths deliberately.

See [the configuration guide](../../QUALITY-GATE.md) for field semantics,
language-specific style ownership, and complete Python, TypeScript, Go, Java,
and .NET examples.

Invoke `speckit.quality.brief task=T014 files=backend/services/api.py` before
editing to give the worker the applicable rules. Invoke
`speckit.quality.check task=T014` after the focused change, or without a task
identifier for the outgoing-diff gate. Ralph uses the returned verdict before
it closes a task.
