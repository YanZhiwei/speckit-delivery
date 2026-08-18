# Spec Kit Delivery

An evidence-driven delivery layer for [GitHub Spec Kit](https://github.com/github/spec-kit). It keeps Spec Kit's specification artifacts as the execution backbone and adds durable architecture decisions, task-based agent orchestration, convergence, simplification review, code review, documentation synchronization, release evidence, and a stable pull-request handoff.

> [!IMPORTANT]
> This repository is an early distribution scaffold (`0.1.0`). The guided workflows and prompt contracts are usable for evaluation. Provider-specific parallel execution and fully machine-driven semantic branching are intentionally tracked as later milestones.

[简体中文](README.zh-CN.md)

## Why

Core Spec Kit provides an excellent `specify → plan → tasks → implement` path. Real delivery also needs answers to questions that live beyond a feature's temporary artifacts:

- Which accepted architecture decisions constrain this work?
- Which decision should become the implementation baseline, and when is it final?
- Can independent tasks be dispatched safely without losing task ownership?
- Does the implementation converge on the specification after agents finish?
- Did the change introduce unused APIs, duplicate state, or speculative machinery?
- Which checks are credible for the actual outgoing diff?
- What durable explanation remains when feature artifacts are not committed?

Spec Kit Delivery supplies those missing delivery contracts without replacing Spec Kit or an existing project workflow.

## Workflow

```text
context → specify → clarify → plan → proposed ADR → tasks → analyze
        → Ralph → converge → simplify → docs sync → review
        → accepted ADR → evidence → PR handoff
```

Three lanes keep the process proportional:

| Lane | Use it for | Path |
| --- | --- | --- |
| Feature | New behavior, cross-module work, architectural change | Full SDD workflow |
| Bugfix | A reproducible defect with bounded scope | Assess → red test → fix → verify |
| Lightweight | Mechanical, documentation, or very small behavior-preserving changes | Scope → change → targeted evidence |

## What's included

```text
speckit-delivery/
├── bundle/                 # Installable Spec Kit bundle manifest
├── catalogs/               # Extension, workflow, and bundle catalogs
├── extensions/             # Independently versioned Spec Kit capabilities
│   ├── decision/
│   ├── ralph/
│   ├── review/
│   ├── simplify/
│   ├── evidence/
│   ├── docs-sync/
│   └── delivery/
├── workflows/              # Feature, bugfix, and lightweight workflows
├── skills/                 # Optional agent-native router and $sd facade
├── templates/              # Durable PR handoff template
├── docs/                   # Architecture and distribution contracts
├── evals/                  # Behavioral evaluation prompts
└── scripts/                # Reproducible component packaging
```

The package is integration-agnostic. Its portable surface is the Spec Kit
extension command family and workflows; Codex, Claude Code, OpenCode, and a
generic adapter render those commands in their own native formats. Integrations
with native delegation can run Ralph concurrently; all others use the same
dependency-ordered sequential protocol.

## One entry point

Use `$sd <request>` in Codex to start the optional agent-native SDD facade. In
harnesses that expose skills as slash commands, publish the same facade as
`/sd`. The facade loads `speckit-delivery`, which invokes the canonical
`speckit.delivery.route` extension command. The extension command—not the
facade—is the portable integration surface.

For the optional native entry point, copy both directories under `skills/` into
the same agent skill-discovery root. See [skills/README.md](skills/README.md)
for the required sibling layout.

## Requirements

- Spec Kit CLI `>=0.16.4`
- A Spec Kit-supported coding-agent integration
- Git
- Project build and test tools selected by the target repository

Check the CLI before installation:

```bash
specify self check
specify check
```

## Quick start: install and initialize a project

The following commands run in the **target project**, not in this distribution
repository. Initialize Spec Kit once, choosing the integration and script type
that match the target environment. For a PowerShell-based Codex project:

```powershell
cd D:\Repos\Acme\my-project
specify init . --integration codex --integration-options="--skills" --script ps
```

This creates `.specify/` and the integration's command/skill surface. It does
not replace existing project governance. Do not use `--force` unless replacing
an existing Spec Kit setup is intentional.

Choose one default integration per project. These are equivalent initialization
examples for the primary supported hosts:

| Host | Initialization | Native command surface |
| --- | --- | --- |
| Claude Code | `specify init . --integration claude --script sh` | Spec Kit skills in `.claude/skills/` |
| Codex | `specify init . --integration codex --integration-options="--skills" --script ps` | Spec Kit skills in `.agents/skills/` |
| OpenCode | `specify init . --integration opencode --script sh` | Spec Kit command files rendered for OpenCode |
| Other host | `specify init . --integration generic --integration-options="--commands-dir .myagent/commands" --script sh` | Chosen command directory |

After installing the Delivery extension, start the same route through the
surface rendered for the active host:

| Host | Route invocation |
| --- | --- |
| Claude Code | `/speckit-delivery-route <request>` |
| Codex | `$speckit-delivery-route <request>` or the optional `$sd <request>` facade |
| OpenCode | `/speckit.delivery.route <request>` |
| Generic adapter | Invoke the rendered `speckit.delivery.route` command file |

Use the command that `specify init` prints for the installed CLI version if it
differs from this table. `$sd` is ergonomics for compatible skill hosts, not a
portability requirement.

For a team that truly needs several hosts in one repository, install each
additional integration with `specify integration install <key>`, then run
`specify integration use <key>` when switching the active default so installed
extensions are re-rendered for that host. Prefer one default integration;
Spec Kit may require explicit `--force` for combinations it does not mark
multi-install safe.

Install this delivery layer from a local checkout by supplying absolute paths
to the components:

```powershell
$delivery = "D:\Repos\Github\speckit-delivery"

specify extension add --dev "$delivery\extensions\decision"
specify extension add --dev "$delivery\extensions\ralph"
specify extension add --dev "$delivery\extensions\review"
specify extension add --dev "$delivery\extensions\simplify"
specify extension add --dev "$delivery\extensions\evidence"
specify extension add --dev "$delivery\extensions\docs-sync"
specify extension add --dev "$delivery\extensions\delivery"

specify workflow add --dev "$delivery\workflows\feature-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\bugfix-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\lightweight-delivery\workflow.yml"
```

Then invoke `speckit.delivery.init` through the selected agent integration. It
discovers existing instructions, CI checks, ADR locations, documentation
projections, and whether Spec artifacts are `tracked` or `ephemeral`. Review
the resulting project-local delivery configuration before relying on it.

For the optional `$sd` entry point, install `skills/sd/` and
`skills/speckit-delivery/` together into the same agent skill-discovery root;
see [skills/README.md](skills/README.md). In Codex, the first practical run is:

```text
$sd Add an audit trail for privileged configuration changes.
```

The router inspects the project and selects Feature, Bugfix, or Lightweight;
it does not assume every request needs the full workflow.

## Establish the project constitution

The constitution is durable, project-local governance at
`.specify/memory/constitution.md`. Create it after `specify init`, before the
first substantial feature—not once per feature. Invoke the core
`speckit.constitution` command through the active integration (for example,
`$speckit-constitution` in Codex Skills mode) with concrete, non-negotiable
principles:

```text
Create the project constitution with these principles:
- Preserve backward-compatible public APIs unless an ADR records the migration.
- Every behavior change has focused automated evidence; CI owns the full suite.
- Secrets and user data never enter logs, fixtures, or client-side state.
- Material cross-module or persistence decisions require a durable ADR.
- Generated documentation is changed only through its configured source.
```

The command resolves the active template, preserves applicable amendments,
versions the constitution, writes a sync-impact comment, and only changes the
constitution. Review it like source: its rules must be testable and reflect
the repository's real CI and engineering practices. Amend it when governance
changes; feature-level design stays in ADRs and Specs.

## Run a feature delivery

Use `$sd <request>` for agent-native orchestration, or start the installed
workflow directly when its explicit steps suit the integration:

```bash
specify workflow run feature-delivery --input spec="Describe the change"
```

The Feature lane runs `specify → clarify → ADR resolution → plan → proposed
ADR → tasks → analyze`, then implementation and the verification loop. The
Proposed ADR remains editable through implementation and review. Only after
the reviewed repository HEAD matches the decision does it become Accepted.

## Run Ralph from tasks

Ralph is an execution coordinator, not a planning shortcut. Start it only
after `speckit.tasks` has produced and `speckit.analyze` has checked the active
feature's `tasks.md`:

```text
speckit.ralph.run
```

It reads `tasks.md` as the only scheduling source, finds dependency-ready
`Txxx` tasks, and respects file overlap, migrations, public contracts, and
unresolved decisions as blocking edges. With native delegation it can dispatch
independent task packets in parallel; otherwise it performs the same packets
sequentially with fresh task focus.

Each worker receives the task's acceptance condition, allowed scope, relevant
Spec/Plan/ADR excerpts, and expected verification. Workers report results;
the orchestrator verifies changed paths and evidence, then—and only then—marks
the task `[X]`. A failed task remains open and blocks dependents. If Spec files
are ignored, the excerpts are injected into every cross-worktree packet.

After Ralph, run convergence, simplification, review, and evidence collection.
Review findings become new or reopened tasks and re-enter the same
`analyze → Ralph → review` loop. The final ADR is reconciled against HEAD,
not against an earlier plan.

## Usage scenarios

### Feature: add Redis L2 caching

**Request:** “Add Redis-backed L2 caching. The repository already has an ADR
for process-local caching, and Spec files are gitignored.”

Run `$sd` with the request. It routes to **Feature**, retrieves the local-cache
ADR before planning, and produces a Proposed cache ADR once the plan selects a
direction. `speckit.tasks` creates the queue; Ralph may independently dispatch
serialization, cache adapter, invalidation, and test tasks only where their
files and contracts do not overlap. Because Spec artifacts are ephemeral,
every worker packet carries the assigned task plus the relevant cache and ADR
excerpts. After review, finalize a self-contained Accepted ADR that explains
the Redis and local-cache relationship without citing the ignored Spec files.

### Bugfix: prevent duplicate retry notifications

**Request:** “Retries sometimes send users the same notification twice.”

Run `$sd` with the request. It routes to **Bugfix**, first establishes a
reproduction and a red regression test, then identifies the retry/idempotency
owner and applies the smallest corrective change. It creates an ADR only if
the diagnosis changes a durable cross-module, persistence, or public-contract
decision. Verification records the regression test and relevant focused checks;
the full Feature ceremony is not required for a bounded fix.

### Lightweight: correct a documentation heading

**Request:** “Fix a misspelled heading in one Markdown file and prepare it for
review.”

Run `$sd` with the request. It routes to **Lightweight**, constrains the change
to the named document, runs the configured documentation or link check, and
prepares a concise evidence-backed handoff. It does not create Spec artifacts,
an ADR, or a Ralph queue for a behavior-preserving typo correction.

### Direct Ralph: resume verified task execution

**Situation:** Planning is complete, `tasks.md` has passed analysis, and tasks
`T014` and `T017` are dependency-ready while `T015` changes the same public
contract as `T014`.

Run `speckit.ralph.run`. Ralph can dispatch `T014` and `T017` when their file
and contract scopes are independent; it holds `T015` until `T014` is verified.
Workers return their changes and evidence, while Ralph alone updates task
checkboxes. If `T014` fails verification, it stays open and its dependents
remain blocked with an explicit reason.

## Local development installation

If the current directory is the distribution checkout rather than a target
project, use the same commands above with the appropriate target paths. The
absolute-path form avoids accidentally installing the extensions into the
distribution repository itself.

```bash
specify bundle validate --path ./bundle
specify bundle build --path ./bundle --output ./dist
```

## Release installation

Releases publish each extension as a root-layout zip, expose pinned catalogs, and publish the bundle artifact. Add the versioned catalogs before installing the bundle:

```bash
specify extension catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.0/catalogs/extensions.json \
  --name speckit-delivery --install-allowed

specify workflow catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.0/catalogs/workflows.json \
  --name speckit-delivery

specify bundle catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.0/catalogs/bundles.json \
  --id speckit-delivery --policy install-allowed

specify bundle install speckit-delivery
```

The remote repository and release do not exist until the maintainer explicitly publishes them. Local creation of this project does not create or push a GitHub repository.

## Commands

| Capability | Commands |
| --- | --- |
| Decision memory | `speckit.decision.context`, `.propose`, `.finalize`, `.check` |
| Task execution | `speckit.ralph.run` |
| Code review | `speckit.review.run` |
| Simplification | `speckit.simplify.scan`, `.verify` |
| Evidence | `speckit.evidence.collect` |
| Documentation | `speckit.docs-sync.run` |
| Routing and handoff | `speckit.delivery.route`, `.handoff` |

## Durable and ephemeral artifacts

The project chooses whether `spec.md`, `plan.md`, and `tasks.md` are committed. Durable records must remain understandable at repository HEAD:

- Constitution: cross-feature non-negotiable project rules
- Issue: problem, scope, and acceptance contract
- ADR: long-lived architectural decision and rationale
- Source/tests/docs: implemented behavior
- PR: final change summary, risk, and verification evidence

When Spec Kit artifacts are ignored, Ralph must inject the assigned task and relevant artifact excerpts into each worker. Cross-worktree workers must never assume ignored files exist in their worktree.

See [Architecture](docs/architecture.md), [Artifact lifecycle](docs/artifact-lifecycle.md), and [Distribution](docs/distribution.md).

## Design principles

- Requirements before implementation details.
- Evidence before completion claims.
- One task queue: `tasks.md` is Ralph's scheduling source.
- One durable owner for each architectural decision.
- Review the real base/head diff, not a remembered change set.
- Simplification requires production-consumer evidence and net deletion.
- Integration-specific acceleration with a generic sequential fallback.

## Status and roadmap

- `0.1.x`: prompt contracts, guided workflows, catalogs, release packaging, structural validation
- `0.2.x`: machine-readable workflow state and semantic result gates
- `0.3.x`: provider adapters for parallel Ralph execution
- `1.0.0`: clean-project installation evidence across supported integrations

See [CHANGELOG.md](CHANGELOG.md) for released changes.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). New commands should remain narrow, have an explicit completion criterion, and include at least one behavioral evaluation prompt.

## Security

Read [SECURITY.md](SECURITY.md) before adding shell execution, URL fetching, repository publishing, or credential-dependent providers.

## License

[MIT](LICENSE)
