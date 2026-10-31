# Spec Kit Delivery

An evidence-driven delivery layer for [GitHub Spec Kit](https://github.com/github/spec-kit). It keeps Spec Kit's specification artifacts as the execution backbone and adds durable architecture decisions, project-local quality gates, task-based agent orchestration, convergence, simplification review, code review, documentation synchronization, release evidence, and a stable pull-request handoff.

> [!IMPORTANT]
> This repository is an early distribution scaffold (`0.2.x`). The guided workflows and prompt contracts are usable for evaluation. The portable Ralph path is sequential with per-task Git commits; delivery slicing and merge policy are available, while provider-specific parallel execution and fully machine-driven semantic branching remain later milestones.

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
- What already exists, which Issue/PR/commit history explains it, and which
  files would this change actually touch?
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
doctor → decision discovery → explore code/history/GitHub references
       → show current + candidate trees → scope approval → specify → clarify
       → ADR resolution → plan → proposed ADR → finalized-tree/design approval
       → tasks → slice/slice gate → analyze → quality brief → Ralph → quality + standards
        → converge → simplify → docs sync → bounded review/fix → final review gate
        → accepted ADR → review freshness → evidence → snapshot-checked PR handoff
```

Three lanes keep the process proportional:

| Lane | Use it for | Path |
| --- | --- | --- |
| Feature | New behavior, cross-module work, architectural change | Full SDD workflow |
| Bugfix | A reported defect expected to have bounded scope | Explore → assess/red evidence → repair-scope approval → fix → verify |
| Lightweight | Mechanical, documentation, or very small behavior-preserving changes | Scope → change → targeted evidence |

Before a Feature spec, `speckit.delivery.explore` shows actual code directories
and candidate changes, including tests, reuse/no-change areas, alternatives,
risks, and evidence gaps. It traces relevant project Issues, PRs, and commit
diffs. New capabilities and new architectural mechanisms get GitHub reference
research grounded in actual code, fixed versions/SHAs, and related follow-up fixes;
small understood extensions may skip with a reason. CodeGraph is preferred when
available, with an explicit source/test fallback rather than mandatory indexing.

The user approves scope first, then the finalized file responsibilities,
interfaces, and tests at the existing plan gate. Bug assessment retains diagnosis
ownership; Lightweight avoids full research and two approval rounds. Mermaid/SVG
may explain complex relationships, but never replaces the trees; AI image
generation is not used. See the [Delivery contract](extensions/delivery/README.md).

After tasks, `speckit.delivery.slice` binds real task IDs to reviewable slices and
derives the merge mode from trunk-safety evidence. Large changes use stacked PRs
by default; an integration branch is the fallback when intermediate slices cannot
safely enter the target branch. Slice approval is a separate gate, and a failed
prefix check reopens slicing instead of continuing the stack. `tasks.md` remains
the only execution queue; see the [slice contract](extensions/delivery/commands/speckit.delivery.slice.md).

Review covers requirements, code quality, architecture/design standards,
correctness, security/compatibility, and test effectiveness. It stays read-only;
Delivery coordinates verified repairs and independent re-review. All lanes keep
stable finding IDs and content/requirements fingerprints, not HEAD-only passes.
Up to three safe repair slots honor a lower configured budget and no-op after a
complete current pass. Blocked/incomplete and missing coverage cannot pass a gate.
These are guided contracts, not a machine-enforced semantic engine; see the
[Reviewer contract](extensions/review/templates/reviewer.md).

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
│   ├── diagram/
│   └── delivery/
├── workflows/              # Feature, bugfix, and lightweight workflows
├── skills/                 # Optional router facades and diagram renderers
├── docs/                   # Architecture and distribution contracts
├── examples/                # Copy-and-adapt project quality configurations
├── evals/                  # Behavioral evaluation prompts
└── scripts/                # Reproducible component packaging
```

The package is integration-agnostic. Codex, Claude Code, OpenCode, and generic
adapters can render the same commands in their native formats. The portable
Ralph path uses one dependency-ready task per iteration in a clean
`ralph/<feature>` branch, with one verified Git commit per task. Provider-level
parallelism requires isolated worktrees and is a later integration contract.

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

- Spec Kit CLI `>=0.16.4` for individual extensions and workflows
- Spec Kit CLI `>=1.2.3` for the Bundle installer path
- A Spec Kit-supported coding-agent integration
- Git
- Project build and test tools selected by the target repository

> [!NOTE]
> Release `v0.1.1` fixed the workflow-catalog alignment, so the Bundle installer
> works on Spec Kit `>=1.2.3`. Release `v0.1.2` adds the Diagram extension.
> Install the versioned catalogs that match the commands you need; do not mix
> component versions across tags.

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
specify extension add --dev "$delivery\extensions\diagram"
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
specify workflow run feature-delivery --input delivery_run=audit-trail-01 --input spec="Describe the change"
```

The Feature lane runs `doctor → decision discovery → explore → scope approval →
specify → clarify → ADR resolution → plan → proposed ADR → design approval →
tasks → analyze`, then implementation, quality, and the verification loop. The
Proposed ADR remains editable through implementation and review. Only after
the reviewed repository HEAD matches the decision does it become Accepted.

Approved exploration is explicitly passed into spec, assessment, plan, and task
generation. Once the actual feature/run location exists, its record is
`.specify/delivery/<feature-or-run>/exploration.md`, honoring `artifact_policy`;
before that it remains preserved context without a fabricated feature path.
Material expansion returns to scope/design approval, not a silently enlarged task
queue. Research limitations must be explicit; decision-critical gaps block progress.

Direct workflows require a unique safe `delivery_run` id (reuse on resume).
Explore persists `.specify/delivery/<delivery_run>/exploration.md` before its host
process exits; downstream steps receive that exact path and the actual gate
choice, recording approval against the reviewed scope/snapshot. Keep this run
path stable after Feature/bug identity becomes known. Context-only preservation
is limited to a shared-session router; ephemeral direct workflows still need a
local ignored file. Bugfix review repairs preserve original official fix/test
reports through a versioned continuation adapter rather than overwriting them.

Direct Bugfix also takes explicit `bug_slug=<lowercase-kebab-slug>`; only its
coordinator persists the verified assessment mapping, not official Assess.
Continuation runs applicable mandatory pre/post fix/test hooks with current
round report context and blocks on incompatible or missing required hook results.

## Run Ralph from tasks

Ralph is an execution coordinator, not a planning shortcut. Start it only
after `speckit.tasks` has produced and `speckit.analyze` has checked the active
feature's `tasks.md`:

```text
speckit.ralph.run
```

It reads `tasks.md` as the only execution source, finds one dependency-ready
`Txxx` task per iteration, and respects file overlap, migrations, public
contracts, and unresolved decisions as blocking edges. Before selecting a
task, the command creates or reuses and verifies a clean `ralph/<feature>`
branch, reports the applicable governance and code-style rules, and emits a
task-specific governance packet. It then runs the task checks plus Quality,
Standards, and independent task-scoped Review gates. Only after the pre-checkbox closure gate passes is a task
marked `[X]`; it is immediately committed with its receipt. It emits
`<promise>ALL_TASKS_DONE</promise>` only after every task has a snapshot-bound receipt associated with its verified commit
and a clean committed worktree.

Each worker receives the task's acceptance condition, allowed scope, relevant
Spec/Plan/ADR excerpts, and expected verification. Workers report results;
the orchestrator verifies changed paths, evidence, and all three current-snapshot
verdicts, then—and only then—marks the task `[X]`. A failed or blocked task
remains open and blocks dependents. If Spec files
are ignored, the excerpts are injected into every cross-worktree packet.

After Ralph, run the aggregate Quality Gate and Standards Review, then
convergence, simplification, review, and evidence collection. A task stays open
unless all three verdicts cover its actual code, requirements, and declared scope.
Task review repairs stay in the open task without recursive Ralph. Final Feature
findings become new or reopened tasks and re-enter the same
`analyze → Ralph → review` loop within the persistent repair budget. The final ADR is reconciled against HEAD,
not against an earlier plan.

## Usage scenarios

### Feature: add Redis L2 caching

**Request:** “Add Redis-backed L2 caching. The repository already has an ADR
for process-local caching, and Spec files are gitignored.”

Run `$sd` with the request. It routes to **Feature**, retrieves the local-cache
ADR before planning, and produces a Proposed cache ADR once the plan selects a
direction. `speckit.tasks` creates the queue; Ralph executes the
serialization, cache adapter, invalidation, and test tasks one at a time. Each
iteration carries the assigned task plus the relevant cache and ADR excerpts,
runs the task gates, and creates its own verified commit. Because Spec
artifacts are ephemeral, workers must not assume that another worktree contains
them. After review, finalize a self-contained Accepted ADR that explains the
Redis and local-cache relationship without citing the ignored Spec files.

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

Run `speckit.ralph.run`. Ralph first creates or reuses and verifies the
feature's `ralph/<feature>` branch, reports the applicable governance packet,
then selects one ready task and runs its checks plus Quality, Standards, and
independent Review gates. A pre-checkbox closure gate verifies acceptance evidence,
current code/requirements snapshot, allowed paths, and required tools. After it passes, Ralph marks `[X]`
and immediately creates exactly one commit containing the verified scope and
task receipt. Workers return their changes and evidence; Ralph alone updates
task checkboxes and commits. If `T014` fails verification or commit validation,
it stays open and its dependents remain blocked with an explicit reason.

## Local development installation

If the current directory is the distribution checkout rather than a target
project, keep validation rooted in a clean target project. `bundle validate`
resolves project-local installed components from the bundle's parent tree; a
checkout-local `.specify` cache must not become the validation context.

```bash
# In a clean target project after installing the local components:
cp -R /path/to/speckit-delivery/bundle ./bundle
specify bundle validate --path ./bundle

# From the distribution checkout:
specify bundle build --path ./bundle --output ./dist
```

## Release installation

Maintainers use the manual **Prepare release PR** workflow to stamp all versions
and catalog URLs, validate the candidate, and open a reviewed `release/v<version>`
PR. Merge that PR before running **Release distribution**; the release pipeline
does not write back to `main` or move an existing tag.

> [!NOTE]
> The commands below target the prepared `v0.2.2` release. Until it is published,
> use the released `v0.2.1` catalogs, which contain the PR body-path handoff fix
> but not the Chinese fallback template. Do not mix components from different
> tags.

Releases publish each extension as a root-layout zip, expose pinned catalogs, and publish the bundle artifact. Add the versioned catalogs before installing the bundle (Bundle requires Spec Kit `>=1.2.3`):

```bash
specify extension catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.2/catalogs/extensions.json \
  --name speckit-delivery --install-allowed

specify workflow catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.2/catalogs/workflows.json \
  --name speckit-delivery

specify bundle catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.2/catalogs/bundles.json \
  --id speckit-delivery --policy install-allowed

specify bundle install speckit-delivery
```

Preparing source or installing components does not publish a release. After the
release-preparation PR is reviewed and merged, maintainers explicitly run
**Release distribution** for the selected version and commit.

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
| Exploration, slicing, routing, repair, doctor, handoff, and close-out | `speckit.delivery.explore`, `.slice`, `.doctor`, `.route`, `.review-fix`, `.handoff`, `.close` |
| Diagrams | `speckit.diagram.render` |
| Code context | `speckit.delivery.context` |

`speckit.delivery.context` reads the project's local `.codegraph/` index when it
exists and reports entry points, callers, and affected tests for the change. It
is optional: without the index it returns a partial brief and names the gaps,
and it never initializes an index or treats the graph as test evidence.

`speckit.delivery.handoff` writes the reviewed PR body to
`.specify/delivery/<run>/pull-request.md` (or `pull-request-<slice>.md`) and
prints `PR_BODY_PATH` plus a `gh pr create --body-file` hint. Installing the
extension does not replace the target repository's `.github` PR template; GitHub
UI still reads that repository file unless a body file is supplied.

`speckit.delivery.close` records what actually happened to the PR. A merged run
becomes `delivered`; a PR closed without merging becomes `abandoned` and keeps one
self-contained `evidence.md` retirement note; a replaced run becomes `superseded`.
Retirement removes that run's workspace artifacts only, never `evidence.md`.
Installation and upgrade records are operational one-offs, not delivery runs.

## Durable and ephemeral artifacts

The project chooses whether `spec.md`, `plan.md`, and `tasks.md` are committed. Durable records must remain understandable at repository HEAD:

- Constitution: cross-feature non-negotiable project rules
- Issue: problem, scope, and acceptance contract
- ADR: long-lived architectural decision and rationale
- Source/tests/docs: implemented behavior
- PR: final change summary, risk, and verification evidence
- Delivery evidence: `.specify/delivery/<run>/evidence.md` and its recorded
  `delivered`/`abandoned`/`superseded` outcome; other run files follow
  `artifact_policy`

When Spec Kit artifacts are ignored, Ralph must inject the assigned task and relevant artifact excerpts into each worker. Cross-worktree workers must never assume ignored files exist in their worktree.

See [Quick SD Configuration](QUICK-CONFIGURATION.md), [Architecture](ARCHITECTURE.md), [Artifact lifecycle](LIFECYCLE.md), and [Distribution](DISTRIBUTION.md).

## Design principles

- Requirements before implementation details.
- Evidence before completion claims.
- Unknown or unavailable required quality checks block closure; they do not pass by omission.
- One task queue: `tasks.md` is Ralph's scheduling source; `slices.md` is boundary metadata only.
- Large changes are sliced before coding; stacked PRs by default, integration only when a prefix cannot safely enter the target.
- One durable owner for each architectural decision.
- Review the real base/head diff, not a remembered change set.
- Simplification requires production-consumer evidence and net deletion.
- Integration-specific acceleration with a generic sequential fallback.

## Status and roadmap

- `0.1.x`: prompt contracts, guided workflows, catalogs, release packaging, structural validation
- `0.2.x`: delivery slicing and merge policy, then richer machine-readable workflow state and cross-host semantic gates
- `0.3.x`: provider adapters for parallel Ralph execution
- `1.0.0`: clean-project installation evidence across supported integrations

See [CHANGELOG.md](CHANGELOG.md) for released changes.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). New commands should remain narrow, have an explicit completion criterion, and include at least one behavioral evaluation prompt.

## Security

Read [SECURITY.md](SECURITY.md) before adding shell execution, URL fetching, repository publishing, or credential-dependent providers.

## License

[MIT](LICENSE)
