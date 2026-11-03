# Reference review

The distribution was informed by public patterns from GitHub Spec Kit,
Anthropic Skills, Superpowers, and DeepSeek Harness.

Adopted patterns: one clear root entry point, one capability per extension,
composable workflows, a memorable `$sd` facade, progressive disclosure,
version-pinned catalogs, and clean-project installation evidence.

Deliberately excluded: repository-specific paths or commands, one monolithic
workflow prompt, claims of equivalent parallelism across hosts, direct edits to
generated projections, and unrelated repository-wide simplification.

## Evidence-first planning references

The exploration contract selectively adopts these patterns, not their complete
workflows or automatic skill installations:

- [GSD structure template](https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/get-shit-done/templates/codebase/structure.md):
  physical directory layout, key responsibilities, and where new code/tests fit.
- [Superpowers writing-plans](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-plans/SKILL.md):
  map file responsibilities before decomposing tasks, with exact change/test paths.
- [Superpowers systematic-debugging](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/systematic-debugging/SKILL.md):
  trace boundaries, compare working/broken paths, and require evidence before fixes.
- [OpenSpec explore](https://github.com/Fission-AI/OpenSpec/blob/6d04a1b58dedc95729d34e4f223d9d483aae210a/docs/explore.md):
  investigate the existing system before proposing a change; exploration is not implementation.
- [Spec Kit plan template](https://github.com/github/spec-kit/blob/99e047e9b48c3ecbbc5c3e530fb45bed671960bc/templates/plan-template.md):
  concrete source paths and a justified structure decision remain in the plan.

SD adds its own bounded Issue/PR/commit provenance, proportionate GitHub reference
research, two-tree scope presentation, and explicit scope/design checkpoints.
Reference patterns do not override the target project's governance or ADRs.

## Independent review references

The review update draws selectively on Superpowers' reviewer packets and verified
feedback, Codex's concrete actionable-defect calibration, Anthropic's staged
review, PR-Agent's persistent feedback, Trail of Bits' diff/caller analysis, and
Matt Pocock's focused task-review pattern. These inform the shared
[Reviewer contract](extensions/review/templates/reviewer.md), not automatic
multi-agent fan-out or confidence scores used as proof.

- [Superpowers PR #1299](https://github.com/obra/superpowers/pull/1299) is merged;
  [issue #1481](https://github.com/obra/superpowers/issues/1481) remains open in the
  research snapshot, not an implemented upstream fix.
- [PR-Agent PR #2722](https://github.com/The-PR-Agent/pr-agent/pull/2722) is merged:
  omitted feedback in same-snapshot or partial reruns is not evidence of resolution.

SD adds one six-dimensional task/final contract, current content/requirements
identity, explicit coverage/independence gaps, coordinator-owned lane repairs,
and persistent bounded attempts. Synthetic evaluations are behavioral probes,
not proof of a complete business-repository delivery or universal defect detection.

## Borrowed discipline criteria

Code Review and Standards Review adapt four criteria from
[unclebob/ub-mode](https://github.com/unclebob/ub-mode): test behavior rather
than implementation, fix the cause rather than the symptom, subtract before
adding, and close only independently verifiable units. The skill itself is not
vendored. Its "push to the main line at the end" and commit-frequency guidance
conflict with this distribution's explicit authorization and task-gate
boundaries, and its CRAP/duplication/mutation tools report results rather than
failing a process, so they need a project-owned wrapper before they can be
Quality Gate commands.

## Architecture skill methods

The Feature plan checkpoint adopts selected methods from these MIT-licensed
sources, inspected at fixed revisions on 2026-11-03. These are research references,
not vendored skills or runtime/install dependencies. The shipped
[Plan checkpoint](extensions/delivery/templates/exploration.md#architecture-constraints)
owns the executable prompt sequence; Core Plan/Tasks, Decision, Quality, and
Review retain their existing responsibilities.

| Source at inspected revision | Adopted method | Rejected or limited guidance |
| --- | --- | --- |
| [Jeffallan architecture-designer](https://github.com/jeffallan/claude-skills/blob/078a25cc5bfd8011459be7b91d004e900c1d02d3/skills/architecture-designer/SKILL.md), [NFR checklist](https://github.com/jeffallan/claude-skills/blob/078a25cc5bfd8011459be7b91d004e900c1d02d3/skills/architecture-designer/references/nfr-checklist.md), [system design](https://github.com/jeffallan/claude-skills/blob/078a25cc5bfd8011459be7b91d004e900c1d02d3/skills/architecture-designer/references/system-design.md) | Consider applicable non-functional requirements, trade-offs, operational cost, and failure modes before selecting a design. | Numeric targets and stack examples are not project facts. The example's Accepted ADR does not bypass SD's Proposed/review/finalize lifecycle. |
| [Matt Pocock codebase-design](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/codebase-design/SKILL.md), [Design It Twice](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/codebase-design/DESIGN-IT-TWICE.md) | Compare interface alternatives, consider what callers must know, concentrate state/complexity, and test through meaningful interfaces. | Keep project vocabulary; no mandatory terminology replacement or three-agent fan-out. Its broader [architecture scan](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/improve-codebase-architecture/SKILL.md) is optional audit work, not the default feature scope. |
| [Superpowers brainstorming](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/brainstorming/SKILL.md) | Ground alternatives in current code, distinguish requirements from recommendations, and make constraints explicit before implementation. | Reuse SD's existing scope/design checkpoints and artifact paths; do not start another question loop, design document, or planning workflow. |
| [wshobson architecture-patterns](https://github.com/wshobson/agents/blob/7e2fb559cf4b824b27f1fec49fe88f7511066d26/plugins/backend-development/skills/architecture-patterns/SKILL.md) | For a relevant backend design, inspect dependency direction, state ownership, and test boundaries. | Clean/Hexagonal/DDD are conditional options, not mandatory layers for every project. |

[Architecture Guard 3.5.0](https://github.com/DyanGalih/architecture-guard/blob/94e86a9baf7b3b2fc4bd0201b7e22b7142a9ff21/README.md)
is an adjacent orchestration system rather than a narrow architecture skill. Its
standalone installer is now primary; the legacy Spec Kit extension receives only
safety/breakage fixes. Do not make that orchestrator a prerequisite for SD or
inherit its default non-blocking violation policy.

The shared [method adapter contract](extensions/delivery/templates/method-adapter.md)
turns that provenance rule into an explicit optional provider flow for design,
diagnosis/testing, and review. It validates local resources by digest, defaults to
builtin, and returns analysis only to the existing owner; it does not adopt the
source's plan, queue, repair budget, commit, or review closure.

### Workflow method references

The optional diagnosis and review profiles use the same provenance rule. Pinned
source snapshots:

| Source | Adopted method | Rejected or limited |
| --- | --- | --- |
| [Superpowers systematic-debugging](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/systematic-debugging/SKILL.md) | Stable reproduction, cross-boundary evidence, working/broken comparison, one hypothesis and a minimal experiment. | Its fix/TDD/completion loop cannot replace official Bug ownership or SD repair budgets. |
| [Superpowers writing-good-tests](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/test-driven-development/writing-good-tests.md) | Behavior at a meaningful interface, independent expected values, tests that catch a named real failure. | Its broader always-test-first ritual is not a universal gate; project test policy decides. |
| [Superpowers requesting-code-review](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/requesting-code-review/SKILL.md) | Fresh-context reviewer packet, exact scope, findings with locations and evidence, implementer claims are not proof. | Its commit/worktree assumptions and any budget-expiry parking do not replace SD closure. |
| [Matt Pocock tdd](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/tdd/SKILL.md) | Public-interface behavior tests, one vertical red/green loop, refactoring left to review. | Its user-confirmed seams and repository-specific commands are not universal defaults. |
| [Matt Pocock code-review](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/code-review/SKILL.md) | Separate standards and specification lenses; repository rules win over generic smells. | Its two-axis report cannot replace SD's six dimensions, snapshot, or finding lifecycle. |

An already available skill can supply additional method guidance through the
checkpoint's source/provenance contract. Its recommendations become binding only
through the project's governing decision process and approved design; neither a
skill name nor its popularity proves architectural compliance. Deterministic
checks remain project-owned commands in Quality; unsupported graph coverage
(e.g. implicit imports or runtime DI) must be stated rather than reported green.
