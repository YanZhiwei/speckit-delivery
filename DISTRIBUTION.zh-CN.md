# 分发说明

## 发布单元

每个 Extension 打包为根目录包含 `extension.yml` 的压缩包；Workflow 是固定版本的
YAML；Bundle 在 Catalog 引用全部解析后构建。

```text
decision  ralph  review  simplify  evidence  quality  docs-sync  delivery
                         + feature / bugfix / lightweight Workflow
                         + speckit-delivery Bundle
```

Catalog URL 必须指向与发布版本相同的 Tag，发布不能依赖可变的 `main` 内容。

## 本地验证

在干净的临时 Spec Kit 项目中安装所有本地 Extension 和三个 Workflow，然后执行：

```bash
specify bundle validate --path /path/to/speckit-delivery/bundle
specify bundle build --path /path/to/speckit-delivery/bundle --output ./dist
python scripts/check_links.py
```

发布前还要在第二个干净项目中验证 Catalog 安装。只有 Manifest、Catalog、压缩包根
布局、README 命令和版本完全一致时，才能认为可发布。

## README 归属

根目录 README 负责产品价值、快速开始、支持宿主和状态；根目录双语参考文档负责
长期说明；Extension README 负责命令安装、输出、配置和安全；Catalog 与 Manifest
负责精确的机器可读版本。
