# Lightweight Delivery Workflow

Avoids full feature artifacts for mechanical or behavior-preserving work. The implementation command must escalate when scope, public behavior, architecture, or compatibility is unclear.

Supply required `delivery_run=<safe-id>` and reuse it on resume so separate host
processes share one review/report/attempt location, without Feature documents.

Six-dimensional Review is proportional to the bounded request; non-applicable
surfaces need an explanation, not a full Feature Spec. Up to three safe
review/repair slots honor the lower configured budget, retain attempts/findings
across resume/new HEAD, and no-op after a current complete pass. Final review and
an aborting gate reject blocked/incomplete results before evidence/handoff.
These are guided contracts, not automatic semantic branching. See the
[Reviewer contract](../../extensions/review/templates/reviewer.md).
