<!--
Delivery 扩展的中文兜底 PR 模板。目标项目可通过 delivery-config.yml 的
pull_request_template 或自己的 .github/pull_request_template.md 覆盖本模板。
保持 `Part of #` / `Closes #` 为英文，GitHub 依赖这些关键字关联和关闭 Issue。
-->

## 摘要

## 动机

Part of #<issue> for a lower slice; Closes #<issue> only on the release slice or final rollup.

## Slice / Stack

<!-- 适用于切片交付；单 PR 可删除本节。低层使用 "Part of #"，
     只有 release slice 或 rollup 使用 "Closes #"。 -->
- Slice 与目标：
- Base 分支：
- 依赖：
- 合并顺序 / 方式：
- 不包含在本层：
- 回滚：

## Rollup

<!-- 适用于 integration -> target 的最终汇总；单 Slice 可删除。 -->
| Slice | PR | Review |
| --- | --- | --- |
|  |  |  |

- 聚合 CI / Review 证据：
- 最终合并方式：merge commit
- 整体功能回滚：

## 变更类型

- [ ] 新功能
- [ ] Bugfix
- [ ] 重构或简化
- [ ] 文档或治理
- [ ] 发布准备

## 当前设计（变更前）

- 入口或组件：
- 归属与依赖方向：
- 当前约束与不变量：

## 变更内容

| 位置 | 变更 | 原因 |
| --- | --- | --- |
|  |  |  |

## 影响

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API、命令、配置 |  |  |
| 持久化或迁移 |  |  |
| 兼容性与升级路径 |  |  |
| 安全与权限 |  |  |
| 性能与资源 |  |  |
| 依赖与供应链 |  |  |

## 设计

<!-- 可选。优先使用 Mermaid；也可以链接已提交的 SVG，不要粘贴 HTML。
     没有持久结构变化时写 "N/A" 并说明原因。 -->

```mermaid
flowchart LR
```

## 架构决策

- [ ] 已链接相关 ADR，并与 HEAD 的实现一致。
- [ ] 没有架构决策变化。

## 行为与验收

| 需求 | 结果 | 证据 |
| --- | --- | --- |
|  |  |  |

## 验证

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 构建 |  |  |
| 测试 |  |  |
| 规范与 Spec 审查 |  |  |
| ADR 一致性 |  |  |
| 变更范围的简化检查 |  |  |

## 文档

- [ ] 源文档已更新。
- [ ] 生成文档已同步。
- [ ] 不需要文档变更。

## 回滚

## AI 辅助

- [ ] 未使用 AI 辅助。
- [ ] 使用了 AI 辅助，且每一行变更都已审阅和验证。

## 评审说明

## 检查清单

- [ ] 验收条件已覆盖。
- [ ] 阻断性评审问题已解决。
- [ ] ADR 与 HEAD 的实现一致。
- [ ] 已附相关验证证据。
- [ ] 外发 diff 与已审阅范围一致。
