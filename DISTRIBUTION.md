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

## Local verification

Use a clean temporary Spec Kit project, install every local extension and all
three workflows, then run:

```bash
specify bundle validate --path /path/to/speckit-delivery/bundle
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
