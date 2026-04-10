# feishu-am-workbench

一个面向个人 AM 场景的 Codex Skill，用于围绕飞书“经营工作平台”完成客户分析、会议准备、会后沉淀、经营判断和确认后回写。

这个仓库用于版本化管理 `feishu-am-workbench`，让 skill 的规则、字段映射、路由逻辑、兼容性策略和模板演进都能通过 GitHub 持续治理。

## 这个 skill 做什么

- 分析多种 AM 输入：
  - 本地客户资料目录
  - 会议纪要
  - 你的自然语言补充
  - 飞书 Base 中的经营工作台数据
  - 客户档案文档
  - 客户公开资讯
- 产出：
  - 客户经营分析和判断
  - 对飞书经营工作台的更新建议
  - 在你确认后的 Base / 文档 / Todo 回写
- 严格执行经营规则：
  - 每个客户只能有 1 份正式客户档案
  - 日期必须使用绝对时间
  - 客户主数据表是快照层，不是流水账
  - 长会议纪要进入“冷记忆”文档，不直接塞进 Base
  - Todo 必须有责任人，且要做语义去重
  - 写回前先做 live schema 检查，避免字段或选项漂移导致误写

## 仓库结构

- [SKILL.md](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/SKILL.md)
  - skill 主说明，定义工作流、写回边界和硬约束
- [agents/openai.yaml](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/agents/openai.yaml)
  - agent 展示信息和默认 prompt
- [references/](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/references)
  - 规则说明、字段快照、路由规则、兼容性策略等参考文件
- [CHANGELOG.md](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/CHANGELOG.md)
  - skill 的版本变更记录
- [VERSION](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/VERSION)
  - 当前 skill 版本
- [.github/](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/.github)
  - GitHub issue / PR 模板

## 当前设计原则

这套 skill 不假设飞书经营工作台的 schema 永远不变。

它采用的是：

- skill 内固化稳定的业务规则
- reference 文件保存当前 schema 快照和字段意图
- 真正写回前，实时读取 live schema 和 live options
- 字段改名时，优先 live 匹配，其次才是 alias fallback
- 一旦无法安全匹配，就停留在建议态，不做盲写

## 本地安装方式

如果这个仓库是后续唯一维护源，可以把它同步为 Codex 实际使用的 skill。

两种方式都可以：

1. 直接复制到 `~/.codex/skills/feishu-am-workbench`
2. 从本仓库创建软链接到 `~/.codex/skills/feishu-am-workbench`

推荐软链接方式，因为后续仓库变更会直接反映到本地生效版本。

示例：

```bash
mv ~/.codex/skills/feishu-am-workbench ~/.codex/skills/feishu-am-workbench.bak
ln -s "/Users/liaoky/Documents/工作/神策/feishu-am-workbench" ~/.codex/skills/feishu-am-workbench
```

## 迭代方式

建议所有有意义的 skill 变更都走 GitHub 管理，包括：

- Base 字段映射调整
- 经营规则变化
- 客户档案模板规则变化
- 写回路由和去重规则变化
- Todo 结构和字段使用变化
- schema 兼容策略变化

小范围字段快照刷新可以直接提交，但涉及经营逻辑和写回边界的变化，建议通过 PR 审核后再合并。

## 建议的 issue 类型

- `Skill change`
  - 用于提行为、模板、路由、规则、写回策略调整
- `Schema drift`
  - 用于提飞书 Base 字段改名、增删字段、选项变化、任务清单自定义字段变化

## 当前状态

这个仓库已经是 `feishu-am-workbench` 的 GitHub 管理源，且本地 Codex 使用的 skill 已经指向这份仓库。
