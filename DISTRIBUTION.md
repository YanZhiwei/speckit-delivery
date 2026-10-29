# Distribution

## Release units

Each extension is a root-layout zip containing `extension.yml`; workflows are
versioned YAML; the bundle is built after catalog references resolve.

```text
decision  ralph  review  simplify  evidence  quality  docs-sync  diagram  delivery
                         + feature / bugfix / lightweight workflows
                         + speckit-delivery bundle
```

Catalog URLs must point to the same release tag. A release must not depend on
mutable `main` content.

## Release preparation PR

A release has two separate pipeline steps:

1. Add non-empty `## [<version>]` sections to both changelogs.
2. Run the manual **Prepare release PR** workflow with the target version and
   base branch.
3. The workflow runs `scripts/stamp_release.py`, which updates all extension,
   workflow, bundle, and catalog versions plus tag/download URLs. It then runs
   the distribution contract tests, local-catalog Bundle installation, and
   component packaging. It pushes `release/v<version>` and opens a PR.
4. Review and merge the PR. The preparation workflow never tags or publishes.
5. Run **Release distribution** against the merged commit with the same version.
   The release workflow also checks `stamp_release.py --version <version> --check`
   so an unstamped source cannot be published.

Do not write `bundles.json` back after publishing: an already-created Tag cannot
be changed safely, and the installers read the catalog at that Tag. Preparation
must happen before the Tag is created.

## Manual release workflow

The GitHub Actions `Release distribution` workflow is started manually from
the Actions page. Enter the semantic version and the source branch or commit.
The workflow builds and validates the distribution first; only after those
checks pass does it create `v<version>` and publish the GitHub Release assets.
Do not create a second release workflow or upload the archives by hand.

The selected source must already contain the matching manifests, catalogs,
README commands, and English/Chinese changelog entries. Reusing an existing tag
is allowed only when it already points to the selected source commit; a tag
pointing to a different commit is rejected.

The published Release body is rendered from the matching sections in
`CHANGELOG.md` and `CHANGELOG.zh-CN.md`. It includes bilingual Install and
What's Changed sections, the pinned CLI, Catalog, Bundle installation, and
version check commands. A missing or empty versioned section in either language
blocks release before the Tag is created.

## Local verification

Use a clean temporary Spec Kit project, install every local extension and all
three workflows, copy the bundle into that project, then run:

```bash
uv run --with pyyaml python scripts/stamp_release.py --version <version> --check
uv run --with pyyaml python scripts/validate_distribution.py
uv run --with pyyaml python scripts/test_validate_distribution.py
uv run --with pyyaml python scripts/test_stamp_release.py
python scripts/test_bundle_install.py
python scripts/test_bundle_install.py --integration codex
cp -R /path/to/speckit-delivery/bundle /tmp/speckit-bundle-check/bundle
specify bundle validate --path /tmp/speckit-bundle-check/bundle
specify bundle build --path /path/to/speckit-delivery/bundle --output ./dist
python scripts/check_links.py
```

`test_bundle_install.py` installs the built Bundle through local, release-shaped
catalogs in a clean project. It requires Spec Kit `>=1.2.3`, which is also the
Bundle's minimum; individual extensions and workflows remain installable on
`>=0.16.4`. Release verification additionally installs from published catalogs
in a second clean project. A release is ready only when catalogs, manifests,
workflow requirements, packaged roots, README commands, and versions agree.

The local Bundle test also checks that Explore/Review templates, review-fix,
and Ralph resources survive packaging/installation, the active host renders the commands, and all
three installed workflows match source. Its default host is OpenCode; the Codex
variant verifies Skills-mode rendering. Structural checks do not prove semantic
research quality or user approval; behavioral prompts live in `evals/evals.json`.

`scripts/test_workflow_handoff.py` additionally probes the real Spec Kit
Command/Gate boundary with fake host consumers and a temporary shared disk
packet: fresh contexts, actual gate choices, and missing-packet failures.
Run it in a Python environment containing `specify_cli` and PyYAML (verified
against Spec Kit 1.2.3). It is not live model execution or end-to-end delivery.

## README contract

Root README files own product value, quick start, supported hosts, and status.
Root bilingual reference files own durable user-facing explanations.
Extension READMEs own command installation, outputs, configuration, and safety.
Catalogs and manifests own exact machine-readable versions.
