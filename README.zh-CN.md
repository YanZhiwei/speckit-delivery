# Spec Kit Delivery

基于 [GitHub Spec Kit](https://github.com/github/spec-kit) 的证据驱动交付层。它保留 Spec Kit 的 Spec、Plan、Tasks 主线，并补充 ADR 决策记忆、Ralph 任务编排、实现收敛、简化审查、代码评审、文档同步、交付证据和稳定的 PR 交接。

> [!IMPORTANT]
> 当前为 `0.1.0` 初始分发骨架。引导式 Workflow 和命令契约可用于评估；Provider 级并行调度和完全机器化的语义分支属于后续里程碑。

[English](README.md)

## 为什么需要它

Spec Kit 已经提供了良好的 `specify → plan → tasks → implement` 主线，但通用工程交付还需要解决：

- 当前工作受哪些既有 ADR 约束？
- 新决策何时只是 Proposed，何时可以成为 Accepted？
- 多 Agent 如何基于 `tasks.md` 安全调度？
- 实现完成后是否真正收敛到 Spec？
- 是否引入了无消费者 API、重复状态或投机性扩展？
- 当前 outgoing diff 需要哪些可信验证？
- Spec 文件被忽略后，哪些长期背景仍然保留？

## 主流程

```text
上下文 → specify → clarify → plan → Proposed ADR → tasks → analyze
      → Ralph → converge → simplify → docs sync → review
      → Accepted ADR → evidence → PR handoff
```

按变更规模分为三条 Lane：

| Lane | 适用范围 |
| --- | --- |
| Feature | 新功能、跨模块修改、架构变化 |
| Bugfix | 可复现且范围明确的缺陷 |
| Lightweight | 文档、机械修改、极小的行为不变变更 |

## 本地开发安装

发布 Release 前，可从当前 checkout 安装：

```bash
specify extension add --dev ./extensions/decision
specify extension add --dev ./extensions/ralph
specify extension add --dev ./extensions/review
specify extension add --dev ./extensions/simplify
specify extension add --dev ./extensions/evidence
specify extension add --dev ./extensions/docs-sync
specify extension add --dev ./extensions/delivery

specify workflow add --dev ./workflows/feature-delivery/workflow.yml
```

运行 Feature Lane：

```bash
specify workflow run feature-delivery --input spec="描述需要交付的变更"
```

## 分发方式

仓库同时发布：

- 独立 Extension 压缩包
- 版本固定的 Extension/Workflow Catalog
- `speckit-delivery` Bundle

## 统一入口

在 Codex 中使用 `$sd <需求>` 启动 SDD 路由；将 skill 暴露为 slash 命令的
宿主可使用 `/sd`。`sd` 只是易记门面，实际流程由唯一的
`speckit-delivery` 路由维护；跨集成的稳定接口仍是 Bundle 与
`speckit.*` 命令。

需要 agent 原生入口时，把 `skills/` 下的两个目录一起复制到同一个 skills
发现根目录；目录关系见 [skills/README.md](skills/README.md)。
- 可选的 Agent-native 入口 Skill

Bundle 负责组合组件，不替代组件自己的版本、README 和测试。完整说明见 [分发文档](docs/distribution.md)。

## 长期记录

即使 `spec.md`、`plan.md`、`tasks.md` 被 gitignore，以下内容仍应持久化：

- Constitution：跨 Feature 的项目规则
- Issue：问题、范围和验收条件
- ADR：长期架构决策
- 代码、测试和文档：实际行为
- PR：最终变化、风险和验证证据

最终 ADR 和 PR 不应引用临时 Task ID、Review 轮次或被忽略的 Plan 章节。

## 当前状态

- `0.1.x`：命令契约、引导式 Workflow、Catalog 和发布结构
- `0.2.x`：机器可读状态和语义 Gate
- `0.3.x`：Ralph Provider 并行适配
- `1.0.0`：完成多 Integration 的干净项目安装验证

## License

[MIT](LICENSE)
