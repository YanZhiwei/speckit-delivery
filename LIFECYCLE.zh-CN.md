# 产物生命周期

| 产物 | 负责人 | 默认生命周期 | 最终要求 |
| --- | --- | --- | --- |
| Constitution | 项目 | 持久 | 约束所有 Feature，不能重复 ADR |
| Issue | Tracker | 持久 | 问题、范围、验收和结果 |
| `.specify/delivery/<feature-or-run>/exploration.md` | Delivery | 遵循 `artifact_policy` | 代码／历史／开源参考证据、现状和候选目录树、真实范围确认及限制 |
| `spec.md` / `plan.md` | Feature | 项目配置 | 行为契约和当前实现方案 |
| `tasks.md` | Feature/Ralph | 项目配置 | 唯一任务队列和完成状态 |
| `.specify/delivery/<run>/slices.md` | Delivery Slice | 遵循 `artifact_policy` | 已确认的 Slice 边界、trunk-safe 证据、合并策略和回滚；绝不是第二执行队列 |
| `.specify/delivery/<feature>/task-verdicts.yml` | Ralph | 临时 | Task 快照、Quality／Standards／Review 回执及已验证提交关联 |
| `.specify/delivery/<feature>/slice-verdicts.yml` | Ralph | 临时 | Slice base/head、Task 范围、prefix／flag／checkpoint 证据和合并方式判定 |
| Proposed ADR | 架构 | 跟踪 | 编码前的实现基线 |
| Accepted ADR | 架构 | 跟踪 | 与 HEAD 对齐的自包含事实 |
| 实际交付 Run 下的 `reviews/<scope>/review.yml` | 编排器 | 遵循 `artifact_policy` | 快照、六维判定、独立性、覆盖和稳定问题 ID |
| Review 修复检查点 | 编排器 | 与 Run 相同 | 跨恢复／新 HEAD 保留尝试次数、上限和未解决 ID |
| Quality Verdict | Task/Ralph | 默认临时 | HEAD、范围、Profile、检查和结果 |
| Standards Verdict | Task/Ralph | 默认临时 | HEAD、范围、语义规范判定和阻断项 |
| Evidence 报告 | 交付运行/PR | 持久摘要 | 命令、结果、环境风险，以及实际记录的 PR 结果（`delivered`／`abandoned`／`superseded`） |
| `.specify/delivery/<run>/pull-request.md` | Delivery Handoff | 遵循 `artifact_policy` | 渲染后的 PR 正文和 `gh pr create --body-file` 路径；不是 GitHub UI 模板 |
| PR 正文 | Pull Request | 持久 | 变更、风险、决策和证据 |
| Package README | 包负责人／Docs Sync | 持久 | 面向使用者的安装／API／限制，以及面向维护者的开发／发布契约；内容取自真实包内容 |

`slices.md` 是评审和合并边界计划。它绑定 `tasks.md` 的真实 Task ID，但不得增删或重排
Task。Slice 回执只证明一个边界的检查，不能替代 Task 回执或最终集成 Review。范围、设计、
Task 映射、prefix check 或合并策略变化后，必须刷新或废弃旧 Slice 计划。

## Spec 临时模式

允许忽略 Spec 文件，但恢复依赖原工作区；跨 Worktree Worker 必须注入 Task Packet
或复制相关摘录。Issue 和 PR 要保留稳定的需求与验收摘要，ADR 不能链接被忽略的
Feature 路径。只有交接、Review 和 ADR 对齐完成后才能清理。

对于多人协作，跟踪模式仍然更安全。

实际 Feature/Run 标识尚未确定时，将取证包显式保留在上下文中，不虚构保存路径；位置
确定后保存并更新同一份记录。Spec 和 Plan 消费其证据，详细实现设计仍归 Plan。恢复时
核对 HEAD 和相关工作区变化；范围重大扩大需要重新确认。取证记录为临时文件时，长期
Issue、ADR 和交接摘要不能依赖其路径或对话历史。

上述仅上下文降级限于共享会话 Router。直接 YAML 入口先取得明确 `delivery_run`，在退出
前将包保存到固定 Run 路径；临时策略也需要本地忽略文件。后续 Feature／Bug 身份只写入
该包，不搬移路径。消费者接收确切引用与真实 Gate 选择，Gate 不编辑包，也不隐式批准 ready。

## 交付记录结果与退役

`evidence.md` 是持久记录；`.specify/delivery/<run>/` 下的其他文件都是运行工作区，
遵循 `artifact_policy`。策略为临时时，exploration、slices、回执、verdict、Review 报告
和渲染后的 PR 正文只保留在本地，通过 PR 正文发布。证据绑定 PR 实际发布的已审阅
HEAD 与 PR 引用；合并版本在事后记录，不在发布前虚构。

PR 合并或关闭后，由 `speckit.delivery.close` 记录真实结果。`merged` 记为
`delivered`；未合并而关闭记为 `abandoned`，只保留一份自包含的退役说明；被替代的
运行记为 `superseded`，并给出可解析的 `superseded_by`。没有 `status` 表示仍在进行；
与实际 PR 结果矛盾的记录不算收口。退役只删除该 Run 的工作区文件，绝不删除
`evidence.md` 或其他 Run。

安装、升级、初始化脚手架和手工治理动作是运维性一次性记录，不是交付运行。其权威
记录应放在项目持久证据根目录，不要在 `.specify/delivery/` 下维护第二份副本。

## Review 与修复记录

[Reviewer 契约](extensions/review/templates/reviewer.md) 统一拥有问题和快照规则。
报告绑定 base／HEAD／merge-base、实际内容和需求，不能只看 HEAD；未提交和相关未跟踪文件
都计入。只能排除声明的记账内容；ADR／Spec／测试／源码变化会使旧结论失效。问题保留
`open → fixed-pending-review → resolved` 或有证据的 `dismissed` 状态；遗漏、新快照和
修复者声明都不能自动关闭问题。

Task 回执保留预提交 Review 身份，仅在核对内容等价后关联结果提交，不能改称最终 HEAD
评审；集成覆盖属于最终 Review。编排器记录不能造成提交后的跟踪文件脏状态。恢复保留修复
预算，耗尽后保留未解决问题；后置治理输入变化必须在交接前复审。临时报告的长期摘要需自包含。

Bugfix 续修保留原始 assessment／fix／test 报告，逐轮证据保存于实际 Bug 的
`review-repairs/<delivery-run>/round-<n>/`，由编排器检查点引用。检查原始回执保留真正执行时
的输入／配置身份；缺失时重跑，不用当前哈希重新标注旧结果。
