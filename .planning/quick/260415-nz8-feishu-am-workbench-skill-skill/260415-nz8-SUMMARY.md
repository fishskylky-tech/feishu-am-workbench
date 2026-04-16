# Quick Task 260415-nz8 Summary

**Date:** 2026-04-15
**Status:** Completed
**Type:** Refined architecture discussion

## Updated Framing

这次讨论的重点不应表述为“把当前 skill 再拆分一次”，而应表述为：

- 保留一个主 skill 作为入口和编排层
- 未来新增的经营场景以子 skill 方式扩展
- 场景 skill 在需要时调用专家子 agent
- 所有场景复用同一个飞书通用底座
- 后续再增加初始化安装/检查与本地缓存能力

这一定义比上一轮更准确，也更符合你希望长期演进的方向。

## Architecture Recommendation

### 1. 主 skill

主 skill 的职责应该是“薄协调层”，而不是“更大的总包 prompt”。

它负责：

- 识别输入属于哪个经营场景或工作流
- 判断是否需要 live context
- 决定调用哪个子 skill
- 决定是否需要额外专家 agent
- 串起推荐模式与确认后的写回模式

它不应该负责：

- 深业务分析细节
- 直接操作飞书字段
- 直接承担所有场景规则

这与 GSD 的薄 orchestrator 原则一致，也与 ADK/Anthropic 的“description 决定路由，instructions 按需加载”一致。

### 2. 多个场景子 skill

后续新增场景建议按“经营场景 / 工作流”建子 skill，而不是按底层表结构建子 skill。

第一类建议场景：

1. todo-capture-and-update
2. customer-recent-status
3. phase-goal-review
4. meeting-prep
5. post-meeting-synthesis
6. archive-refresh
7. weekly-or-monthly-account-review
8. public-update-synthesis

为什么按场景拆而不是按表拆：

- 用户的工作目标是“记待办”“查近期情况”“看目标达成情况”，不是“操作某张表”
- 场景往往横跨多个飞书对象，按表拆会把工作流切碎
- 当前仓库的 workbench-information-architecture 已明确把客户主数据、detail tables、archive、Todo 看成一个闭环，而不是独立孤岛

这与 Google ADK 的 file-based skill 设计很贴近：每个子 skill 应该是一个独立 folder，拥有自己的 SKILL.md、场景说明、输入输出约定和需要时才加载的 resources。

### 3. 按需专家子 agent

专家 agent 应该作为场景 skill 的内部协作组件，而不是全局常驻的平铺角色。

推荐角色：

1. context-hydrator
2. account-analyst
3. meeting-interpreter
4. archive-curator
5. action-planner
6. write-safety-checker
7. goal-auditor
8. schema-drift-checker

推荐调用方式：

- 主 skill 先路由到场景 skill
- 场景 skill 再判断是否需要这些专家 agent
- 专家 agent 只做自己那一段，结果交回场景 skill 汇总

这与 GSD 的研究/规划/执行/验证分工相似：重活由专门 agent 做，主入口不承担所有上下文。

### 4. 通用底座

底座应继续保留在 runtime + lark-cli 这层，职责是“通用访问与安全执行”。

底座包括：

- customer resolution
- context hydration primitives
- live resource probing
- schema preflight
- write guard
- unified writer surface
- capability diagnostics

底座不应该直接演变成“自动帮所有场景组装默认业务上下文”的智能层。当前 ARCHITECTURE.md、feishu-workbench-gateway.md 和 STATUS.md 对这个边界定义是对的，建议保留。

## Initialization And Install Capability

这是你这次补充里非常关键的一层，我建议把它作为“后续可选扩展 skill”，而不是塞进当前主 skill 主流程里。

### 它要解决什么

- 某个用户没有现成的飞书工作台结构
- 飞书中的表/字段/目录结构与当前仓库默认结构不同
- 需要初始化本地 config、语义映射、检查运行条件和 drift 风险

### 推荐形态

新增一个 workspace-bootstrap 子 skill 或 admin skill。

它负责：

1. 检查当前飞书资源是否存在
2. 检查最小 required workbench layers 是否齐备
3. 输出缺失项与兼容项
4. 生成或更新本地 workspace config
5. 生成缓存清单或 schema snapshot
6. 在结构偏差过大时停在 recommendation/setup mode

### 为什么不放进主 skill 主流程

- 主 skill 应该服务日常经营场景，而不是每次都承担环境诊断
- 初始化/安装属于低频但高影响任务，单独一个 skill 更符合 Anthropic skills 的 self-contained folder 范式
- 它的输出更像 setup report、compatibility report，而不是日常经营分析

## Local Cache / Ontology Capability

### 结论

可以做，而且应该做，但必须被定义为“加速层 / 兼容层 / 索引层”，而不是 live truth。

当前仓库其实已经有这方面雏形：

- actual-field-mapping.md 是 schema compatibility cache
- CONFIG-MODEL.md 已定义 workspace config 作为环境边界
- ROADMAP.md 已把 ontology 单列为 M3.5 候选主线
- schema-compatibility.md 和 live-schema-preflight.md 已明确 live schema 优先，cache 只能回退使用

### 建议拆成三类缓存

#### A. Workspace Schema Cache

保存：

- 表 id
- 字段 id
- 字段类型
- 常用 option snapshot

用途：

- 降低重复 schema 查询
- 提升 preflight 前的推理速度

规则：

- 只作 compatibility cache
- 写前仍以 live preflight 为准

#### B. Workspace Manifest / Index Cache

保存：

- canonical archive doc link
- meeting-note doc index
- 常用 folder / tasklist / custom field 映射
- 高频客户资源索引

用途：

- 降低“找文档 / 找目录 / 找任务字段”的重复 API 调用
- 为场景 skill 提供快速入口

规则：

- 可以定期刷新
- 一旦与 live probe 冲突，以 live 为准

#### C. Semantic / Ontology Cache

保存：

- 实体
- 关系
- 事件
- 经营状态
- 证据类型
- 写回落点映射

用途：

- 统一不同场景、不同输入源的语义口径
- 减少“同一事实在不同场景被不同方式解读”的漂移

规则：

- 这是 reasoning layer，不是 live resource truth
- 应该后置到当前 live-first 链路稳定后再正式推进

### 更新策略建议

1. 初始安装时生成第一次 cache/manifest
2. 场景运行时尽量优先读 cache 做路由推理
3. 只在真正写前或关键读取前做 live confirm
4. 当 drift 被发现时，更新本地 cache
5. 对 ontology 采用版本化更新，而不是每次运行自动重建

这和 GSD 的状态文件思路也一致：稳定状态可以沉淀成本地 artifact，但真正执行前仍要做当下验证。

## How The Three External Frameworks Map Here

### GSD

- 主 skill = orchestrator
- 子 skill = 可独立演进的工作流单元
- 专家 agent = 专门处理重推理或检查的执行者
- 本地 cache / manifest = 类似状态与上下文 artifact

最值得借鉴的是：

- 薄编排器
- 专家分工
- 显式 artifact
- 后置验证

### Google ADK Skills

- 主 skill 和各场景子 skill 都应该遵守 L1/L2/L3 progressive disclosure
- 每个子 skill 都应该是 file-based skill，而不是继续往单一 skill 里追加更多 references
- 初始化/安装 skill 后期甚至可以演进成 skill-factory 或 bootstrap skill，但前提是先有人审查与验证

最值得借鉴的是：

- description 是路由 API
- 场景 skill 独立目录化
- resources 按需加载
- 缓存和额外知识放到 L3，而不是塞回 L2

### Anthropic Skills

- 每个场景 skill 都应该做到 self-contained
- 每个 skill folder 只放该场景需要的说明、例子、资源
- admin/bootstrap skill 与日常经营 scene skills 分开

最值得借鉴的是：

- self-contained skill folder
- 专门 skill 做专门事
- 不把所有行为都堆到一个 SKILL.md 里

## Recommended Target Shape

建议目标结构如下：

1. main skill
   - route scene
   - enforce global rules
   - decide recommendation vs confirm-write path

2. scene skills
   - todo-capture-and-update
   - customer-recent-status
   - phase-goal-review
   - meeting-prep
   - post-meeting-synthesis
   - archive-refresh
   - weekly-or-monthly-account-review

3. foundation capability layer
   - runtime gateway
   - lark-cli adapters
   - resource/config/schema/write safety services

4. admin/setup layer
   - workspace-bootstrap
   - workspace-health-check
   - cache-refresh

5. local artifacts layer
   - workspace config
   - schema cache
   - manifest/index cache
   - semantic or ontology cache

## What To Keep / Adjust / Add

### Keep

- live-first as write truth
- recommendation-first safety model
- runtime thin-foundation boundary
- semantic slots and minimal stable core
- scene-driven rather than table-driven business logic

### Adjust

- 不要再把“新增经营场景”继续堆进根 skill
- 把 references 的组织方式逐步从主题文档改成场景 skill 资源包
- 在 roadmap 里把 bootstrap/cache/admin 能力单列成基础扩展线，而不是混在日常场景里

### Add

- 子 skill 目录规范
- scene-to-agent 触发矩阵
- workspace bootstrap / install design
- cache / manifest / ontology 的分层和更新策略

## Final Assessment

你的设想是成立的，而且和当前仓库已有方向并不冲突。

更准确的落地方向是：

- 主 skill 负责“编排”
- 子 skill 负责“场景”
- 专家 agent 负责“重推理或检查”
- runtime 底座负责“飞书能力与安全”
- bootstrap 与 cache 负责“可安装、可兼容、可扩展”

这样后续扩的不是一个越来越长的 prompt，而是一组可增长的经营工作流能力包。