# Spec Kit Delivery

An evidence-driven delivery layer for [GitHub Spec Kit](https://github.com/github/spec-kit). It keeps Spec Kit's specification artifacts as the execution backbone and adds durable architecture decisions, project-local quality gates, task-based agent orchestration, convergence, simplification review, code review, documentation synchronization, release evidence, and a stable pull-request handoff.

> [!IMPORTANT]
> This repository is an early distribution scaffold (`0.1.0`). The guided workflows and prompt contracts are usable for evaluation. Provider-specific parallel execution and fully machine-driven semantic branching are intentionally tracked as later milestones.

[English] · [简体中文](README.zh-CN.md)

## At a glance

| Need | Start here |
| --- | --- |
| Start a change from an agent host | `$sd <request>` or `/sd <request>` |
| Install the portable workflow | [Quick start](#quick-start-install-and-initialize-a-project) |
| Rapidly configure an existing project | [Quick SD Configuration](QUICK-CONFIGURATION.md) |
| Configure language quality gates | [Quality Gate guide](QUALITY-GATE.md) · [Examples](examples/quality-gate/) |
| Understand ADR, Ralph, and evidence ownership | [Architecture](ARCHITECTURE.md) |
| Package or release the bundle | [Distribution](DISTRIBUTION.md) |

The portable contract is the `speckit.*` extension command family. `$sd` and
`/sd` are optional host-native facades over that contract.

## Why

Core Spec Kit provides an excellent `specify → plan → tasks → implement` path. Real delivery also needs answers to questions that live beyond a feature's temporary artifacts:

- Which accepted architecture decisions constrain this work?
- Which decision should become the implementation baseline, and when is it final?
- Can independent tasks be dispatched safely without losing task ownership?
- Does the implementation converge on the specification after agents finish?
- Did the change introduce unused APIs, duplicate state, or speculative machinery?
- Which checks are credible for the actual outgoing diff?
- How do local complexity, comments, lint, type, and test rules block a task
  from closing instead of remaining advisory?
- What durable explanation remains when feature artifacts are not committed?

Spec Kit Delivery supplies those missing delivery contracts without replacing Spec Kit or an existing project workflow.

## Workflow

```text
context → doctor → specify → clarify → plan → proposed ADR → tasks → analyze
        → quality brief → Ralph → quality + standards → converge → simplify
        → docs sync → review → accepted ADR → evidence → PR handoff
```

Three lanes keep the process proportional:

| Lane | Use it for | Path |
| --- | --- | --- |
| Feature | New behavior, cross-module work, architectural change | Full SDD workflow |
| Bugfix | A reproducible defect with bounded scope | Assess → red test → fix → verify |
| Lightweight | Mechanical, documentation, or very small behavior-preserving changes | Scope → change → targeted evidence |

## Repository layout

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
│   ├── quality/
│   ├── docs-sync/
│   └── delivery/
├── workflows/              # Feature, bugfix, and lightweight workflows
├── skills/                 # Optional agent-native router and $sd facade
├── templates/              # Durable PR handoff template
├── docs/                   # Architecture and distribution contracts
├── examples/                # Copy-and-adapt project quality configurations
├── evals/                  # Behavioral evaluation prompts
└── scripts/                # Reproducible component packaging
```

The package is integration-agnostic. Codex, Claude Code, OpenCode, and generic
adapters can render the same commands in their native formats. Hosts with
delegation may run Ralph concurrently; other hosts use the same dependency-
ordered sequential protocol.

## Agent entry point

Use `$sd <request>` in Codex to start the optional agent-native SDD facade. In
harnesses that expose skills as slash commands, publish the same facade as
`/sd`. The facade loads `speckit-delivery`, which invokes the canonical
`speckit.delivery.route` extension command. The extension command—not the
facade—is the portable integration surface.

Copy both directories under `skills/` into the same agent skill-discovery root
for the optional native entry point. See [skills/README.md](skills/README.md)
for the sibling layout.

When Codex Skills mode is active, an installed Delivery extension is rendered
as the `speckit-delivery-route` skill under the active skill roots. Do not use
`Get-Command speckit*` as the Codex availability check; read the matching skill
and execute it through the host's surface instead.

The same warning applies elsewhere: Claude Code exposes the Delivery router as
`/speckit-delivery-route`, OpenCode as `/speckit.delivery.route`, and generic
adapters as a rendered command file. Do not turn host-native extension
availability into a PATH check like `which speckit*`.

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

The commands below run in the **target project**, not this distribution
checkout.

Initialize Spec Kit once, choosing the integration and script type that match
the target environment. For a PowerShell-based Codex project:

```powershell
cd D:\Repos\Acme\my-project
specify init . --integration codex --integration-options="--skills" --script ps
```

This creates `.specify/` and the integration's command/skill surface. It does
not replace existing project governance. Use `--force` only when replacing an
existing Spec Kit setup is intentional.

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

For several hosts in one repository, install each additional integration with
`specify integration install <key>`, then use
`specify integration use <key>` when switching the active default so installed
extensions are re-rendered. Prefer one default integration.

Install this delivery layer from a local checkout by supplying absolute paths
to the components:

```powershell
$delivery = "D:\Repos\Github\speckit-delivery"

specify extension add --dev "$delivery\extensions\decision"
specify extension add --dev "$delivery\extensions\ralph"
specify extension add --dev "$delivery\extensions\review"
specify extension add --dev "$delivery\extensions\simplify"
specify extension add --dev "$delivery\extensions\evidence"
specify extension add --dev "$delivery\extensions\quality"
specify extension add --dev "$delivery\extensions\docs-sync"
specify extension add --dev "$delivery\extensions\delivery"

specify workflow add --dev "$delivery\workflows\feature-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\bugfix-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\lightweight-delivery\workflow.yml"
```

Then invoke `speckit.delivery.init` through the selected agent integration. It
discovers existing instructions, CI checks, ADR locations, documentation
projections, and whether Spec artifacts are `tracked` or `ephemeral`. Review
the generated project-local configuration before relying on it.

It also drafts `.specify/extensions/quality/quality-config.yml`. Add one
profile for each source family and make every configured command executable in
the target project. The [Quality Gate configuration guide](QUALITY-GATE.md)
shows how to connect Python, TypeScript, Go, Java, and .NET style tooling,
complexity limits, tests, and architecture-policy sources to task closure.
For copy-and-adapt native configuration plus matching profile fragments, see
[Quality Gate examples](examples/quality-gate/).

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
ADR → tasks → analyze`, then implementation, quality, and the verification loop. The
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
the orchestrator verifies changed paths, evidence, and a current-HEAD Quality
Gate verdict, then—and only then—marks the task `[X]`. A failed or blocked task
remains open and blocks dependents. If Spec files
are ignored, the excerpts are injected into every cross-worktree packet.

After Ralph, run the aggregate Quality Gate and Standards Review, then
convergence, simplification, review, and evidence collection. A task stays open
unless both verdicts cover its current HEAD and declared scope.
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
| Quality gate | `speckit.quality.brief`, `speckit.quality.check` |
| Standards closure | `speckit.review.standards` |
| Documentation | `speckit.docs-sync.run` |
| Routing, doctor, and handoff | `speckit.delivery.doctor`, `.route`, `.handoff` |

## Durable and ephemeral artifacts

The project chooses whether `spec.md`, `plan.md`, and `tasks.md` are committed. Durable records must remain understandable at repository HEAD:

- Constitution: cross-feature non-negotiable project rules
- Issue: problem, scope, and acceptance contract
- ADR: long-lived architectural decision and rationale
- Source/tests/docs: implemented behavior
- PR: final change summary, risk, and verification evidence

When Spec Kit artifacts are ignored, Ralph must inject the assigned task and relevant artifact excerpts into each worker. Cross-worktree workers must never assume ignored files exist in their worktree.

See [Quick SD Configuration](QUICK-CONFIGURATION.md), [Architecture](ARCHITECTURE.md), [Artifact lifecycle](LIFECYCLE.md), and [Distribution](DISTRIBUTION.md).

## Design principles

- Requirements before implementation details.
- Evidence before completion claims.
- Unknown or unavailable required quality checks block closure; they do not pass by omission.
- One task queue: `tasks.md` is Ralph's scheduling source.
- One durable owner for each architectural decision.
- Review the real base/head diff, not a remembered change set.
- Simplification requires production-consumer evidence and net deletion.
- Integration-specific acceleration with a generic sequential fallback.

## Status and roadmap

- `0.1.x`: prompt contracts, guided workflows, catalogs, release packaging, structural validation
- `0.2.x`: richer machine-readable workflow state and cross-host semantic gates
- `0.3.x`: provider adapters for parallel Ralph execution
- `1.0.0`: clean-project installation evidence across supported integrations

See [CHANGELOG.md](CHANGELOG.md) for released changes.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). New commands should remain narrow, have an explicit completion criterion, and include at least one behavioral evaluation prompt.

## Security

Read [SECURITY.md](SECURITY.md) before adding shell execution, URL fetching, repository publishing, or credential-dependent providers.

## License

[MIT](LICENSE)
