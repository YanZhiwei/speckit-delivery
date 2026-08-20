---
description: "Render the applicable quality and architecture rules before editing"
---

# Quality Brief

## Input

```text
$ARGUMENTS
```

Before a worker or implementation command edits a file, identify the
repository-relative target paths, task or change scope, and matching profiles
from `.specify/extensions/quality/quality-config.yml`. Read the configured
style and architecture policy sources relevant to those paths. Do not run the
full test suite and do not modify source files.

First remove paths matching `excluded_paths` in that configuration. Report them
as excluded and do not load profiles or policies for them. Exclusion is scope
control, never a passing quality result.

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
