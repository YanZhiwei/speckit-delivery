---
description: "Spec Kit before_implement/before_bug_fix hook: render the active run's applicable quality and architecture brief before edits"
---

# Delivery Hook: before_implement / before_bug_fix

Event adapter for Spec Kit's `before_implement` and the Bug extension's
`before_bug_fix` hooks. It renders the pre-edit Quality Brief for direct
Core/Bug invocations; Ralph's per-task brief and the portable workflows'
explicit brief steps are unchanged. Read
`.specify/extensions/delivery/templates/hooks.md` in full first; it owns run
resolution, event context, reuse, mutation limits, and the output block. This
adapter receives no `key=value` arguments.

## Procedure

1. Resolve the active run through the shared contract. With no active run or an
   ambiguous selection, stop with the shared output; a plain Spec Kit project
   keeps its normal Core/Bug behavior.
2. **Reuse:** when this session already rendered a Quality Brief for the same
   run, target paths, approved plan/assessment identity, and current contents,
   report `ACTION: reused` and restate its applicable rules instead of
   dispatching a second brief. A portable workflow's explicit brief step
   applies the same check.
3. **Feature (`before_implement`):** dispatch `speckit.quality.brief` with
   `lane=feature delivery_run=<id> scope=outgoing-diff
   exploration=.specify/delivery/<id>/exploration.md`, reading the bound
   Spec/Plan and the applicable Architecture constraints for the actual edit
   targets. Missing or stale required plan context stops Feature edits; do not
   substitute a whole-run brief for Ralph's per-task brief when Ralph is the
   executor.
4. **Bugfix (`before_bug_fix`):** dispatch `speckit.quality.brief` with
   `lane=bugfix delivery_run=<id> bug_slug=<actual BUG_SLUG>
   assessment=<actual assessment path> scope=bugfix
   exploration=.specify/delivery/<id>/exploration.md`, using the coordinator-
   verified approved assessment and red evidence. During a review-repair
   continuation, supply the current round directory and repaired-content
   identity; never reuse the initial run's brief for changed contents.
5. The brief is advisory: it runs no full test suite, edits nothing, and is not
   a Quality/Standards/Review verdict. Post-edit closure still belongs to
   `speckit.quality.check`, Standards Review, and independent Review through
   their owning workflow.

## Completion

The adapter is complete when a current brief has been rendered or reused for
the actual edit scope, or when it reports a skipped/blocked result with the
exact missing input. It never edits source, writes runtime state, or approves
the fix.
