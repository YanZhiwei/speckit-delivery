# Documentation refresh after a review repair

Owned by Delivery Review Fix. Apply within the already reserved repair attempt,
before current checks and independent re-review. A previous pre-review README or
projection result cannot cover a changed public surface merely because HEAD or
the documentation filename stayed the same.

1. Compare the actual repair with the snapshot the previous documentation result
   covered. Identify affected packages and changes to purpose, install/setup,
   public API/CLI/config/defaults, compatibility, dependencies, error behavior,
   development/test commands, release/versioning, ownership, or authoritative
   projection inputs. Use Docs Sync's package/manifest contracts. An internal-only
   repair records `not-applicable` with a concrete reason; reserve `unchanged` for
   documentation that was actually checked and needs no edit.
2. Reuse an existing documentation result only when its original surface inputs,
   configuration, scope, and documentation contents still match. Honor configured
   Docs Sync rules and, for Feature, the actual caller's `with_docs_sync` choice;
   if that optional argument is absent, do not infer enabled projection sync
   (package README policy still applies). Propagate an explicit choice on nested
   repairs. Bugfix/Lightweight use their configured
   docs policy and request/assessment contract. Do not silently re-enable disabled
   optional sync. For affected enabled projections, run `speckit.docs-sync.run`
   through its owner with `repair=1` and the reserved attempt number; never
   directly edit generated projections.
   A missing required tool/rule blocks
   the repair, not a claimed successful refresh.
3. Re-run `speckit.docs-sync.package-readme` for affected README surfaces after any
   projection sync, supplying the actual run, lane, reserved attempt number,
   `repair=1`, and package paths. Respect its `auto|required|off` policy and report
   actual outcomes/limits. A required blocked
   result blocks repair completion. Re-check source-to-README facts on repaired
   contents rather than relabeling a previous verdict. For any project README the
   repair touches, re-run the structure guard and report `README_STRUCTURE` plus
   `README_MOVES` against the repository base; under `required`, a blocked
   structure blocks the repair instead of being recorded as an accepted append.
4. Keep writes within the authorized lane/task paths. For Feature, include needed
   documentation work in the same repair task/packet and perform it before that
   task's Quality/Standards/Review/commit gate. At outgoing scope, reconcile those
   task receipts; remaining documentation changes return to the same task queue,
   not direct post-commit source edits or a hidden second execution loop. Bugfix
   preserves original official reports; Lightweight stays within its request.
   If new authorized paths or material scope/design decisions are needed, use the
   existing lane escalation/approval rules instead of silently extending scope.
5. Refresh checks against the final code and documentation contents. In Feature
   task scope, the repaired task owns one pre-commit review of the combined
   contents, so a separate whole-diff Review is not required before that commit
   check. In Bugfix/Lightweight, complete the refresh and hand the combined result
   to the normal independent review/re-review. Never let the refresh turn an
   open finding into resolved. Persist the refresh outcome and original input identity
   in the existing task/round checkpoint; no new durable ledger or extra budget.

Report `DOCS_REFRESH: refreshed | unchanged | not-applicable | blocked`, affected
surfaces/packages, commands and actual results, reused receipt identity, and any
remaining gaps. Report sources-only changes as such; a documentation refresh does
not prove implementation correctness or resolve reviewer findings itself.
