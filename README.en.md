<div align="center">

# Spec Kit Delivery

**A delivery layer that carries Spec Kit's Spec / Plan / Tasks through to a mergeable change.**

[![Latest release](https://img.shields.io/github/v/release/YanZhiwei/speckit-delivery)](https://github.com/YanZhiwei/speckit-delivery/releases/latest)
[![License](https://img.shields.io/github/license/YanZhiwei/speckit-delivery)](LICENSE)
[![Spec Kit](https://img.shields.io/badge/Spec%20Kit-%E2%89%A51.2.3-blue)](https://github.com/github/spec-kit)

[简体中文](README.md) · [English](README.en.md)

</div>

Spec Kit turns a request into `Spec → Plan → Tasks`. Spec Kit Delivery carries those artifacts through to a mergeable change: it establishes the affected code, history, and references first, records architectural decisions as ADRs, constrains every task with project-local quality gates and independent review, and produces evidence and a pull-request body bound to the current HEAD.

It builds on Spec Kit's Extension, Workflow, and Bundle mechanisms. It **does not replace Spec Kit and does not bind the project to a model or host**.

> [!IMPORTANT]
> The current release line is `0.3.x`. The workflows, gates, and command contracts are usable. The portable Ralph path is sequential, with one verified commit per task. Provider-level parallelism and fully machine-driven semantic branching remain on the roadmap.

## Contents

- [Who it is for](#who-it-is-for)
- [Capability map](#capability-map)
- [How a delivery closes](#how-a-delivery-closes)
- [Quick start](#quick-start)
- [Command reference](#command-reference)
- [Durable and ephemeral artifacts](#durable-and-ephemeral-artifacts)
- [Compatibility and hosts](#compatibility-and-hosts)
- [Local development and release](#local-development-and-release)
- [Documentation map](#documentation-map)
- [Status and roadmap](#status-and-roadmap)

## Who it is for

- Teams already using Spec Kit whose implementation and review still depend on ad-hoc prompts after Spec / Plan / Tasks.
- Projects that need ADRs, quality gates, independent review, and auditable evidence instead of "the tests probably ran".
- Multi-agent or multi-worktree execution that still needs per-task boundaries and a verified commit.
- Maintainers who need to reconstruct, from a PR, what changed, what ran, and which risks remain.
- Changes large enough to need independently reviewable PRs instead of one multi-thousand-line diff.

## Capability map

| What you need | What the delivery layer provides | Entry point |
| --- | --- | --- |
| Decide which process a request needs | Three-lane routing and a Doctor preflight | `speckit.delivery.route`, `$sd` |
| See the current code, impact, and prior art first | Explore, current/candidate trees, external reference research | `speckit.delivery.explore` |
| Make architectural decisions traceable | ADR discovery, proposal, finalization, consistency check | `speckit.decision.context`, `.propose`, `.finalize`, `.check` |
| Split a large change into reviewable PRs | Slice boundaries, trunk-safety classification, merge policy | `speckit.delivery.slice` |
| Execute tasks safely | Per-task gates, independent review, verified commits | `speckit.ralph.run` |
| Make "done" evidence-backed | Project quality gates, standards review, six-dimensional code review, evidence collection | `speckit.quality.*`, `speckit.review.*`, `speckit.evidence.collect` |
| Produce a submittable PR body | Snapshot-bound handoff | `speckit.delivery.handoff` |
| Close out after the PR merges or closes | Outcome record, workspace retirement, one-page evidence | `speckit.delivery.close` |
| Keep docs and package READMEs from drifting | Projection sync and package README judgment | `speckit.docs-sync.run`, `.package-readme` |
| Explain a change visually | Mermaid by default, optional rendering | `speckit.diagram.render` |

## How a delivery closes

```text
route → doctor → decision discovery → explore code/history/references
      → current + candidate trees → scope approval
      → specify → clarify → ADR resolution → plan → design approval
      → tasks → slice → slice approval → analyze
      → quality brief → Ralph → quality → standards → review
      → converge → simplify → docs / package README
      → final review → evidence → handoff
      → (after authorization) PR merges or closes → close
```

Three gates separate "think it through" from "write code": **scope approval** before the Spec, **design approval** after the Plan, and **slice approval** after tasks. `tasks.md` is always the only execution queue; `slices.md` supplies review and merge boundaries only.

Three lanes keep the process proportional:

| Lane | Use it for | Main path |
| --- | --- | --- |
| Feature | New behavior, cross-module work, architectural change | Full SDD flow plus slicing |
| Bugfix | A reported defect expected to have bounded scope | Explore → assessment/red evidence → repair-scope approval → fix → verify |
| Lightweight | Mechanical, documentation, or behavior-preserving small changes | Scope → change → targeted evidence |

`$sd` and `/sd` are host conveniences. The cross-host contract is the `speckit.delivery.route` extension command.

## Quick start

> [!NOTE]
> Run these commands in the **target project**, not in this distribution checkout.

### 1. Prepare the Spec Kit CLI

```bash
uv tool install "specify-cli>=1.2.3"
specify self check
```

- The Bundle install path requires Spec Kit CLI `>=1.2.3`.
- Individual extensions and workflows require `>=0.16.4`.
- Git and the target project's own build, test, and quality tools are also required.

### 2. Initialize the target project

```bash
cd /path/to/my-project
specify init . --integration codex --integration-options="--skills" --script sh
```

| Host | Initialization example | Native command surface |
| --- | --- | --- |
| Claude Code | `specify init . --integration claude --script sh` | `.claude/skills/` |
| Codex | `specify init . --integration codex --integration-options="--skills" --script ps` | `.agents/skills/` |
| OpenCode | `specify init . --integration opencode --script sh` | OpenCode command directory |
| Other hosts | `specify init . --integration generic ...` | Chosen command directory |

Initialization creates `.specify/` and the host command surface; it does not replace existing project governance. Use `--force` only when replacing an existing setup is intentional.

### 3. Install the Bundle

```bash
specify extension catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.1/catalogs/extensions.json \
  --name speckit-delivery --install-allowed

specify workflow catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.1/catalogs/workflows.json \
  --name speckit-delivery

specify bundle catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.1/catalogs/bundles.json \
  --id speckit-delivery --policy install-allowed

specify bundle install speckit-delivery
```

The Bundle installs Delivery, Decision, Ralph, Review, Simplify, Evidence, Quality, Docs Sync, and Diagram, plus Spec Kit's official Bug extension and the Feature, Bugfix, and Lightweight workflows. Do not mix component versions from different tags.

### 4. Initialize project governance

Invoke `speckit.delivery.init` through the active host. It discovers existing agent instructions, CI, hooks, ADR locations, documentation projections, and the Spec-artifact policy, then drafts:

```text
.specify/extensions/delivery/delivery-config.yml
.specify/extensions/quality/quality-config.yml
```

Review both before starting a Feature. Each source family needs its own quality profile, and every configured command must be executable from the project root. The distribution does not guess Python, Node.js, a package manager, or a test framework. See the [Quality Gate guide](QUALITY-GATE.md) and [examples](examples/quality-gate/).

### 5. Start the first delivery

```text
$sd Add an audit trail for privileged configuration changes.
```

The router inspects the project and selects Feature, Bugfix, or Lightweight; it does not assume every request needs the full workflow. You can also run a workflow directly:

```bash
specify workflow run feature-delivery \
  --input delivery_run=audit-trail-01 \
  --input spec="Add an audit trail for privileged configuration changes"
```

## Command reference

| Capability | Commands |
| --- | --- |
| Routing and delivery | `speckit.delivery.route`, `.doctor`, `.explore`, `.slice`, `.context`, `.lightweight`, `.review-fix`, `.handoff`, `.close` |
| Decision memory | `speckit.decision.context`, `.propose`, `.finalize`, `.check` |
| Task execution | `speckit.ralph.run` |
| Defect handling | `speckit.bug.assess`, `.fix`, `.test` (Spec Kit's official Bug extension) |
| Quality gates | `speckit.quality.brief`, `speckit.quality.check`, `speckit.review.standards` |
| Code review | `speckit.review.run` |
| Simplification | `speckit.simplify.scan`, `.verify` |
| Delivery evidence | `speckit.evidence.collect` |
| Documentation | `speckit.docs-sync.run`, `speckit.docs-sync.package-readme` |
| Diagrams | `speckit.diagram.render` |

Boundaries worth knowing:

- `speckit.delivery.handoff` writes the reviewed PR body to `.specify/delivery/<run>/pull-request.md`, prints `PR_BODY_PATH` and a `gh pr create --body-file` hint, and **does not create, push, or merge a PR**.
- `speckit.delivery.close` records what actually happened: `delivered` for a merge, `abandoned` with one self-contained `evidence.md` retirement note for a closed-unmerged PR, or `superseded` with a resolvable reference. It does not mutate the remote.
- `speckit.docs-sync.package-readme` derives a package README from the real manifest, exports, CLI, configuration, and test commands. A new package records two or three comparable projects; a changed package reports `updated`, `unchanged-with-reason`, or `gap` per changed surface.
- `speckit.delivery.context` optionally reads a local `.codegraph/` index. Without one it returns a partial brief with named gaps; it never initializes an index or treats the graph as correctness evidence.

## Durable and ephemeral artifacts

The project chooses whether `spec.md`, `plan.md`, and `tasks.md` are committed. Either way, these must remain understandable at repository HEAD:

- **Constitution**: cross-feature project rules.
- **Issue**: problem, scope, and acceptance contract.
- **ADR**: long-lived architectural decision and rationale.
- **Source, tests, docs**: implemented behavior.
- **PR**: final change summary, risk, and verification evidence.
- **Delivery evidence**: `.specify/delivery/<run>/evidence.md` and its recorded `delivered` / `abandoned` / `superseded` outcome.

`exploration.md`, `slices.md`, `receipts/`, `task-verdicts.yml`, review workspaces, and the rendered PR body are run workspace and follow `artifact_policy`; under `ephemeral` they stay local. Evidence binds to actual contents and the requirements snapshot. Stale evidence is rerun, never relabeled with the current hash.

See [Artifact lifecycle](LIFECYCLE.md) and [Architecture](ARCHITECTURE.md).

## Compatibility and hosts

| Item | Requirement |
| --- | --- |
| Bundle install | Spec Kit CLI `>=1.2.3` |
| Individual extension or workflow | Spec Kit CLI `>=0.16.4` |
| Hosts | Codex, Claude Code, OpenCode, generic adapters |
| Runtime | Git; the target project's build and test tools |

Extension commands are the stable cross-host surface. Host entry points:

| Host | Invocation |
| --- | --- |
| Claude Code | `/speckit-delivery-route <request>` |
| Codex | `$speckit-delivery-route <request>`, or the optional `$sd <request>` facade |
| OpenCode | `/speckit.delivery.route <request>` |
| Generic adapter | Run the rendered `speckit.delivery.route` command file |

Do not use `Get-Command speckit*` or `which speckit*` to decide whether an extension is installed. In Codex Skills mode, check for the `speckit-delivery-route` skill under the active skills root; other hosts should check the rendered command file.

## Local development and release

The repository publishes individually versioned extension archives, pinned Extension/Workflow/Bundle catalogs, and the `speckit-delivery` Bundle. Validate the Bundle in a clean target project: the CLI searches upward from the Bundle directory for the project root, so a checkout-local `.specify` cache must not become the validation context.

```bash
# In a clean target project after installing the local components:
cp -R /path/to/speckit-delivery/bundle ./bundle
specify bundle validate --path ./bundle

# From the distribution checkout:
specify bundle build --path ./bundle --output ./dist
```

<details>
<summary>Install every component from a local checkout (maintainers)</summary>

```bash
delivery=/path/to/speckit-delivery

specify extension add --dev "$delivery/extensions/decision"
specify extension add --dev "$delivery/extensions/ralph"
specify extension add --dev "$delivery/extensions/review"
specify extension add --dev "$delivery/extensions/simplify"
specify extension add --dev "$delivery/extensions/evidence"
specify extension add --dev "$delivery/extensions/quality"
specify extension add --dev "$delivery/extensions/docs-sync"
specify extension add --dev "$delivery/extensions/diagram"
specify extension add --dev "$delivery/extensions/delivery"

specify workflow add --dev "$delivery/workflows/feature-delivery/workflow.yml"
specify workflow add --dev "$delivery/workflows/bugfix-delivery/workflow.yml"
specify workflow add --dev "$delivery/workflows/lightweight-delivery/workflow.yml"
```

</details>

Run the distribution checks before submitting:

```bash
uv run --with pyyaml python scripts/validate_distribution.py
uv run --with pyyaml python scripts/test_validate_distribution.py
uv run --with pyyaml python scripts/test_workflow_handoff.py
uv run --with pyyaml python scripts/check_links.py
uv run --with pyyaml python scripts/test_bundle_install.py --integration opencode
```

`test_workflow_handoff.py` requires Spec Kit CLI 1.2.3 to be installed.

Releasing is two steps: run **Prepare release PR** to stamp versions and catalog URLs (including the pinned install URLs in this README) and merge `release/v<version>`, then run **Release distribution** to create the tag and assets. The release pipeline does not write back to `main` or move an existing tag. See [Distribution](DISTRIBUTION.md).

## Documentation map

| Document | Contents |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | Component boundaries, control planes, ownership |
| [Artifact lifecycle](LIFECYCLE.md) | Durable records, ephemeral artifacts, evidence, retirement |
| [Quality Gate](QUALITY-GATE.md) | Project profiles, commands, and blocking semantics |
| [Delivery contract](extensions/delivery/README.md) | Full Explore, Slice, Handoff, and Close contract |
| [Reviewer contract](extensions/review/templates/reviewer.md) | Six dimensions, snapshots, independence, finding states |
| [Quick SD configuration](QUICK-CONFIGURATION.md) | Fast onboarding checklist for an existing project |
| [Distribution](DISTRIBUTION.md) | Catalogs, packaging, release, clean-install verification |
| [Changelog](CHANGELOG.md) | Released changes and upgrade notes |
| [Contributing](CONTRIBUTING.md) | Submission and review conventions |
| [Security](SECURITY.md) | Credentials, execution, and publishing boundaries |

## Status and roadmap

- `0.1.x`: command contracts, guided workflows, catalogs, quality profiles, release structure.
- `0.2.x`: delivery slicing and merge policy, handoff body path, Chinese fallback template.
- `0.3.x`: delivery outcome and retirement, package README node, and README drift judgment in all three lanes.
- Next: provider-level parallel Ralph, machine-readable workflow state, cross-host semantic gates.
- `1.0.0`: clean-project installation evidence across supported integrations.

## Contributing and license

- New commands stay narrow, define explicit completion criteria, and ship at least one behavioral eval.
- Run the distribution checks above before submitting; never mix component versions across tags.
- Read [SECURITY.md](SECURITY.md) before changing execution or publishing boundaries.

[MIT](LICENSE)
