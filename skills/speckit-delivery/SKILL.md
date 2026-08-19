---
name: speckit-delivery
description: 启动 Speckit Delivery 的手动 SDD 路由。
disable-model-invocation: true
---

# Spec Kit Delivery

Use the installed `speckit.delivery.route` command with the user's request.
That extension command is the canonical cross-integration owner of lane
routing, ADR lifecycle, Ralph orchestration, and completion conditions.

The native skill is a convenience surface only. Preserve the selected project's
existing workflow and report a missing Delivery extension as an installation
blocker. Do not publish, push, merge, or create external resources unless the
user separately authorized that action.
