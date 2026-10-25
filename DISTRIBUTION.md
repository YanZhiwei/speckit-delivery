# Distribution

## Release units

Each extension is a root-layout zip containing `extension.yml`; workflows are
versioned YAML; the bundle is built after catalog references resolve.

```text
decision  ralph  review  simplify  evidence  quality  docs-sync  delivery
                         + feature / bugfix / lightweight workflows
                         + speckit-delivery bundle
```

Catalog URLs must point to the same release tag. A release must not depend on
mutable `main` content.

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
cp -R /path/to/speckit-delivery/bundle /tmp/speckit-bundle-check/bundle
specify bundle validate --path /tmp/speckit-bundle-check/bundle
specify bundle build --path /path/to/speckit-delivery/bundle --output ./dist
python scripts/check_links.py
```

Release verification additionally installs from catalogs in a second clean
project. A release is ready only when manifests, catalogs, packaged roots,
README commands, and versions agree.

## README contract

Root README files own product value, quick start, supported hosts, and status.
Root bilingual reference files own durable user-facing explanations.
Extension READMEs own command installation, outputs, configuration, and safety.
Catalogs and manifests own exact machine-readable versions.
