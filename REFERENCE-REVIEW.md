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
