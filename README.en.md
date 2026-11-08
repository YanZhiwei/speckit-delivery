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
> The current release line is `0.4.x`. The workflows, gates, and command contracts are usable. The portable Ralph path is sequential, with one verified commit per task. Provider-level parallelism and fully machine-driven semantic branching remain on the roadmap.

## Contents

- [Who it is for](#who-it-is-for)
- [Capability map](#capability-map)
- [How a delivery closes](#how-a-delivery-closes)
- [Quick start](#quick-start)
- [Compatibility and hosts](#compatibility-and-hosts)
- [Local development and release](#local-development-and-release)
- [Documentation map](#documentation-map)
- [Status and roadmap](#status-and-roadmap)
- [Contributing and license](#contributing-and-license)

## Who it is for

- Teams already using Spec Kit whose implementation and review still depend on ad-hoc prompts after Spec / Plan / Tasks.
- Projects that need ADRs, quality gates, independent review, and auditable evidence instead of "the tests probably ran".
- Multi-agent or multi-worktree execution that still needs per-task boundaries and a verified commit.
- Maintainers who need to reconstruct, from a PR, what changed, what ran, and which risks remain.
- Changes large enough to need independently reviewable PRs instead of one multi-thousand-line diff.

## Capability map

| Capability | Commands | Read more |
| --- | --- | --- |
| Routing and preflight: three lanes, Doctor | `speckit.delivery.route`, `.doctor` | [Host entry points](skills/README.md) |
| Evidence-first context: current/candidate trees, prior art | `speckit.delivery.explore`, `.context` | [Delivery contract](extensions/delivery/README.md) |
| Decision memory: ADR discovery, proposal, finalization, check | `speckit.decision.context`, `.propose`, `.finalize`, `.check` | [Decision contract](extensions/decision/README.md) |
| Slicing and merge policy: boundaries, trunk safety, PR grouping | `speckit.delivery.slice` | [Delivery contract](extensions/delivery/README.md) |
| Task execution: per-task gates, independent review, verified commits | `speckit.ralph.run` | [Ralph](extensions/ralph/README.md) |
| Quality gates: project profiles, standards, six-dimensional review | `speckit.quality.brief`, `.check`, `speckit.review.standards` | [Quality Gate](QUALITY-GATE.md) |
| Code review and repair: guarded review, convergence, repair | `speckit.review.run`, `speckit.delivery.review-fix` | [Reviewer contract](extensions/review/templates/reviewer.md) |
| Simplification: only accepted candidates are applied | `speckit.simplify.scan`, `.verify` | [Simplify](extensions/simplify/README.md) |
| Evidence and close-out: snapshot-bound evidence, handoff, close | `speckit.evidence.collect`, `speckit.delivery.handoff`, `.close` | [Artifact lifecycle](LIFECYCLE.md) |
| Documentation sync: projection sync, project README structure guard, package README judgment | `speckit.docs-sync.run`, `.package-readme` | [Docs Sync](extensions/docs-sync/README.md) |
| Diagrams: Mermaid by default, optional rendering | `speckit.diagram.render` | [Diagram](extensions/diagram/README.md) |
| Defect handling: assessment, fix, regression | `speckit.bug.assess`, `.fix`, `.test` | [Spec Kit](https://github.com/github/spec-kit) |

## How a delivery closes

```text
route → doctor → decision discovery → explore code/history/references
      → current + candidate trees → scope approval
      → specify → clarify → ADR resolution → plan (architecture constraints + verification) → design approval
      → tasks → slice → analyze → combined execution/slice gate → Ralph → quality → standards → Converge
      → (only when tasks are appended) Slice → Analyze → renewed slice approval → Ralph → reassessment
      → simplify (only accepted candidates are applied/verified) → docs / package README
      → guarded Review/Repair → ADR/freshness checks → evidence → handoff → (after authorization) PR merges or closes → close
```

Three gates separate "think it through" from "write code": **scope approval** before the Spec, **design approval** after the Plan, and the **combined execution/slice approval** after Analyze. `tasks.md` is always the only execution queue; `slices.md` supplies review and merge boundaries only.

Runtime invariants (state transitions and recovery live in the [delivery contract](extensions/delivery/README.md#runtime-state-resume-and-conditional-dispatch); local coordinator state and artifact retention in the [artifact lifecycle](LIFECYCLE.md#runtime-coordination-and-checkpoints)):

- Every task's owner receipt and actual commit must hold individually; checked boxes or a final integrated review cannot replace missing task evidence.
- `action=status` reports only the same run's local coordinator state and `action=resume` recovers only that run's pending ticket; a current Review pass skips unnecessary Repair, and unresolved work at a repair/convergence cap fails the final machine guard.
- Quality, Standards, Reviewer, Core, and Ralph remain the semantic owners; the runtime guards only structure, fingerprints, and freshness.

The Plan records architecture constraint sources, affected paths, design responses, verification owners, and evidence gaps, carrying IDs into Tasks, Brief, and Review. `method_adapters` in `delivery-config.yml` can select design, diagnosis/testing, and review methods separately; the default is `builtin`. An explicit external method must bind a local entrypoint, fixed revision, resource manifest, and SHA-256 digests, and returns analysis only: no second plan, queue, commit, or review-closure authority. See the pinned [method review](REFERENCE-REVIEW.md#architecture-skill-methods) and [method contract](extensions/delivery/templates/method-adapter.md).

Three lanes keep the process proportional:

| Lane | Use it for | Main path |
| --- | --- | --- |
| Feature | New behavior, cross-module work, architectural change | Full SDD flow plus slicing |
| Bugfix | A reported defect expected to have bounded scope | Explore → assessment/red evidence → repair-scope approval → fix → verify |
| Lightweight | Mechanical, documentation, or behavior-preserving small changes | Scope → change → targeted evidence |

After installation use `/sd` in OpenCode, `$speckit-sd` in Codex Skills mode, or `/speckit-sd` in Claude Code; the shortcut and the full entry render from the same router source and share one lifecycle. See [host entry points](skills/README.md).

## Quick start

> [!NOTE]
> Run these commands in the **target project**, not in this distribution checkout.

### 1. Prepare the Spec Kit CLI

```bash
uv tool install "specify-cli>=1.2.3"
specify self check
```

| Install path | Requirement |
| --- | --- |
| Bundle | Spec Kit CLI `>=1.2.3` |
| Individual extension | Spec Kit CLI `>=0.16.4` |

Python `>=3.11` (workflow runtime), Git, and the target project's own build, test, and quality tools are also required.

### 2. Initialize the target project

```bash
cd /path/to/my-project
specify init . --integration opencode --script sh
```

Initialization creates `.specify/` and the host command surface; it does not replace existing project governance. Other hosts are listed under [compatibility and hosts](#compatibility-and-hosts). Use `--force` only when replacing an existing setup is intentional.

### 3. Install the Bundle

```bash
base=https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.6/catalogs
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle install speckit-delivery
```

The Bundle installs Delivery, Decision, Ralph, Review, Simplify, Evidence, Quality, Docs Sync, and Diagram, plus Spec Kit's official Bug extension and the Feature, Bugfix, and Lightweight workflows. Do not mix component versions from different tags.

#### Upgrade an existing Bundle

Back up project configuration and core template customizations, then follow [upgrading the Bundle from catalogs](QUICK-CONFIGURATION.md#upgrade-the-bundle-from-catalogs) to replace the version-pinned catalogs and run `specify bundle update speckit-delivery`. Afterwards verify the Bundle version, project configuration, core customizations, and the `/sd` entry.

### 4. Initialize project governance

Invoke `speckit.delivery.init` through the active host. It discovers existing agent instructions, CI, hooks, ADR locations, documentation projections, and the Spec-artifact policy, then drafts:

```text
.specify/extensions/delivery/delivery-config.yml
.specify/extensions/quality/quality-config.yml
```

Review both before starting a Feature. Each source family needs its own quality profile, and every configured command must be executable from the project root; the distribution does not guess Python, Node.js, a package manager, or a test framework. See the [Quality Gate guide](QUALITY-GATE.md) and [examples](examples/quality-gate/).

### 5. Start the first delivery

```text
/sd Add an audit trail for privileged configuration changes.
```

The router inspects the project and selects Feature, Bugfix, or Lightweight; it does not assume every request needs the full workflow. You can also run a workflow directly:

```bash
specify workflow run feature-delivery \
  --input delivery_run=audit-trail-01 \
  --input spec="Add an audit trail for privileged configuration changes"
```

A Windows project using the Python Launcher can pass `--input runtime_python="py -3"`; Linux/macOS projects can select `python3`. Use a verified local interpreter invocation and fix shell startup errors first; the runtime does not alter global shell configuration.

## Compatibility and hosts

| Host | Initialization | Installed entry | Native command surface |
| --- | --- | --- | --- |
| Claude Code | `specify init . --integration claude --script sh` | `/speckit-sd`, full `/speckit-delivery-route` | `.claude/skills/` |
| Codex | `specify init . --integration codex --integration-options="--skills" --script ps` | `$speckit-sd`, full `$speckit-delivery-route` | `.agents/skills/` |
| OpenCode | `specify init . --integration opencode --script sh` | `/sd`, full `/speckit.delivery.route` | OpenCode command directory |
| Generic adapter | `specify init . --integration generic ...` | Run the rendered `speckit.delivery.route` command file | Chosen command directory |

Extension commands are the stable cross-host surface. Do not use `Get-Command speckit*` or `which speckit*` to decide whether an extension is installed: Codex Skills mode should check for the `speckit-delivery-route` skill under the active skills root, and other hosts should check the rendered command file.

## Local development and release

The repository publishes individually versioned extension archives, pinned catalogs, and the `speckit-delivery` Bundle; local installation, clean validation, and release checks live in [Distribution](DISTRIBUTION.md). Validate the Bundle in a clean target project: the CLI searches upward from the Bundle directory for the project root, so a checkout-local `.specify` cache must not become the validation context.

```bash
cp -R /path/to/speckit-delivery/bundle ./bundle   # clean target project
specify bundle validate --path ./bundle
specify bundle build --path ./bundle --output ./dist   # distribution checkout
```

Before submitting, run every check in the distribution guide: `scripts/validate_distribution.py`, the replay suites, the link check, and a clean-project installation check for each changed host and workflow.

Releasing is two steps: run **Prepare release PR** to stamp versions and catalog URLs (including the pinned install URLs in this README) and merge `release/v<version>`, then run **Release distribution** to create the tag and assets. The release pipeline does not write back to `main` or move an existing tag.

## Documentation map

| Document | Contents |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | Component boundaries, control planes, ownership |
| [Artifact lifecycle](LIFECYCLE.md) | Durable records, ephemeral artifacts, evidence, retirement |
| [Quality Gate](QUALITY-GATE.md) | Project profiles, commands, and blocking semantics |
| [Delivery contract](extensions/delivery/README.md) | Full Explore, Slice, Runtime, Handoff, and Close contract |
| [Reviewer contract](extensions/review/templates/reviewer.md) | Six dimensions, snapshots, independence, finding states |
| [Reference review](REFERENCE-REVIEW.md) | Sources behind evidence-first planning, independent review, and architecture skill methods |
| [Quick SD configuration](QUICK-CONFIGURATION.md) | Fast onboarding checklist for an existing project |
| [Distribution](DISTRIBUTION.md) | Catalogs, packaging, release, README contract, clean-install verification |
| [Changelog](CHANGELOG.md) | Released changes and upgrade notes |
| [Contributing](CONTRIBUTING.md) | Submission and review conventions |
| [Security](SECURITY.md) | Credentials, execution, and publishing boundaries |

## Status and roadmap

- Current line: `0.4.x` provides persistent runtime checkpoints, conditional dispatch and recovery, the Core/Ralph compatibility contract, and guarded Review/Converge.
- Next: provider-level parallel Ralph and cross-host semantic gates.
- `1.0.0`: clean-project installation evidence across supported integrations.

See the [changelog](CHANGELOG.md) for per-release changes.

## Contributing and license

- New commands stay narrow, define explicit completion criteria, and ship at least one behavioral eval.
- Run the checks in [Distribution](DISTRIBUTION.md) before submitting; never mix component versions across tags.
- Read [SECURITY.md](SECURITY.md) before changing execution or publishing boundaries.

[MIT](LICENSE)
