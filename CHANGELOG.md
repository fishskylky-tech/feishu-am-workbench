# 变更记录

这里记录 `feishu-am-workbench` 的重要变化。

使用轻量分类：

- `新增`：新能力
- `变更`：已有行为调整
- `修复`：问题修正
- `移除`：废弃能力

## [Unreleased]

### 新增

- `SKILL.md` — frontmatter 元数据补全
  - 新增 `version: 0.2.11`（与 VERSION 文件同步）
  - 新增 `author: fishskylky-tech`
  - 新增 `tags: [feishu, account-management, am-workflow, chinese, crm, pipeline]`
  - 新增 `license: MIT`
  - 新增 `repository: https://github.com/fishskylky-tech/feishu-am-workbench`
  - 新增 `load_strategy: progressive`
  - 新增 `tier` 说明 L1/L2/L3 边界
  - 新增 `triggers`：关键词、模式和文件类型
- `runtime/models.py`
  - 为统一落盘通道补充 `WriteCandidate` 公共字段：`operation`、`match_basis`、`source_context`、`target_object`
  - 新增 `WriteExecutionResult` 统一写回结果模型
- `evals/meeting_output_bridge.py`
  - 新增最小 Todo candidate 生成与 confirmed write 调用入口
  - 输出中可展示统一写回结果摘要

### 变更

- `runtime/todo_writer.py`
  - 从 Todo 专用返回结构收口到统一写回结果语义
  - 增加第一版 minimal semantic dedupe，支持 `create_new` / `update_existing` / `create_subtask` / `no_write` 决策
  - duplicate 命中后默认走 `update_existing` 自动 patch
  - `create_subtask` 默认 recommendation-only，显式确认（`confirm_create_subtask=true`）后执行真实子任务创建
- `evals/meeting_output_bridge.py`
  - 增加“相关会议纪要候选”命中与排序最小层（基于客户联系记录标题/日期/链接）
- `tests/test_runtime_smoke.py`、`tests/test_meeting_output_bridge.py`
  - 新增 dedupe 中文变体、create_subtask 可选执行、meeting-note 候选排序回归用例
- `ARCHITECTURE.md`、`references/feishu-workbench-gateway.md`、`references/task-patterns.md`
  - 明确“场景层产出 write candidate，底座统一执行 writer”的分层边界
- `STATUS.md`、`VALIDATION.md`
  - 新增 unified Todo writer 的状态和验证口径

## [0.2.11] - 2026-04-11

### 新增

- `evals/runner.py`
  - 新增最小可执行 eval runner，用结构化断言复核真实会议输出
- `evals/meeting_output_bridge.py`
  - 新增 meeting output bridge，支持 gateway 结果承接、最小 Stage 3 context recovery 和 CLI 生成待检输出
- `tests/test_eval_runner.py`、`tests/test_meeting_output_bridge.py`、`tests/test_validation_assets.py`
  - 补齐 runner、bridge 和验证资产的回归测试
- `validation-reports/2026-04-11-multi-case-skill-validation.md`
  - 统一沉淀 3 个真实案例的 baseline / green / regression 结论

### 变更

- `VALIDATION.md`
  - 从单案例回归清单升级为多案例验证协议，并将 live-first 设为会议类案例的强制前置条件
- `evals/evals.json`
  - 收口为 3 个真实案例的结构化 eval 资产，并与 runner 断言协议对齐
- `SKILL.md`
  - 压缩高频加载区重复表达，保留 live-first、no-write、absolute-date、owner-required 等核心规则
- `ROADMAP.md`
  - 明确将 archive doc 正文读取、历史 meeting-note docs 定向读取和 ontology 设计后置到 roadmap
- `STATUS.md`
  - 更新为 meeting 场景最小 `live-first` 闭环已验证完成，并明确当前 `completed` 仅代表最小 live context recovered

### 修复

- 统一 `VERSION`、`CHANGELOG.md`、`evals/evals.json` 与验证报告的版本口径
- 清理分支收尾阶段的状态漂移，移除“meeting 场景尚未正式验证”的过时描述

## [0.2.10] - 2026-04-11

### 新增

- `evals/meeting_output_bridge.py`
  - 新增 Stage 3 最小 context recovery：基于已解析 `客户ID` 读取 `客户联系记录`、`行动计划` 和客户档案链接
  - 当最小读取集齐全时，bridge 现在可输出 `上下文恢复状态: completed`
  - 输出中新增 `关键补充背景` 和 `未找到但应存在的资料`

### 变更

- `tests/test_meeting_output_bridge.py`
  - 增加 Stage 3 context recovery 回归测试
  - 校验最小 Base 上下文恢复可将 meeting 场景从 `partial` 推进到 `completed`
- `validation-reports/2026-04-11-multi-case-skill-validation.md`
  - 更新为真实 live-first Stage 1/2/3 最小闭环已验证通过
- `VALIDATION.md`
  - 执行层说明更新为：bridge 已可读取最小 live context，而不只是承接 gateway 结果

## [0.2.9] - 2026-04-11

### 新增

- `evals/meeting_output_bridge.py`
  - 新增 `run_gateway_and_build_meeting_output(...)`，可先执行 gateway，再把真实 `GatewayResult` 接进 bridge 输出
  - `--run-gateway` CLI 模式已可直接使用，不再要求手工传 `resource-status`、`customer-status`、`context-status`

### 变更

- `tests/test_meeting_output_bridge.py`
  - 增加 gateway 集成回归测试
  - 覆盖 resolved customer -> `partial`、missing customer -> `context-limited`、以及 `--run-gateway` CLI 路径
- `VALIDATION.md`
  - 执行层说明从“静态 bridge”升级为“可调用 gateway 的 bridge”
- `validation-reports/2026-04-11-multi-case-skill-validation.md`
  - 补充当前 bridge 已能接收真实 gateway 结果，但 live gateway 全链路仍待实测

## [0.2.8] - 2026-04-11

### 新增

- `evals/meeting_output_bridge.py`
  - 新增最小 meeting output bridge，负责把 transcript、gateway 结果和 fallback / used-source 证据拼成 runner 可检查的结构化输出
  - 提供轻量 CLI，便于用真实会议文件快速生成待检输出文本
- `tests/test_meeting_output_bridge.py`
  - 为 3 个真实案例增加 bridge 回归测试
  - 覆盖 resolved live-first、显式 fallback、以及 CLI 输出可被 runner 接受的路径

### 变更

- `VALIDATION.md`
  - 执行层新增 meeting output bridge，明确“真实会议输出接 runner”的最小实现路径
- `tests/test_validation_assets.py`
  - 版本更新到 `0.2.8`
  - 增加对 meeting output bridge 存在性的验证
- `SKILL.md`
  - 继续压缩高频加载区的重复表达，保持 live-first / no-write / absolute-date / owner-required 规则醒目

## [0.2.7] - 2026-04-11

### 新增

- `evals/runner.py`
  - 新增最小 eval runner，可读取案例、接收 agent 输出文本，并逐条执行断言
  - 当前支持 `contains_all`、`contains_any`、`not_contains_any`、`live_first_gate` 四类断言
- `tests/test_eval_runner.py`
  - 为最小 runner 增加回归测试
  - 覆盖联合利华 live-first 正例、缺少 live-first 证据的失败样例、显式 fallback 的通过样例

### 变更

- `evals/evals.json`
  - 版本更新到 `0.2.7`
  - 为 3 个真实案例补充 machine-readable 断言
  - 新增 live-first gate 断言，要求输出显式记录 gateway 尝试、客户解析、上下文状态和飞书资料 / fallback 原因
  - 移除本轮范围之外的 `scene type` 断言，避免把已搁置的 P2 又做回来
- `VALIDATION.md`
  - 增加 live-first 强制前置验证协议
  - 明确当前验证资产由文档层、数据层和最小 runner 三层组成
- `SKILL.md`
  - 做一轮高频加载成本压缩，减少重复说明，不改变核心规则语义
- `validation-reports/2026-04-11-multi-case-skill-validation.md`
  - 更新为 P1 / P3 方向的统一结论
  - 区分“runner 已落地”和“真实 live-first 全链路仍待业务场景实测”

## [0.2.6] - 2026-04-11

### 新增

- `evals/evals.json`
  - 收口为 3 个真实案例的结构化 eval 资产：联合利华、永和大王、达美乐
  - 每个案例包含真实文件路径、预期行为说明和可复核断言
  - 当前版本用于可重复执行的人工复核协议，不再把它表述为已落地的自动化 runner
- `references/INDEX.md`
  - 21 个 reference 文件的一句话说明 + "何时加载"快速索引
  - 解决 reference 文件多但无导航入口的问题
- `validation-reports/2026-04-11-multi-case-skill-validation.md`
  - 统一记录 3 个真实案例的 baseline / current-branch / regression 结论
  - 给出按 P1 / P2 / P3 排序的修改建议

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
- `VALIDATION.md`
  - 从第一轮单案例检查清单升级为多案例验证协议
  - 明确 `RED / baseline`、`GREEN / current-branch`、`REFACTOR / regression` 的执行方式

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
