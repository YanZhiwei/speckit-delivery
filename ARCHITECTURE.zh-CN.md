# 架构说明

Spec Kit Delivery 是 Spec Kit 之上的分发层，不是 Spec Kit 的 Fork，也不替换项目
已有流程。它通过可独立安装的扩展补充交付能力，并用 Workflow 和 Bundle 组合。

| 组件 | 负责 | 不负责 |
| --- | --- | --- |
| Core Spec Kit | Spec、Plan、Tasks 和核心实现命令 | ADR 生命周期、交付证据、Provider 编排 |
| Workflow | 阶段顺序、Gate、有限循环、恢复点 | 隐藏在 Agent 文本中的语义判断 |
| Extension | 一个窄命令族及其产物契约 | 整体交付编排 |
| Bundle | 固定版本的组件组合 | 组件实现和宿主 Integration |
| Quality Gate | 项目本地可执行检查和关闭判定 | DRY 或架构语义判断 |
| Standards Review | Task 或批次的语义规范判定 | 重跑机械质量检查 |
| Code Review | 独立六维 Task／最终评审和问题核对 | 修改代码、自批修复或关闭任务 |
| Delivery Review Fix | 一次已核实、由 Lane 负责人执行的修复及持续轮次记录 | Review 判定或第二套执行队列 |
| Delivery Slice | Slice 边界、Task 映射、trunk-safe 分类、合并策略与 Slice／Rollup 交接 | 需求、Task 生成、代码修改、Review 判定、分支或 PR 创建 |
| Delivery Close | 记录 PR 真实结果并退役运行工作区 | 修改代码、变更远端 PR 或其他 Run 的记录 |
| Package README | 面向使用者的安装／API／限制，以及面向维护者的开发／发布契约；内容取自真实包内容 | 代码行为、生成文档或发布动作 |
| Ralph | 依赖就绪任务执行、Git Task 提交、Slice 边界验证和完成确认 | 规划或自行关闭任务 |
| Diagram | 每次变更一张有证据的视图，默认 Mermaid | 测试证据、评审判断或安装器行为 |

系统分成三个控制面：

```text
Agent Skill       执行语义工作
Spec Kit Workflow 排列阶段、Gate 和有限循环
Machine State     承载文本无法可靠表达的 Verdict
```

`0.1.x` 与 `0.2.x` 通过显式 Gate 和有限循环工作；`0.2.x` 增加交付切片与合并策略，
后续版本再引入机器可读的阶段和 Verdict 状态文件。

## 决策与关闭生命周期

```text
检索既有决策 → 代码／历史／开源参考取证 → 范围确认
→ specify/clarify → 解析 ADR → plan → Proposed ADR → 设计确认
→ 实现 → review → 对齐 HEAD → Accepted ADR
```

ADR 是主题级、长期的记录；Spec 是 Feature 级记录；Constitution 是跨 Feature 的
治理规则。Accepted ADR 必须脱离被忽略的 Spec 文件、Task ID、Review 轮次和对话记录
独立成立。

Delivery Explore 负责取证和候选范围，不负责 ADR 策略、Bug 根因诊断或详细实现设计。
Router 和 Workflow 负责范围确认与 Lane 调整，现有 plan gate 负责设计确认；Core
Spec Kit 继续负责 spec/plan/tasks。Spec 前展示现状和候选改动目录树，Tasks 前再展示
确定版目录、文件职责、接口和测试。详见 [Delivery 契约](extensions/delivery/README.md)。
Lightweight 不继承完整取证仪式。

Delivery Close 只负责持久记录的结果和运行工作区，不发布、不合并，也不改写其他 Run；
`evidence.md` 始终是唯一持久记录。安装、升级和初始化脚手架记录属于项目证据根目录的
运维性一次性记录，不是交付 Run。

Package README 由 Docs Sync 负责，在每条 Lane 的 Review 之前运行。内容取自包清单和
公开面；同类项目研究只影响结构，不复制文案。生成文档仍归投影同步，正确性判断仍归
Review。

直接 Workflow 使用明确 `delivery_run`、固定磁盘取证包和前一 Gate 的真实选择跨宿主
进程传递。只有同会话 Router 可暂存上下文；临时直接运行仍需本地忽略文件。消费者记录
批准，Gate 不编辑文件，Feature／Bug 标识确定后不搬移 Run 包。这不等于自动语义判断。

Ralph 只把 `tasks.md` 当作执行队列；已批准的 `slices.md` 只提供评审／合并边界，
不得增删或重排 Task。可移植协议是在干净的 `ralph/<feature>` 分支上每轮执行一个
依赖就绪任务；启用切片时使用 `ralph/<feature>/<slice>`，stacked Slice 基于上一层，
integration Slice 基于集成分支。并行执行必须使用隔离 Worktree 和 Provider 专用集成
契约，不能在共享 Worktree 中进行。只有编排器检查变更路径、证据，并确认当前代码和需求
快照的 `QUALITY_VERDICT: pass`、`STANDARDS_VERDICT: pass` 与
`REVIEW_VERDICT: pass` 后，才能标记 `[X]`；快照包括未提交和相关未跟踪内容，随后创建
该 Task 的 Git 提交。Slice 边界还要验证 `standalone` 的目标分支 prefix build/test、
`flagged` 的开关关闭／打开行为，或 `integration-only` 的 checkpoint。

Delivery Slice 在 Tasks 生成后运行，把真实 Task ID 绑定到可独立评审的 Slice。合并方式
由证据推导而非偏好：`standalone`／`flagged` 且顺序线性时可用 `stacked`；存在
`integration-only` 时使用 `integration`；证据不足或策略冲突返回 `needs_decision`。
Slice Gate 记录用户实际批准；prefix check 失败时回到切片重新分类，不继续堆叠。Handoff
负责单 Slice 与 Rollup PR 文本，不创建或合并 PR。合并策略明确：Slice 默认 squash，
integration Rollup 使用 merge commit，禁止 squash 最终 Rollup、rebase 共享集成分支，
或把目标分支 merge 进 stack 分支。

质量闸门负责格式、lint、类型、测试和已配置的复杂度；DRY、模块归属、目录边界、
公共 API 和架构一致性仍由 Simplify、Review 与 ADR 负责。

`speckit.quality.brief` 是编辑前的提醒层，`speckit.quality.check` 是编辑后的机械关闭闸门；
`speckit.review.standards` 对 DRY、归属、分层方向、公共接口、注释意图和 ADR 影响给出
语义关闭判定。
宿主支持 Hook 时可以调用 Brief；即使没有 Hook，Workflow 也会主动调用它，因此跨宿主
流程仍然有效。

Code Review 复用有效检查回执，但独立覆盖需求符合性、代码质量、架构与设计规范、运行
正确性、安全与兼容性、测试有效性。遵循 Plan 不能掩盖有证据的设计缺陷，重大重设计返回
确认。[Reviewer 模板](extensions/review/templates/reviewer.md) 统一拥有快照、覆盖、
Verdict 与问题生命周期策略；编排器保存报告，Reviewer 保持只读。未被用户明确接受的
自审降级属于 incomplete。

三条 Lane 均采用有界 `review.run → delivery.review-fix` 槽位、最终 Review 与可中止 Gate。
修复命令负责 Lane 路由；Feature 保持 `tasks.md` 唯一队列，Bugfix／Lightweight 不强制
Feature 文档。可移植 YAML 最多提供三次修复槽位，再取配置上限的较小值；跨恢复／新 HEAD
不重置，完整当前 pass 后剩余槽位 no-op。这仍是引导式提示契约，不是自动语义状态引擎。
ADR 等后置变更需要 freshness review，交接再次核对实际代码和需求快照。

Quality 拥有原始执行身份和精确输入／配置的 Hook 复用策略，调用者不能用当前哈希标注旧
结果。Bugfix 复审续修使用 Delivery 的 Assessment 约束适配器，保留官方原始 fix/test
报告并新增逐轮证据，不绕过自动覆盖保护；首次 Bug 命令保持不变。
