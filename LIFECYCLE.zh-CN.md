# 产物生命周期

| 产物 | 负责人 | 默认生命周期 | 最终要求 |
| --- | --- | --- | --- |
| Constitution | 项目 | 持久 | 约束所有 Feature，不能重复 ADR |
| Issue | Tracker | 持久 | 问题、范围、验收和结果 |
| `.specify/delivery/<run>/exploration.md` | Delivery | 遵循 `artifact_policy` | 代码／历史／开源参考证据、现状和候选目录树、真实范围确认及限制 |
| `spec.md` / `plan.md` | Feature | 项目配置 | 行为契约和当前实现方案 |
| `tasks.md` | Feature/Ralph | 项目配置 | 唯一任务队列和完成状态 |
| `.specify/delivery/<run>/slices.md` | Delivery Slice | 遵循 `artifact_policy` | 已确认的 Slice 边界、trunk-safe 证据、合并策略和回滚；绝不是第二执行队列 |
| `.specify/delivery/<run>/task-verdicts.yml` | Ralph | 遵循 `artifact_policy` | Task 快照、Quality／Standards／Review 回执及已验证提交关联 |
| `.specify/delivery/<run>/slice-verdicts.yml` | Ralph | 遵循 `artifact_policy` | Slice base/head、Task 范围、prefix／flag／checkpoint 证据和合并方式判定 |
| `.specify/delivery/<run>/runtime/` | Delivery Runtime | 本地忽略 | 仅保存编排检查点、负责人输入／结果、阶段、批准回执和有界尝试记账；不保存规划或证据内容 |
| Proposed ADR | 架构 | 跟踪 | 编码前的实现基线 |
| Accepted ADR | 架构 | 跟踪 | 与 HEAD 对齐的自包含事实 |
| `.specify/delivery/<run>/reviews/<scope>/review.yml` | 编排器 | 遵循 `artifact_policy` | 快照、六维判定、独立性、覆盖和稳定问题 ID |
| Review 修复检查点 | 编排器 | 与 Run 相同 | 跨恢复／新 HEAD 保留尝试次数、上限和未解决 ID |
| Quality Verdict | Task/Ralph | 默认临时 | HEAD、范围、Profile、检查和结果 |
| Standards Verdict | Task/Ralph | 默认临时 | HEAD、范围、语义规范判定和阻断项 |
| Evidence 报告 | 交付运行/PR | 持久摘要 | 命令、结果、环境风险，以及实际记录的 PR 结果（`delivered`／`abandoned`／`superseded`） |
| `.specify/delivery/<run>/pull-request.md` | Delivery Handoff | 遵循 `artifact_policy` | 渲染后的 PR 正文和 `gh pr create --body-file` 路径；不是 GitHub UI 模板 |
| PR 正文 | Pull Request | 持久 | 变更、风险、决策和证据 |
| Package README | 包负责人／Docs Sync | 持久 | 面向使用者的安装／API／限制，以及面向维护者的开发／发布契约；内容取自真实包内容 |

显式提供 `delivery_run` 后，所有 Run 级 Packet 和回执都以该 Run 为身份，
只能使用 `.specify/delivery/<run>/`。Feature slug 只是元数据，不能搬移或猜测
Packet。唯一的旧版降级是非切片、独立 Feature 且显式提供映射时的 Legacy fallback；
切片运行和 Workflow 必须使用固定 Run 路径。

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

## Runtime 编排与检查点

随扩展安装的可移植 Helper 位于
`.specify/extensions/delivery/scripts/delivery_runtime.py`。在项目根目录运行时，
需要 PATH 中有 Python 3.11 或更高版本以及 Git；Helper 只使用标准库和 Git，
不会调用模型、执行项目测试、修改产品代码或 Task、创建提交，或联系 Tracker。
状态 Schema 和负责人边界以[Delivery Runtime 契约](extensions/delivery/templates/runtime.md)为准。

`.specify/delivery/<run>/runtime/` 是编排记账目录；Spec Kit 的
`.specify/workflows/runs/` 运行账本同样属于本地状态。已声明的 Run 运维记录
（`runtime/`、`reviews/`、`receipts/`、verdict、`evidence.md`、PR 正文）不阻断干净
执行入口；源码、规划、测试、策略和无关脏路径仍然阻断。`init` 向 Git 的本地
`.git/info/exclude` 增加这两条精确规则，并保留已有条目；已跟踪文件不会取消跟踪。
这个本地忽略规则不改变 `artifact_policy`：Run 根目录的规划工件、Packet、回执和
`evidence.md` 仍遵循原有跟踪／临时策略；`evidence.md` 始终持久。

`/sd` 控制面提供以下与 Run 绑定的动作：

- `action=help` 说明所选 Lane、记录、Gate、Runtime 位置和下一安全动作，不启动
  Lane，也不调用模型。
- `action=status delivery_run=<id>` 只读取指定 Run；不带 Run 时列出所有 Run。
  它是只读的，不按最近修改时间猜测身份。
- `action=resume delivery_run=<id>` 只恢复同一 Run 的负责人动作、输入 Ticket、批准
  或已预留尝试；不会重置身份或重新分配尝试次数。
- `action=checkpoint delivery_run=<id> stage=initial|converge|simplify|outgoing-repair`
  应用[Core／Ralph 适配契约](extensions/delivery/templates/core-adapter.md)，核对已批准
  路径、指纹、Git 授权、当前 Analyze 结果和干净执行入口。协调者可在已有项目 Git
  授权下，只提交精确批准的规划路径；Helper 本身不提交。不能暂存无关改动、批准
  设计，也不能从脏入口启动 Ralph。
- `action=phase delivery_run=<id> name=<phase>` 只记录当前负责人阶段，不代表完成。
  Handoff ready 必须先有当前 Review 和同 Run 的 Evidence。

Workflow 的 Shell 条件消费 Runtime 输出的无换行 `needs` 布尔值。Need 为 false
时，条件分支完全不派发，不存在固定的“空操作模型槽位”。Review 和 Converge 的
预留尝试会跨进程恢复和新 HEAD 保留；原生修复负责人消费原尝试，达到上限且仍有
阻断项或不完整证据时，最终 `require` 守门会失败。Runtime 只检查传输身份、新鲜度、
完整性和原生报告哈希；Quality、Standards、Reviewer、Core 与 Ralph 仍是语义判定
负责人。合法 Envelope 或零退出码都不是自动语义判断。

Feature 的规划到执行检查点遵循 Core 适配契约，要求明确的批准路径、指纹、Git 授权
和干净工作区。Slice 规划之后只有一个合并的 Analyze／执行／Slice Gate，由 Delivery
写入真实选择后才能让 Ralph 消费批准的队列。这里不复制 YAML 的具体顺序或参数，详见
[Runtime 契约](extensions/delivery/templates/runtime.md)和[Core 适配契约](extensions/delivery/templates/core-adapter.md)。

## 交付记录结果与退役

`evidence.md` 是持久记录。`.specify/delivery/<run>/` 根下的文件是运行工作区，遵循
`artifact_policy`；其中的 `runtime/` 是上文所述的本地编排记账目录。策略为临时时，
exploration、slices、回执、verdict、Review 报告
和渲染后的 PR 正文只保留在本地，通过 PR 正文发布。证据绑定 PR 实际发布的已审阅
HEAD 与 PR 引用；合并版本在事后记录，不在发布前虚构。复用已批准的规划或证据输入
必须保持相关字节和需求／策略指纹不变。项目授权的规划提交只有在内容等价且仅涉及
批准路径时才能关联原批准；路径或字节变化必须重新展示并重新批准，不能给旧结果
补一个新哈希。

[Doctor](extensions/delivery/commands/speckit.delivery.doctor.md) 会按当前阶段和检查点判断
缺少 Evidence 是否真的是缺口：在合法的 Evidence 前置阶段、Run 仍处于活动状态时，
如果之前没有记录过 Evidence 且必需 Packet／检查点存在，可以暂时没有
`evidence.md`。Evidence 已记录后文件消失、最终／Terminal 阶段缺失文件，或之前记录
过的证据被删除，都是阻断项。其他 Run 只产生维护发现，不改变当前 Run 身份；远端
事实不可用时保持 `unverified`。

Handoff ready 不是 Terminal 结果：`HANDOFF_READY: ready` 只表示 Review 后的 PR
正文已准备好，仍需单独授权发布并等待实际结果。PR 合并或关闭后，由
`speckit.delivery.close` 记录真实结果。`merged` 记为 `delivered`；未合并而关闭记为
`abandoned`，只保留一份自包含的退役说明；被替代的运行记为 `superseded`，并给出可解析
的 `superseded_by`。如果 PR、Tracker、凭据或结果无法核验，Close 返回 `unverified`，
并在写入 Terminal 状态／历史或删除任何工作区之前停止。没有 `status` 表示仍在进行；
与实际 PR 结果矛盾的记录不算收口。退役只删除该 Run 允许的工作区文件，绝不删除
`evidence.md` 或其他 Run。

安装、升级、初始化脚手架和手工治理动作是运维性一次性记录，不是交付运行。其权威
记录应放在项目持久证据根目录，不要在 `.specify/delivery/` 下维护第二份副本。

## Review 与修复记录

[Reviewer 契约](extensions/review/templates/reviewer.md) 统一拥有问题和快照规则。
报告绑定 base／HEAD／merge-base、实际内容和需求，不能只看 HEAD；未提交和相关未跟踪文件
都计入。只能排除声明的记账内容；ADR／Spec／测试／源码变化会使旧结论失效。所选可选
方法的配置／资源身份也属于需求与策略身份，切换提供者同样使旧结论失效。问题保留
`open → fixed-pending-review → resolved` 或有证据的 `dismissed` 状态；遗漏、新快照和
修复者声明都不能自动关闭问题。

Task 回执保留预提交 Review 身份，仅在核对内容等价后关联结果提交，不能改称最终 HEAD
评审；集成覆盖属于最终 Review。编排器记录不能造成提交后的跟踪文件脏状态。恢复保留修复
预算，耗尽后保留未解决问题；后置治理输入变化必须在交接前复审。临时报告的长期摘要需自包含。

Bugfix 续修保留原始 assessment／fix／test 报告，逐轮证据保存于实际 Bug 的
`review-repairs/<delivery-run>/round-<n>/`，由编排器检查点引用。检查原始回执保留真正执行时
的输入／配置身份；缺失时重跑，不用当前哈希重新标注旧结果。
