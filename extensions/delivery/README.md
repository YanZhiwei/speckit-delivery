# Spec Kit Delivery Core

Creates project-local delivery configuration, checks that installed delivery
components are coherent, routes a request, and renders a final pull-request
handoff. `speckit.delivery.doctor` runs first: it blocks a workflow when an
extension or workflow is stale, a code family lacks a Quality Profile, or a
documented rule lacks an owner and enforcement mechanism. Distributed defaults
do not assume a language, framework, ADR path, or verification command.
