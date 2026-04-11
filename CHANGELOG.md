# 变更记录

这里记录 `feishu-am-workbench` 的重要变化。

使用轻量分类：

- `新增`：新能力
- `变更`：已有行为调整
- `修复`：问题修正
- `移除`：废弃能力

## [Unreleased]

## [0.2.6] - 2026-04-11

### 新增

- `evals/evals.json`
  - 首版自动化测试集，覆盖会前准备、会后更新、档案刷新三个高频场景
  - 每个场景包含预期输出说明和 4-6 条可验证断言
  - 对应 skill-creator 规范中要求的 eval 体系，可供后续 benchmark 迭代使用
- `references/INDEX.md`
  - 21 个 reference 文件的一句话说明 + "何时加载"快速索引
  - 解决 reference 文件多但无导航入口的问题

### 变更

- `SKILL.md` — description（frontmatter）
  - 补充中文触发词（飞书工作台、客户档案、会议纪要、行动计划等）
  - 补充典型用户表达示例（"帮我整理一下今天的会议"、"更新飞书行动计划" 等）
  - 与 skill-creator 规范要求的"稍微强势的触发描述"对齐
- `SKILL.md` — 新增 compatibility 字段
  - 声明 lark-cli 和 Python 3.10+ 依赖
- `SKILL.md` — 新增 Runtime Prerequisites 小节
  - 明确 runtime/ 模块的使用方式、诊断命令和 fallback 说明
- `SKILL.md` — Hard Rules 优化
  - 5 条关键规则补充了 "why" 解释，减少机械执行风险，提升意图理解
  - 涉及：客户解析、绝对日期、会议纪要冷记忆标准、客户档案叙事性、Todo 责任人
- `SKILL.md` — 参考文件区新增 INDEX.md 引用入口

## [0.2.5] - 2026-04-11

### 新增

- `STATUS.md`
  - 统一记录当前实现进度、live schema/runtime 状态、已知阻点和下一步
- `references/meeting-live-first-policy.md`
  - 固定会议纪要 / 逐字稿 / 会后总结场景的 live-first 执行门和 fallback 条件

### 变更

- `runtime/`
  - 已接入当前个人环境的 live Base 入口
  - 已支持 runtime diagnostics
  - 已打通 live customer resolution
  - `base_access` 已升级为验证实际依赖表存在，不再只验证 Base token 可达
  - `schema_preflight` 已补齐第一版类型兼容、guarded policy 和 live option 查询
  - `schema_preflight` 已补充更细的 drift 分类，包括 alias fallback、option synonym、required payload、Todo custom field 缺失、Todo owner 未解析
  - Todo preflight 已接入 live tasklist 校验，并要求 owner 命中当前 tasklist owner / members
  - Todo `客户` / `优先级` custom field 已接入当前 runtime source，其中 `优先级` 选项按已验证快照校验
  - `semantic_registry` 已升级为 `table profile + minimal semantic slots`
  - `客户关键人地图`、`合同清单`、`竞品基础信息表`、`竞品交锋记录` 已先纳入 table profile，不进入全字段镜像
  - Base 表入口已从 3 张表专有 hardcode 收口为统一 `table_targets`
  - gateway 默认主路径已移除上下文自动组装，不再替上层场景决定读哪些表
  - 已移除 `resource_catalog`、`query_guide` 和 `context_hydrator`，底座继续收缩到基础能力
  - 已移除 `live_adapter.py` 中默认业务查询策略、默认读面拼装和场景摘要逻辑
  - 为 `客户联系记录`、`行动计划`、`合同清单` 增加按 `客户ID` 的薄查询能力，优先走 `data-query`
- 新增 `references/base-integration-model.md`
  - 固定多维表格接入原则：live discover + minimal semantic contract + scenario routing
- `SKILL.md`、`meeting-context-recovery.md`、`task-patterns.md`、`feishu-workbench-gateway.md`
  - 会议场景默认改为先尝试 gateway Stage 1-3，再允许正式分析和 fallback

## [0.2.4] - 2026-04-10

### 新增

- `runtime/`
  - 新增 skill 内部底座执行层，包含：
    - `gateway`
    - `runtime_sources`
    - `resource_resolver`
    - `customer_resolver`
    - `context_hydrator`
    - `schema_preflight`
    - `write_guard`
    - 统一数据模型

### 变更

- `README.md`、`ARCHITECTURE.md` 接入 `runtime/`，明确底座已从纯文档设计进入本地执行层实现阶段

## [0.2.2] - 2026-04-10

### 变更

- `ROADMAP.md` 调整优先级：近期优先聚焦个人使用价值、分析质量和功能完善，通用化与配置层演进后置
- `README.md` 明确当前阶段主线是“先把个人高频使用价值做深”
- 新增 `VALIDATION.md` 和 `WORKFLOW.md`，用于真实场景验证和开发分支小步迭代
- 新增会议纪要场景规则：
  - `meeting-context-recovery`
  - `meeting-type-classification`
  - `meeting-note-doc-standard`
- `SKILL.md`、`task-patterns.md`、`update-routing.md`、`VALIDATION.md` 接入会议背景恢复、会议类型判定和写回上限
- 新增 `meeting-output-standard`
  - 统一会议场景最终输出结构
  - 要求上下文恢复来源可审计
  - 要求结构化摘要标题使用中文
  - 要求 `建议态更新` 由实际提取出的实体动态生成
- `README.md` 更新为当前唯一真源目录说明，不再保留旧项目路径和软链接安装说明

## [0.2.3] - 2026-04-10

### 新增

- `references/feishu-runtime-sources.md`
  - 固定当前版本真实飞书资源线索从哪里取，作为个人环境下的运行来源清单
- `references/feishu-workbench-gateway.md`
  - 定义 skill 内部统一的飞书工作台访问底座流程，供会议纪要、会后更新、会前准备等场景复用
- `ARCHITECTURE.md`
  - 固化当前阶段的整体架构，并明确飞书工作台底座是 skill 内部公共能力

### 变更

- `SKILL.md` 将 Feishu workbench gateway 提升为所有 Feishu 相关场景的统一入口
- `README.md` 和 `ARCHITECTURE.md` 接入 gateway / runtime sources，明确当前底座实现不以前置统一配置为前提

## [0.2.1] - 2026-04-10

### 新增

- `references/minimal-stable-core.md`
  - 固定最小稳定内核、扩展面、required minimum config 和 required minimum preflight outputs

### 变更

- `README.md`、`CONFIG-MODEL.md`、`ROADMAP.md` 接入 minimal stable core 边界，明确后续优化优先做增量扩展而不是改动核心契约

## [0.2.0] - 2026-04-10

### 新增

- `config/template.yaml`
  - 为 workspace 资源映射、语义字段位、严格枚举字段和 Todo custom fields 提供统一模板
- `config/example.yaml`
  - 提供脱敏示例，便于本地私有配置快速落地
- `references/live-schema-preflight.md`
  - 定义 live schema preflight 的输入、解析顺序、漂移分类、输出结构和写前 gate

### 变更

- `SKILL.md` 明确：如存在 workspace config，优先按 config 的 semantic slots 解析 live schema
- `README.md` 和 `CONFIG-MODEL.md` 接入 config / preflight contract，使“schema 兼容”从原则说明变成仓库内可复用契约

## [0.1.0] - 2026-04-10

### 新增

- `feishu-am-workbench` 的 GitHub 仓库初始化
- 面向飞书 AM 经营工作台的核心 skill 工作流
- 以下参考规则文件：
  - 字段快照
  - 路由与幂等规则
  - 事实分级
  - 金额与合同解释规则
  - 客户档案规则
  - Todo / 行动模式
  - 经营工作台信息架构
  - schema 兼容策略

### 变更

- 将 live schema discovery 和 live option discovery 提升为写回前的主机制
- 将静态字段映射降级为兼容性快照，而不是永久真相

### 修复

- 明确 Todo 规则：
  - 必须有责任人
  - 必须做语义去重
  - 同一经营主线优先用父任务 + 子任务组织
- 明确客户档案唯一性和会议纪要冷记忆规则
