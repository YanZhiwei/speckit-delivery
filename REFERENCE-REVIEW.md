# Reference review

The distribution was informed by public patterns from GitHub Spec Kit,
Anthropic Skills, Superpowers, and DeepSeek Harness.

Adopted patterns: one clear root entry point, one capability per extension,
composable workflows, a memorable `$sd` facade, progressive disclosure,
version-pinned catalogs, and clean-project installation evidence.

Deliberately excluded: repository-specific paths or commands, one monolithic
workflow prompt, claims of equivalent parallelism across hosts, direct edits to
generated projections, and unrelated repository-wide simplification.

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
