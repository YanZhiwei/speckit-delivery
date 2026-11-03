---
description: "Render the applicable quality and architecture rules before editing"
---

# Quality Brief

## Input

```text
$ARGUMENTS
```

## Diagnosis methods

When an explicitly identified Bugfix or bounded task needs a diagnosis/testing
method, `method_adapters.diagnose` in Delivery configuration selects it. Builtin
(or no configuration) uses the worker's normal method with no extra helper/model
round. For an explicit external method, the coordinator and the same worker read
the installed `.specify/extensions/delivery/templates/method-adapter.md`; the coordinator validates
its local resources and gives the worker `speckit.delivery.method phase=diagnose`
plus the actual lane/run/assessment-or-task scope. The helper returns evidence-bound analysis
only, including proposed regression design. The worker remains the sole owner of
any approved probe/test execution and its report. Diagnose does not replace
official Bug Assess/Fix/Test, authorize a repair, add a queue, or close a task;
missing helper support follows only its explicit fallback/block policy.

## Brief

Before a worker or implementation command edits a file, identify the
repository-relative target paths, task or change scope, and matching profiles
from `.specify/extensions/quality/quality-config.yml`. Read the configured
style and architecture policy sources relevant to those paths. Do not run the
full test suite and do not modify source files.

First remove paths matching `excluded_paths` in that configuration. Report them
as excluded and do not load profiles or policies for them. Exclusion is scope
control, never a passing quality result.

Honor the supplied lane and run; do not infer Feature from unrelated files or
branch state. For an explicitly identified Feature, resolve its exact plan from
the supplied canonical exploration packet or scope-bound plan/excerpts, validate
the recorded approved identity, and read the applicable `Architecture constraints`
rows. Do not guess the newest plan or create Feature artifacts for
Bugfix/Lightweight. Include constraint IDs, sources,
owners, mechanisms, and unresolved gaps in `ARCHITECTURE`. Carry the actual plan
reference into the worker packet; missing/stale required plan context stops
Feature edits. A planned check is work still to do, and semantic review is not
an automated check. Only configured, verified commands go in `VERIFY_AFTER_EDIT`.

Return a compact brief:

```text
QUALITY_BRIEF
FILES: <repository-relative paths>
PROFILES: <matched profile ids>
RULES:
- <format/lint/type/test/complexity/comment/directory-layout rule>
ARCHITECTURE:
- <relevant ownership, directory, dependency, or ADR constraint>
AVOID:
- <known anti-pattern or scope boundary>
VERIFY_AFTER_EDIT:
- <configured command or none>
```

The brief is advisory context, not a pass. If no profile matches a non-excluded
changed source path, say `PROFILE_GAP: <path>` and instruct the caller to stop or
resolve the project policy before editing. Do not invent a language tool,
package manager, complexity threshold, or architecture rule. If a rule is only
semantic (for example DRY or ownership), identify Simplify/Review/ADR as its
owner instead of claiming it can be mechanically checked here.
