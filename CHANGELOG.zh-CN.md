# 更新日志

所有重要变更遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)
和语义化版本规范。

## [Unreleased]

## [0.3.0] - 2026-10-31

### 新增

- `speckit.delivery.close`：记录 PR 的真实结果并退役交付运行。合并记为
  `delivered`；未合并关闭记为 `abandoned`，只保留一份自包含的 `evidence.md`
  退役说明；被替代记为 `superseded`，并给出可解析的引用。

### 变更

- Evidence 绑定 PR 实际发布的已审阅 HEAD 和 PR 引用，不再要求在发布前引用尚不存在的
  合并提交；合并结果由 `speckit.delivery.close` 事后记录，去掉“合并后再开 PR 改写
  证据”的循环。
- Delivery 命令明确区分持久 `evidence.md` 与运行工作区（`exploration.md`、
  `slices.md`、`receipts/`、verdict、review、渲染后的 PR 正文）。`artifact_policy:
  ephemeral` 时工作区只保留在本地。
- `speckit.delivery.doctor` 报告过期或矛盾的交付记录：有工作区但无证据、结果缺少
  必要引用或原因、`superseded_by` 无法解析，以及把安装／升级记录放在交付根目录而
  不是项目持久证据根目录。
- Route、Handoff、Lane 参考、`LIFECYCLE` 和 README 把收口写入交付完成条件；记录状态
  与实际 PR 结果矛盾时不算收口。

### 升级说明

- 已跟踪的运行工作区不会自动删除。对已合并或已关闭的 Run 运行
  `speckit.delivery.close`；下一次交付前先让 `speckit.delivery.doctor` 列出缺少结果或
  结果矛盾的记录。
- 先把安装／升级记录迁移到项目持久证据根目录，再退役其 `.specify/delivery/<id>/`
  副本。

## [0.2.2] - 2026-10-30

### 变更

- Delivery 随包兜底模板
  `extensions/delivery/templates/pull-request.md` 改为中文。只有目标项目未配置
  `pull_request_template` 且没有仓库自己的 `.github/pull_request_template.md` 时才使用；
  已有项目模板绝不覆盖。项目可通过配置或自己的 `.github` 模板保留其他语言。

### 升级说明

- 刷新 Delivery（或 Bundle）即可获得中文兜底模板。Handoff 的 `PR_BODY_PATH` 和
  `--body-file` 行为不变。
- 兜底模板只是格式默认值，不是 GitHub UI 安装。Init 仍只在用户明确批准时才复制到
  `.github/pull_request_template.md`。

### 验证与限制

- 分发与安装检查核对随包模板内容；行为评估覆盖 fallback 选择与项目覆盖。

## [0.2.1] - 2026-10-30

### 新增

- `speckit.delivery.handoff` 把审阅后的正文写入
  `.specify/delivery/<run>/pull-request.md`（或 `pull-request-<slice>.md`），
  输出 `PR_BODY_PATH`，并给出 `gh pr create --body-file` 提示。
- `delivery-config.yml` 新增 `install_pull_request_template`：仅当用户明确批准且项目
  没有现有模板时，Init 才可把静态兜底模板复制到
  `.github/pull_request_template.md`。
- 评估 28 覆盖“已安装 Delivery 但目标仓库没有 GitHub PR 模板”的场景。

### 修复

- 仅输出到对话不再算可持久化的 Handoff；正文必须存在于报告出的本地路径。
- 安装扩展不再被误解为自动改变 GitHub UI 模板；GitHub 仍读取目标仓库
  `.github` 文件，除非显式传入 `--body-file`。
- `speckit.delivery.doctor` 检查已配置的 PR 模板和 Handoff 正文路径契约。

### 变更

- 仓库默认 GitHub PR 模板改为中文；扩展随包兜底模板仍是独立的格式契约，不会替换
  目标项目的 `.github` 模板。

### 升级说明

- 升级 Bundle，或刷新 Delivery 和三条 Workflow；运行 Handoff 后使用输出的
  `PR_BODY_PATH` 配合 `gh pr create --body-file`。
- 已有项目 PR 模板不会被覆盖；静态模板安装必须显式开启。
- 扩展随包兜底模板仍为英文；是否中文化是独立的产品决策，不等同于本仓库默认模板。

### 验证与限制

- 分发校验拒绝无法输出 `PR_BODY_PATH` 和 `--body-file` 提示的 Handoff 命令；
  安装检查断言渲染后的 Handoff 命令包含该标记；评估 28 覆盖无模板场景。
- 本补丁不创建、推送或合并 PR；发布仍需单独授权。

## [0.2.0] - 2026-10-30

### 新增

- `speckit.delivery.slice` 与 `templates/slices.md`：把真实 Task ID 绑定到可独立评审的
  Slice，标注 trunk-safe 证据，并推导 `single`／`stacked`／`integration` 与合并策略。
- Feature Workflow 在 tasks 与 analyze 之间增加 `slice`／`slice-gate`，并把确认后的
  `slices.md` 路径传给 analyze、Ralph、Review 和 Handoff。
- Ralph 在 Slice 边界执行 `standalone` 目标分支 prefix check、`flagged` 开关关闭／打开
  证据、`integration-only` checkpoint，并写入 Slice 回执；不创建、推送或合并 PR。
- Handoff 支持单 Slice PR 与最终 Rollup，包含 stack map、合并顺序、Issue 关闭规则和回滚；
  禁止最终 Rollup 使用 squash。
- Delivery 配置新增 `pr_slicing`、Slice 预算、`stack_provider` 与 `merge_policy`。

### 变更

- `speckit.delivery.init` 先核实 stack、flag、merge queue、linear history 能力，再写入切片策略。
- `speckit.delivery.doctor` 把缺失 Slice 命令／模板／Gate 或非法 integration 合并策略视为
  stale／blocked。
- `tasks.md` 仍是唯一执行队列；`slices.md` 只提供评审／合并边界，不得增删或重排 Task。

### 升级说明

- 升级 Bundle，或同时刷新 Delivery 扩展和三条 Delivery Workflow。缺少
  `slice`／`slice-gate` 的旧 Feature Workflow 视为 stale，升级后运行
  `speckit.delivery.doctor`。
- 现有项目可用 `pr_slicing: off` 保持单 PR；新配置默认 `pr_slicing: auto`，
  但提出多个 Slice 时仍需通过 Slice Gate。
- 没有原生 Stacked PR 能力时设置 `stack_provider: manual`，不要声称支持原生
  Provider 或仓库并不存在的 Merge Queue。

## [0.1.4] - 2026-10-29

修正 Doctor 对共享 Reviewer 契约的路径引用。

### 修复

- Doctor 现在显式引用 Review 已安装的
  `.specify/extensions/review/templates/reviewer.md`，不再使用扩展相对路径
  `templates/reviewer.md`。宿主会按命令所属扩展重写裸相对引用，因此 `0.1.3` 生成了
  不存在的 Delivery 路径，即使 Review 已正确打包并安装模板，也会产生错误的就绪阻塞。
- 分发校验现在拒绝依赖隐式 Delivery 归属的 Doctor Reviewer 引用；干净 Bundle 安装检查
  会在 OpenCode 与 Codex Skills 两种宿主上断言渲染后的 Doctor 指向 Review。

### 升级说明

- 升级 Bundle，或同时刷新 Delivery 与 Review，然后通过当前宿主重新运行
  `speckit.delivery.doctor`。已有安装可通过生成命令中的错误路径
  `.specify/extensions/delivery/templates/reviewer.md` 识别。
- 命令面、配置格式、Review 六维、快照、修复预算和运行时依赖均未改变。最低 CLI 要求
  仍为：单独组件 Spec Kit `>=0.16.4`，Bundle 安装 `>=1.2.3`。

### 验证与限制

- 仓库校验及变异夹具覆盖修正后的引用；OpenCode 与 Codex Skills 的干净 Bundle 安装会核对
  渲染命令和已安装 Review 模板。
- 缺少本地质量工具仍是环境阻塞，不是 Doctor 路径缺陷。本补丁不安装、不跳过、也不放宽
  项目质量检查。

## [0.1.3] - 2026-10-29

取证优先的需求探索与独立评审：从范围确认，到有界修复复审和快照核对后的交接。

### 新增

- 统一 Task／最终集成 Reviewer 模板，覆盖需求符合性、代码质量、架构与设计规范、运行
  正确性、安全与兼容性、测试有效性；报告包含独立性、内容／需求指纹、覆盖和稳定问题 ID／状态。
- 新增 `speckit.delivery.review-fix`、有界 Lane 修复复审槽位、最终 Gate 与后置变化时效核对。
- 增加真实植入缺陷、遗漏问题、过期任务关闭的合成评估，以及 Review／修复／Ralph 分发安装检查。
- 新增 `speckit.delivery.explore` 与随包分发的范围模板：支持代码／CodeGraph 调查、关联
  Issue／PR／Commit 取证、按场景检索 GitHub 开源参考，以及现状／候选改动目录树。
- Feature 在 Spec 前确认范围，并增强原有 Plan Gate 的文件／接口／测试展示；Bugfix
  的结构取证交给官方 Assessment 继续诊断，在原有 Gate 确认修复范围，不重复根因分析。
- 增加取证资源、Gate 顺序回归检查与干净项目命令／模板／Workflow 安装内容检查。
- 使用真实 Spec Kit 消费者和隔离假宿主，增加直接 Workflow 取证包／Gate 调度边界检查。

### 变更

- Ralph 关闭任务前要求 Quality、Standards、独立 Review 三门通过；预提交回执绑定快照，
  并核对结果提交内容等价。
- Doctor、Router、Handoff 拒绝过期、blocked、incomplete 或覆盖不足的评审；跨恢复／新 HEAD
  保留修复预算和问题 ID。Bugfix／Lightweight 保持比例原则，Gate 仍为引导式契约。
- Router 与直接 Workflow 对齐发现／取证／确认顺序，显式把证据交给 Spec、Assessment、
  Plan 和 Tasks。Lightweight 保持轻量，重大范围扩大需要重新确认。
- 直接 Workflow 要求 `delivery_run`，宿主退出前持久化固定取证包，传入确切路径和真实 Gate
  选择；仅上下文降级限于同会话 Router。
- Bugfix 复审续修通过随包的版本化记录适配器保留官方原始报告；Quality／Standards 与调用者
  要求原始内容／配置证据，不再仅凭 HEAD／路径复用。
- Delivery Catalog 和清单同步为八条命令，保留 0.1.2 的可选代码上下文命令，增加数量一致性校验。
- 直接 Bugfix 显式传入 `bug_slug`，由编排器核实评估映射，不突破官方 Assess 输出边界；
  续修补齐强制前后置 Hook 的实际执行、当前轮上下文与结果。

### 修复

- 直接 Workflow 在不同宿主进程间显式传递取证记录与真实批准选择，不再依赖丢失的会话上下文。
- HEAD／路径相同不能作为复用旧 Quality 证据的依据；必须核对原始检查输入／配置身份，否则重跑。
- Bugfix 复审续修不再重复调用会拒绝自动覆盖已有 `fix.md`／`test.md` 的官方命令；保留原始
  报告，新增当前轮证据，并保留全部四个适用的 Hook 阶段。
- 遗漏问题、覆盖不足、快照过期或未经接受的自审不能静默变成 pass；修复者不能自批修复。

### 升级注意事项

- 升级 Bundle，或同步更新受影响的 Extension 与三条交付 Workflow。旧复制命令／Workflow
  缺少新资源和关闭契约；升级后通过当前宿主运行 `speckit.delivery.doctor`。只更新薄 `$sd`
  门面不会更新底层组件。
- **直接 Workflow 的输入发生变化：**三条 Lane 都必须传入 `delivery_run`，使用唯一、安全的
  单段 Run 标识。Bugfix 另需单独指定规范化 `bug_slug`，全新运行的评估输出路径不得已存在。
  恢复时沿用相同标识，不能通过更换 ID 重置修复预算。

  ```bash
  specify workflow run feature-delivery --input delivery_run=audit-trail-01 --input spec="增加审计轨迹"
  specify workflow run bugfix-delivery --input delivery_run=retry-fix-01 --input bug_slug=duplicate-retry --input report="重试导致重复通知"
  specify workflow run lightweight-delivery --input delivery_run=docs-fix-01 --input change="修正文档标题"
  ```

- 直接 Workflow 在宿主退出前将记录保存到 `.specify/delivery/<delivery_run>/`；临时产物模式
  也需保留本地忽略文件以便恢复。Bugfix 不会仅因复审修复就强制完整 Feature Spec／Plan／Tasks。
- Ralph 关闭任务前必须同时通过当前快照的 Quality、Standards、独立 Review。旧 HEAD／路径
  回执不足以通过；修复槽位最多三次（或更低的配置上限），预算耗尽不代表阻断项获准忽略。
- CLI 最低要求不变：单独组件支持 Spec Kit `>=0.16.4`，Bundle 安装要求 `>=1.2.3`。

### 验证与限制

- 本地验证覆盖 23 项分发契约／变异测试、5 项使用真实 Spec Kit Command／Gate 与假宿主
  消费者的交接测试、4 项版本写入测试、链接／diff 检查，以及 OpenCode／Codex Skills 干净
  项目的 Bundle 安装。
- 隔离案例实际验证了同 HEAD 的过期 Hook 拒绝复用，以及 Bugfix 红→绿修复、四个强制 Hook、
  原始报告不变和不兼容 Hook 的阻断。修复仍正确保留为待独立复审，不自批通过。
- 上述不代表完整业务／Provider 集成或自主交付端到端验证。`0.1.x` 仍是引导式提示与 Workflow
  契约，并非新增机器强制执行的语义状态引擎，也不承诺所有宿主的执行能力等价。

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
