# Lightweight Delivery Workflow

Avoids full feature artifacts for mechanical or behavior-preserving work. It starts
the portable [Delivery runtime](../../extensions/delivery/templates/runtime.md),
which records run identity and guarded stage results. The implementation command
must escalate when scope, public behavior, architecture, or compatibility is
unclear.

Supply required `delivery_run=<safe-id>`, a verified `runtime_python` invocation,
and reuse both on resume so separate host processes share one
review/report/attempt location, without Feature documents.

Simplify candidates are optional. A recorded rejection skips application; accepted
candidates are delegated to `delivery.lightweight` within the bounded request and
then verified by native `simplify.verify`. Package README judgment runs afterwards,
then current Quality/Standards and Review cover the final contents. A candidate
that expands behavior, compatibility, data, security, or architecture recommends a
lane change instead of silently growing this one.

Six-dimensional Review is proportional to the bounded request; non-applicable
surfaces need an explanation, not a full Feature Spec. Review starts with one
independent native pass; runtime `needs --kind repair` enters a durable bounded
repair loop only for a current confirmed repairable blocker. Attempts/findings
survive resume and new HEAD, and a current complete pass skips remaining
dispatches. The final runtime guard and aborting human gate reject
blocked/incomplete or exhausted repair results before evidence/handoff. If a review
repair changes a package/public surface, the same reserved attempt refreshes
affected documentation before its current checks and re-review.

Runtime conditions are actual results, not fixed no-op slots. Conventional host
semantic judgment is not replaced by this transport. See the
[Reviewer contract](../../extensions/review/templates/reviewer.md).
