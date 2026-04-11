# 配置模型

本文档定义 `feishu-am-workbench` 在“多人共用 skill、各自使用自己的飞书环境”场景下的配置设计。

核心原则：

- 共用的是 `skill`
- 私有的是 `workspace config`
- 任何真实飞书资源都不应硬编码进通用 skill 仓库
- 稳定的是“语义边界和安全边界”，不是某一版字段名或某一套 runtime 实现

---

## 一、为什么需要配置层

当前这套 skill 是围绕你的个人环境逐步打磨出来的，所以仓库里已经沉淀了很多“当前 live 环境的快照”：

- Base token
- table id
- folder token
- tasklist guid
- 字段名和字段结构
- 任务清单自定义字段

这些信息对你自己是有效的，但如果以后要给其他 AM 用，就不能继续把这些内容当作通用真相。

所以后续必须拆成三层：

- `Core Skill`
- `User Workspace Config`
- `Safe Runtime Guardrails`

---

## 二、三层结构

### 1. Core Skill

通用部分，应该对所有 AM 都成立：

- 客户经营工作流
- 事实分级
- 路由逻辑
- 客户档案唯一性
- 绝对日期规则
- 历史合同与当前合同分层
- Todo 去重和责任人要求
- schema 兼容与 no-write fallback

这层应该尽量不包含任何个人环境信息。

### 2. User Workspace Config

每个人自己的环境配置，例如：

- Base token
- 客户主数据表 id
- 合同清单表 id
- 行动计划表 id
- 客户关键人地图表 id
- 客户联系记录表 id
- 竞品表 / 竞品交锋表 id
- 客户档案目录 token
- 会议纪要目录 token
- Todo tasklist guid
- 主键字段名
- 受保护字段列表
- 常用策略字段
- 任务自定义字段映射

### 3. Safe Runtime Guardrails

运行时安全护栏，例如：

- live schema 校验
- live option 校验
- 环境一致性校验
- 写前预演
- 高风险字段确认
- drift 检测
- no-write fallback

---

## 三、配置应包含哪些内容

建议配置至少包括以下模块。

## 1. 环境标识

- `workspace_name`
- `owner_name`
- `tool_runtime`
  - codex / hermes / openclaw / other
- `locale`
- `timezone`

## 2. Base 资源映射

- `base_token`
- `tables.customer_master`
- `tables.contracts`
- `tables.action_plan`
- `tables.contact_map`
- `tables.contact_log`
- `tables.competitor_master`
- `tables.competitor_encounters`
- `tables.leads_pool`

## 3. 文档资源映射

- `folders.customer_archive`
- `folders.meeting_notes`

## 4. Task 资源映射

- `tasklist_guid`
- `custom_fields.customer`
- `custom_fields.priority`
- 各优先级 option 映射

## 5. 语义字段映射

例如：

- `customer_id_field`
- `archive_link_field`
- `last_contact_field`
- `next_action_field`
- `strategy_summary_field`

这里不要求所有人字段名完全一致，但必须能映射到同样的业务语义位。

## 6. 保护规则配置

- 主表禁止修改字段
- 主表谨慎修改字段
- 高风险字段
- 默认只读字段

## 7. 选项字段配置

只记录“需要特别治理”的字段，而不是记录全部 option：

- 严格枚举字段
- 可控扩展字段
- option 同义词归一规则

---

## 四、推荐的配置文件形式

建议后续采用：

- `config/template.yaml`
  - 对外公开的模板
- `config/example.yaml`
  - 脱敏示例
- `config/local.<owner>.yaml`
  - 每个人自己的本地私有配置，不进仓库

当前仓库已经补齐：

- [config/template.yaml](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/config/template.yaml)
  - 通用配置模板，包含 live schema preflight、语义字段位、严格枚举字段和 Todo 映射
- [config/example.yaml](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/config/example.yaml)
  - 脱敏示例，方便直接照着填本地私有配置
- [references/live-schema-preflight.md](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/references/live-schema-preflight.md)
  - 写前 preflight 的运行时契约，定义输入、解析顺序、漂移分类和输出结构
- [references/minimal-stable-core.md](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/references/minimal-stable-core.md)
  - 标记最小稳定内核、扩展面和变更策略，用来降低后续 skill 迭代返工

也就是说：

- 仓库里放模板和示例
- 真实 token、guid、目录、私有字段配置留在本地

---

## 五、什么不应该进入公开仓库

如果未来仓库公开，以下内容不应保留在公共版本里：

- 真实 Base token
- 真实 doc / folder token
- 真实 tasklist guid
- 真实客户名清单
- 真实联系人
- 真实合同金额和客户经营数据
- 任何能直接定位个人飞书环境的资源 id

仓库里可以保留：

- 模板
- 规则
- 脱敏示例
- 字段语义示例

---

## 六、配置与 skill 的关系

最终应该是：

- `skill` 决定怎么思考、怎么判断、怎么路由
- `config` 决定去哪张表、哪个字段、哪个目录、哪个任务清单
- `preflight contract` 决定写前必须证明什么才允许真正落盘

也就是：

- 逻辑不跟着人变
- 环境跟着人变

---

## 七、推荐演进顺序

1. 先把当前仓库里的真实环境信息逐步识别出来
2. 将“规则”和“个人环境”分离
3. 补模板配置
4. 落地 live schema preflight 契约
5. 再考虑给其他 AM 使用

如果不先做配置层，后续“给别人用”会变成复制一份你的个人 skill，而不是复用一个通用内核。
