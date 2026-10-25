# 更新日志

所有重要变更遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)
和语义化版本规范。

## [Unreleased]

### 新增

- 新增带有项目级 Profile、可执行检查发现和当前 HEAD 任务闭环 verdict 的项目质量闸门 Extension。
- 新增在模型编辑前注入文件级规则的 Quality Brief 命令。
- 新增返回任务或批次语义闭环 verdict 的 Standards Review 命令。
- 新增在 Workflow 执行前检查组件过期、Profile 缺失和文档规则未归属情况的 Delivery Doctor 命令。

### 变更

- 所有交付 Lane 和 Ralph 现在都要求同时通过机械质量检查和语义标准检查，才能关闭任务或 outgoing diff。
- Ralph 现在通过逐任务串行循环连接 Spec Kit Tasks：创建或复用 `ralph/<feature>` 分支，每个任务必须先验证 Git commit 后才能关闭，并且只有已提交的任务队列为空时才会发出机器可读的完成 Promise。

## [0.1.0] - 2026-08-18

### 新增

- 初始 Spec Kit Delivery 分发骨架。
- Decision Memory、Ralph、Review、Simplification、Evidence、Documentation Sync 和 Handoff Extension。
- Feature、Bugfix 和 Lightweight Workflow 定义。
- 版本化 Catalog 模板和 Bundle Manifest。
- Agent 原生 Router Skill、PR 模板、文档和评估 Prompt。
