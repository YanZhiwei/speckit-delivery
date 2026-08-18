# Spec Kit Delivery Bundle

Installs the official Spec Kit `bug` extension plus the Spec Kit Delivery extensions and three guided workflows.

Before release installation, add the versioned Extension and Workflow catalogs documented in the repository README. The bundle intentionally declares no integration and inherits the integration initialized in the target project.

## Installed workflows

- `feature-delivery`: full specification-driven delivery.
- `bugfix-delivery`: bounded defect assessment and regression path.
- `lightweight-delivery`: proportional path for small changes.

The bundle does not create a remote repository, publish a PR, or execute project-specific build commands without the target project's configuration and authorization.
