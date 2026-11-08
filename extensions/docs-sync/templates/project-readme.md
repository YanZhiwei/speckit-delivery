# <project-name>

<!-- One paragraph: what the project provides, who should use it, and what it
     deliberately does not do. Derive it from the repository, not from
     marketing copy. -->

This README is the index. Keep it short: claims, the shortest working path, and
links. Detail belongs in the documents listed under Documentation map.

## Contents

- [Overview](#overview)
- [Quick start](#quick-start)
- [Capabilities](#capabilities)
- [Compatibility](#compatibility)
- [Documentation map](#documentation-map)

## Overview

<!-- Two or three sentences on the problem and the shape of the solution.
     Current behavior only: no release history, no "since version X". -->

## Quick start

```bash
<shortest sequence that actually works in a clean checkout>
```

<!-- Prerequisites belong here only as one line plus a link; the full matrix
     lives in the document that owns it. -->

## Capabilities

| Capability | Entry point | Read more |
| --- | --- | --- |
| <capability> | <command or API> | `docs/<topic>.md` |

<!-- One row per capability, with the read-more cell as a link to the real
     docs page. When a capability needs more than a few sentences, write
     docs/<topic>.md and keep one row here. Do not grow this table into a
     manual. -->

## Compatibility

| Item | Requirement |
| --- | --- |
| <runtime / host / tool> | <verified version floor> |

<!-- State each requirement once. A second copy in Quick start drifts. -->

## Documentation map

| Document | Contents |
| --- | --- |
| `docs/architecture.md` | Components, boundaries, ownership |
| `docs/quality.md` | Commands, gates, and their owners |
| `docs/operations.md` | Deploy, rollback, and known limits |

<!-- Link each path here; every file under docs/ appears exactly once, so a new
     page is reachable from the entry point. This table is the README's growth
     surface: a new page adds one row, not one section. -->

## Adding to this README

<!-- Maintainer note; delete once the team knows the rule. -->

1. Change the section that already owns the fact.
2. If it no longer fits, move it to `docs/<topic>.md` and replace the text with
   one row in the table above.
3. Add a section only when nothing owns the fact, register it in Contents in the
   same edit, and keep the configured line budget.
