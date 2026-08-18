# Distribution

## Release units

Each extension is packaged as a zip whose root contains `extension.yml`. Workflows are distributed as version-tagged raw YAML. The bundle is built with `specify bundle build` after all component references resolve through versioned catalogs.

```text
release v0.1.0
├── decision-0.1.0.zip
├── ralph-0.1.0.zip
├── review-0.1.0.zip
├── simplify-0.1.0.zip
├── evidence-0.1.0.zip
├── docs-sync-0.1.0.zip
├── delivery-0.1.0.zip
└── speckit-delivery-0.1.0.zip
```

Catalog URLs should be pinned to the same tag as the bundle. A release must not depend on mutable `main` content.

## Local verification

From a clean temporary Spec Kit project:

```bash
specify init . --integration codex --ignore-agent-tools --force --script sh

specify extension add --dev /path/to/speckit-delivery/extensions/decision
specify extension add --dev /path/to/speckit-delivery/extensions/ralph
specify extension add --dev /path/to/speckit-delivery/extensions/review
specify extension add --dev /path/to/speckit-delivery/extensions/simplify
specify extension add --dev /path/to/speckit-delivery/extensions/evidence
specify extension add --dev /path/to/speckit-delivery/extensions/docs-sync
specify extension add --dev /path/to/speckit-delivery/extensions/delivery

specify workflow add --dev /path/to/speckit-delivery/workflows/feature-delivery/workflow.yml
specify workflow add --dev /path/to/speckit-delivery/workflows/bugfix-delivery/workflow.yml
specify workflow add --dev /path/to/speckit-delivery/workflows/lightweight-delivery/workflow.yml

specify bundle validate --path /path/to/speckit-delivery/bundle
specify bundle build --path /path/to/speckit-delivery/bundle --output ./dist
python scripts/check_links.py
```

`bundle validate` resolves components from installed components and active catalogs. Installing the local components first makes the structural development check deterministic. Release testing must also exercise catalog-based installation in a second clean project.

## Release checklist

1. Update every changed component version and `CHANGELOG.md`.
2. Update extension, workflow, and bundle catalogs to the same tag.
3. Package every extension with its manifest at archive root.
4. Validate local development installation in a clean project.
5. Validate catalog installation in another clean project.
6. Build the bundle artifact with the target Spec Kit version.
7. Confirm README commands use the released version.
8. Publish the GitHub Release and attach artifacts.
9. Record installation evidence in the release notes.

## README contract

The root README owns product value, quick start, supported paths, and project status. Component READMEs own command-level installation, outputs, configuration, and safety. Architecture rationale belongs in `docs/`; catalogs and manifests own exact machine-readable versions.
