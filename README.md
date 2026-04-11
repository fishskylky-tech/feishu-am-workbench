# feishu-am-workbench

一个面向个人 AM 场景的 Codex Skill，用于围绕飞书“经营工作平台”完成客户分析、会议准备、会后沉淀、经营判断和确认后回写。

这个仓库用于版本化管理 `feishu-am-workbench`，让 skill 的规则、字段映射、路由逻辑、兼容性策略和模板演进都能通过 GitHub 持续治理。

当前阶段的主线不是“先做成通用产品”，而是优先把这套 skill 打磨成对你个人高频 AM 工作真正有用的能力层；配置抽离和通用化继续保留，但排在后面。

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

- [SKILL.md](./SKILL.md)
  - skill 主说明，定义工作流、写回边界和硬约束
- [ARCHITECTURE.md](./ARCHITECTURE.md)
  - 当前架构分层、gateway 位置和 runtime 边界
- [agents/openai.yaml](./agents/openai.yaml)
  - agent 展示信息和默认 prompt
- [references/](./references)
  - 规则说明、字段快照、路由规则、兼容性策略等参考文件
- [CHANGELOG.md](./CHANGELOG.md)
  - skill 的版本变更记录
- [VERSION](./VERSION)
  - 当前 skill 版本
- [config/](./config)
  - workspace config 模板和脱敏示例，用来承接 live schema 兼容落地
- [ROADMAP.md](./ROADMAP.md)
  - skill 的中长期演进路线图
- [CONFIG-MODEL.md](./CONFIG-MODEL.md)
  - 通用 skill 与个人私有飞书环境之间的配置分层设计
- [SECURITY-MODEL.md](./SECURITY-MODEL.md)
  - skill 公开或给其他人使用时的安全设计
- [VALIDATION.md](./VALIDATION.md)
  - 当前版本的真实场景回归检查清单
- [STATUS.md](./STATUS.md)
  - 当前实现进度、阻点和下一步，避免部分完成状态丢失
- [WORKFLOW.md](./WORKFLOW.md)
  - 开发分支迭代和合并节奏说明
- [runtime/](./runtime)
  - skill 内部底座执行层，包含 gateway、resolver、hydrator、preflight、write guard 的本地模块
  - 当前已支持通过 `lark-cli` 产出 live capability report，并返回 resource catalog / query guide，告诉上层有哪些资源可查、优先用什么工具查
- [references/meeting-context-recovery.md](./references/meeting-context-recovery.md)
  - 会议纪要场景下的上下文恢复流程
- [references/meeting-type-classification.md](./references/meeting-type-classification.md)
  - 会议类型分类和不同类型对应的写回上限
- [references/meeting-note-doc-standard.md](./references/meeting-note-doc-standard.md)
  - 结构化会议纪要文档标准、保真边界和 AI 提示语
- [references/meeting-output-standard.md](./references/meeting-output-standard.md)
  - 会议纪要最终输出结构、中文标题规范和动态建议态更新规则
- [references/feishu-runtime-sources.md](./references/feishu-runtime-sources.md)
  - 当前个人环境下飞书资源线索从哪里取
- [references/live-resource-links.md](./references/live-resource-links.md)
  - 当前个人环境的真实飞书入口 URL，供 runtime 直接解析 Base / folder / tasklist 入口
- [references/feishu-workbench-gateway.md](./references/feishu-workbench-gateway.md)
  - skill 内部统一的飞书工作台访问底座
- [references/base-integration-model.md](./references/base-integration-model.md)
  - 多维表格接入模型：只维护最小语义面，不做全字段镜像
- [references/minimal-stable-core.md](./references/minimal-stable-core.md)
  - 定义哪些是后续优化时不应轻易改动的最小稳定内核
- [.github/](./.github)
  - GitHub issue / PR 模板

## 当前设计原则

这套 skill 不假设飞书经营工作台的 schema 永远不变。

它采用的是：

- skill 内固化稳定的业务规则
- config 内定义每个 workspace 的资源映射、语义字段位和枚举治理
- reference 文件保存当前 schema 快照和字段意图
- 真正写回前，实时读取 live schema 和 live options
- 写回前按照 live schema preflight contract 输出可审计的 drift / block 结果
- 字段改名时，优先 live 匹配，其次才是 alias fallback
- 一旦无法安全匹配，就停留在建议态，不做盲写
- 优先保持 minimal stable core 稳定，把 runtime 细节放在扩展层演进
- 当前已补一层本地 `runtime/` 骨架，用来承接飞书工作台底座的执行层
- 当前多维表格接入已引入 `table profile` 模型：
  - profile 可以先纳入表级角色和约束
  - semantic slots 只在场景真正需要时再补

## 本地安装方式

当前真源目录就是：

```bash
~/.codex/skills/feishu-am-workbench
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

这个仓库已经是 `feishu-am-workbench` 的唯一真源，且本地 Codex 直接从这个目录加载。
