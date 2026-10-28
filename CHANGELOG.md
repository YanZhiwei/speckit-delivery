# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [Unreleased]

## [0.1.2] - 2026-10-28

### Added

- Delivery Diagrams extension and `speckit.diagram.render`: Mermaid by default,
  a rendered SVG/PNG/HTML asset only when the project installed a renderer, and
  an explicit `N/A` instead of an invented diagram.
- Optional pinned renderer skills under `skills/`: `archify` (v3.2.0) and
  `fireworks-tech-graph` (v1.2.0), each with provenance, commit, and SHA-256.
- PR handoff template sections for current design, change map, impact, design
  diagram, and AI assistance disclosure.
- `speckit.delivery.context`: an optional code-context brief before planning or
  diagnosis. It uses the project's local `.codegraph/` index when present,
  reports entry points, callers, and affected tests, and degrades to a partial
  brief without initializing an index.

### Changed

- `speckit.delivery.handoff` now resolves the project path, then the repository
  `.github` template, then the extension default, then its section contract.
- Code Review and Standards Review now apply four discipline checks: behavior
  over implementation tests, cause over symptom, subtraction before addition,
  and independently verifiable units.
- Quality Gate documentation explains when CRAP, duplication, and mutation
  thresholds are real gates: only through a project-owned wrapper that exits
  non-zero, never by a report-only tool.
- The Bundle now contains 10 extensions. Diagram adds no workflow step.
- Feature and Bugfix workflows add a non-blocking code-context step before
  `plan` and `assess`. A missing index or tool degrades the brief; it does not
  stop delivery. Set `code_context: off` to skip it.

### Fixed

- The `pull_request_template` default no longer points at a non-existent root
  `templates/` path. The template ships with the delivery extension, the default
  is `null`, and the handoff falls back to the repository template.

## [0.1.1] - 2026-10-28

### Added

- `Prepare release PR` workflow and `stamp_release.py` preflight: stamp all
  component/catalog versions, validate, and open a reviewed release branch
  without tagging or publishing.
- Project Quality Gate extension with project-local profiles, executable check
  discovery, and a current-HEAD task-closure verdict.
- Pre-edit Quality Brief command for injecting file-scoped rules before model
  editing.
- Standards Review command with a task-or-batch semantic closure verdict.
- Delivery Doctor command that detects stale components, missing profiles, and
  unowned documented rules before workflow execution.

### Fixed

- Workflow catalog `requires` now matches each workflow YAML, so Bundle
  installation works on Spec Kit 1.2.3 instead of failing before component
  installation.
- Bundle installation now requires Spec Kit `>=1.2.3`; individual extensions and
  workflows retain their `>=0.16.4` floor.
- Distribution validation now checks catalog URLs, manifest/workflow versions,
  workflow requirements, bundle component pins, and performs a real Bundle
  install from local release-shaped catalogs.

### Changed

- Ralph and all delivery lanes now require both mechanical quality and semantic
  standards verification before task or outgoing-diff closure.
- Ralph now bridges Spec Kit tasks with a sequential per-task loop: it creates
  or reuses a `ralph/<feature>` branch, requires a verified Git commit before
  closing each task, and emits a machine-readable completion promise only when
  the committed task queue is empty.

## [0.1.0] - 2026-08-18

### Added

- Initial Spec Kit Delivery distribution scaffold.
- Decision memory, Ralph, review, simplification, evidence, documentation sync, and handoff extensions.
- Feature, bugfix, and lightweight workflow definitions.
- Versioned catalog templates and bundle manifest.
- Agent-native router skill, PR template, documentation, and evaluation prompts.
