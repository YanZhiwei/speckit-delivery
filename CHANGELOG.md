# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [Unreleased]

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
