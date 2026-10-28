# 更新日志

所有重要变更遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)
和语义化版本规范。

## [Unreleased]

## [0.1.2] - 2026-10-28

### 新增

- 新增 Delivery Diagrams 扩展与 `speckit.diagram.render`：默认输出 Mermaid，仅在
  项目已安装渲染器时生成 SVG/PNG/HTML，并可返回 `N/A` 而不编造图。
- 在 `skills/` 增加可选、版本固定的 `archify`（v3.2.0）和
  `fireworks-tech-graph`（v1.2.0）渲染器副本，附带来源、提交和 SHA-256。
- PR Handoff 模板新增“当前设计/本次改动/影响范围/设计图/AI 使用披露”小节。
- 新增 `speckit.delivery.context`：规划前或诊断前的可选代码上下文简报。项目存在
  `.codegraph/` 时报告入口、调用方和受影响测试；不存在时返回带缺口说明的部分结果，
  且不会初始化索引。

### 变更

- `speckit.delivery.handoff` 明确模板解析顺序：项目配置路径 → 仓库 `.github` 模板 →
  扩展内置模板 → 命令内的小节契约。
- Code Review 与 Standards Review 增加四项纪律检查：测试行为而非实现、修复根因而非
  症状、先减后加、可独立验证的单元。
- Quality Gate 文档说明 CRAP、重复度和变异阈值何时才算真正门禁：必须由项目自有
  wrapper 产生非零退出，只写报告的工具不算。
- Bundle 现在包含 10 个扩展；Diagram 本身不增加 Workflow 步骤。
- Feature 与 Bugfix Workflow 分别在 `plan` 和 `assess` 之前增加非阻塞的代码上下文
  步骤；缺少索引或工具时只降级结果，不中断交付。可用 `code_context: off` 关闭。

### 修复

- 修复 `pull_request_template` 默认指向不存在的根 `templates/` 路径；模板随
  delivery 扩展分发，默认值改为 `null` 并回退到 `.github` 模板。

## [0.1.1] - 2026-10-28

### 新增

- 新增 `Prepare release PR` Workflow 和 `stamp_release.py` 发布前置：统一写入组件/Catalog
  版本，完成校验并创建可审查的发布分支，不打 Tag、不发布。
- 新增带有项目级 Profile、可执行检查发现和当前 HEAD 任务闭环 verdict 的项目质量闸门 Extension。
- 新增在模型编辑前注入文件级规则的 Quality Brief 命令。
- 新增返回任务或批次语义闭环 verdict 的 Standards Review 命令。
- 新增在 Workflow 执行前检查组件过期、Profile 缺失和文档规则未归属情况的 Delivery Doctor 命令。

### 修复

- Workflow Catalog 的 `requires` 现在与 Workflow YAML 一致，Bundle 在 Spec Kit 1.2.3
  上不会再于组件安装前失败。
- Bundle 安装最低版本调整为 Spec Kit `>=1.2.3`；单独安装 Extension 和 Workflow 仍为
  `>=0.16.4`。
- 分发校验现在检查 Catalog URL、Manifest/Workflow 版本、Workflow requirements、Bundle
  组件固定版本，并从本地 release-shaped Catalog 执行真实 Bundle 安装。

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
