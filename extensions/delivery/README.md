# Spec Kit Delivery Core

Creates project-local delivery configuration, checks that installed delivery
components are coherent, routes a request, assembles code context, and renders a
final pull-request handoff. `speckit.delivery.doctor` runs first: it blocks a
workflow when an extension or workflow is stale, a code family lacks a Quality
Profile, or a documented rule lacks an owner and enforcement mechanism.

`speckit.delivery.context` is the optional code-context step: when the project
has a local `.codegraph/` index it reports entry points, callers, and affected
tests for the change; otherwise it degrades to a partial brief with the gaps
named. It never initializes an index and never treats the graph as correctness
evidence. `delivery-config.yml` controls it with `code_context: auto | off`.

Distributed defaults do not assume a language, framework, ADR path, or
verification command.
