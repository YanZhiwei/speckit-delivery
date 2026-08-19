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
| Ralph | 依赖就绪任务调度和完成确认 | 规划或自行关闭任务 |

系统分成三个控制面：

```text
Agent Skill       执行语义工作
Spec Kit Workflow 排列阶段、Gate 和有限循环
Machine State     承载文本无法可靠表达的 Verdict
```

`0.1.x` 通过显式 Gate 和有限循环工作；计划中的 `0.2.x` 会引入机器可读的阶段和
Verdict 状态文件。

## 决策与关闭生命周期

```text
检索既有决策 → specify/clarify → 解析 ADR → plan
→ Proposed ADR → 实现 → review → 对齐 HEAD → Accepted ADR
```

ADR 是主题级、长期的记录；Spec 是 Feature 级记录；Constitution 是跨 Feature 的
治理规则。Accepted ADR 必须脱离被忽略的 Spec 文件、Task ID、Review 轮次和对话记录
独立成立。

Ralph 只把 `tasks.md` 当作调度队列。只有编排器检查变更路径、证据，并确认当前
HEAD 和任务范围的 `QUALITY_VERDICT: pass` 及 `STANDARDS_VERDICT: pass` 后，才能标记 `[X]`。

质量闸门负责格式、lint、类型、测试和已配置的复杂度；DRY、模块归属、目录边界、
公共 API 和架构一致性仍由 Simplify、Review 与 ADR 负责。

`speckit.quality.brief` 是编辑前的提醒层，`speckit.quality.check` 是编辑后的机械关闭闸门；
`speckit.review.standards` 对 DRY、归属、分层方向、公共接口、注释意图和 ADR 影响给出
语义关闭判定。
宿主支持 Hook 时可以调用 Brief；即使没有 Hook，Workflow 也会主动调用它，因此跨宿主
流程仍然有效。
