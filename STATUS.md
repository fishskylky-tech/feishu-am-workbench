# Status

本文档记录 `feishu-am-workbench` 当前阶段的实际实现状态，避免“部分完成但后面忘了”。

它和其他文档的分工是：

- [ROADMAP.md](./ROADMAP.md)
  - 记录后续要做什么
- [CHANGELOG.md](./CHANGELOG.md)
  - 记录已经改了什么
- [VALIDATION.md](./VALIDATION.md)
  - 记录应该怎么验证
- `STATUS.md`
  - 记录“现在到底做到哪了、卡在哪、下一步是什么”

## 当前结论

当前仓库的 v1.0 phases 1-11 已经全部收口并完成归档。当前不再存在主线 phase blocker，mainline capability、verification closure、safe-write validation、meeting write loop E2E 证据以及最后的 cleanup debt 都已经补齐到 milestone-grade。

- Base: 已可 live 读取
- Todo: 已可 live 读取
- Docs / Drive folder: 已可 live 读取
- Meeting 场景: 已完成真实 `gateway -> typed context recovery -> constrained fallback -> audit output` 验证
- 当前核心上下文恢复阶段状态: code review clean、`threats_open: 0`、validation verified、human UAT 4/4 passed
- 当前主线状态: v1.0 archived；剩余仅有 backlog 和下一轮 milestone 选择

## 模块状态

### 1. Runtime 底座

状态：`已实现第一版，并已接入 meeting 场景最小闭环`

已完成：

- `runtime/` 模块已建立
- `FeishuWorkbenchGateway.for_live_lark_cli(...)` 已可用
- 已有：
  - `resource resolver`
  - `customer resolver`
  - `schema preflight`
  - `write guard`
  - `diagnostics`

当前限制：

- 当前验证完成的是 meeting 场景最小闭环，不代表所有写回场景都已完成系统联调

### 2. Live Resource 接入

状态：`已完成当前个人环境接入，敏感值已外迁至环境变量`

已完成：

- 示例入口格式记录在 [references/live-resource-links.example.md](./references/live-resource-links.example.md)（使用占位值，不含真实 token）
- 真实资源配置通过 `FEISHU_AM_*` 环境变量注入；本地 `.env` 仅作为把这些值加载进进程环境的便利层（已加入 `.gitignore`）
- `runtime/env_loader.py` 在 runtime 入口启动时自动加载 `.env`，无需手动 export
- 加载优先级：进程级显式 env > `.env` 注入后的进程环境
- runtime 已能从私有环境变量解析：
  - Base token
  - `客户主数据` table id
  - customer archive folder
  - meeting-note folder
  - tasklist guid

当前限制：

- 目前只覆盖你当前个人环境
- 还没设计成更广义的资源发现层
- checked-in repo 文档已不再参与 live 资源 truth 判定；它们只保留说明和示例作用

### 3. Customer Resolution

状态：`已打通`

已完成：

- 可从 live Base `客户主数据` 读取并解析客户
- 已修复 `+record-list` 返回“字段数组 + 数据矩阵”时无法解析的问题

当前验证结果：

- `联合利华` 可解析为：
  - `C_002`
  - `联合利华（UFS）`

### 4. Context Hydration

状态：`核心上下文恢复阶段已关闭，meeting 场景核心恢复链路已稳定`

已完成：

- 底座默认 gateway 已不再自动执行“客户背景恢复”
- `runtime/live_adapter.py` 中的默认业务查询实现已删除
- `evals/meeting_output_bridge.py` 已在 gateway 之后执行 typed context recovery，并输出固定审计框架
- 当前最小恢复范围包括：
  - `客户主数据`
  - 最近 `客户联系记录`
  - 最近 `行动计划`
  - 客户档案链接
- 当显式链接缺失时，已支持受限 archive / meeting-note fallback 搜索，并把冲突或弱证据显式降级处理
- 当前核心上下文恢复阶段已完成 review、security、validation 与 human UAT 闭环

当前限制：

- 当前 `completed` 仍代表“最小必要上下文 + 受控 fallback 证据已恢复”，不是“已读取档案正文和完整历史线程”
- meeting-note fallback 仍是轻量候选发现，不是全文级相关性理解
- archive doc 正文读取和历史 meeting thread 深度关联仍后置到后续 phase

### 5. Live Schema

状态：`已实现第一版，未完全收口`

已完成：

- [references/live-schema-preflight.md](./references/live-schema-preflight.md) 契约已存在
- runtime 里已有：
  - [runtime/schema_preflight.py](./runtime/schema_preflight.py)
  - [runtime/live_adapter.py](./runtime/live_adapter.py)
- 已支持：
  - live field schema 读取
  - semantic slot -> live field 映射
  - 实际依赖表验证，不再只验证 Base token 可达
  - field type 检查
  - guarded / protected policy 阻断
  - live select option 查询
  - drift 分类细化：
    - `field_renamed_alias_resolved`
    - `option_synonym_resolved`
    - `required_field_missing`
    - `todo_custom_field_missing`
    - `owner_unresolved`
  - Todo preflight 第一版：
    - live tasklist 存在校验
    - owner 必须落在当前 tasklist owner / members 中
    - `客户` / `优先级` custom field guid 从当前 runtime source 读取
    - `优先级` 选项使用当前已验证快照
  - `safe / safe_with_drift / blocked`

还没完成：

- 在真实写回链路里的系统化验证
- 更多 drift case 回归样本
- Todo custom field 仍主要依赖当前已验证快照，不是从任务设置接口直接发现

### 5.1 Unified Todo Write Surface

状态：`已完成第一版收口`

已完成：

- `WriteCandidate` 已补最小公共写回字段：
  - `operation`
  - `match_basis`
  - `source_context`
  - `target_object`
- `WriteExecutionResult` 已作为统一写回结果模型落地
- `TodoWriteResult` 已对齐统一结果结构
- `TodoWriter` 已统一返回：
  - preflight 状态
  - guard 状态
  - dedupe 决策
  - executed operation
  - blocked reasons
  - remote object id / url
- Todo 已补最小 semantic dedupe 第一版
- `evals/meeting_output_bridge.py` 已能：
  - 生成最小 Todo candidate
  - 在确认后调用统一 Todo writer
  - 在输出中展示统一写回结果
- `python3 -m runtime meeting-write-loop` 已作为一等 operator surface 暴露 meeting write loop 的预览与 confirmed write 入口

当前限制：

- 当前 dedupe 仍是最小规则，只覆盖 customer + summary + time window 的近重复判断
- duplicate 命中后默认走 `update_existing` 自动 patch
- step-level duplicate 会优先返回 `create_subtask` 建议；仅当 `source_context.confirm_create_subtask=true` 时执行真实子任务创建
- meeting 入口当前只接了最小 Todo candidate 生成，不代表所有场景都已迁移

### 6. Base Integration Model

状态：`已落到 runtime 第一版`

已完成：

- `runtime/semantic_registry.py` 已从单纯字段槽位表升级为：
  - `table profiles`
  - `minimal semantic slots`
- `runtime/live_adapter.py` 已从 3 张核心表的专有硬编码入口，收口为统一 `table_targets`
- 当前已纳入 table profile 的表包括：
  - `客户主数据`
  - `客户联系记录`
  - `行动计划`
  - `客户关键人地图`
  - `合同清单`
  - `竞品基础信息表`
  - `竞品交锋记录`
- capability check 已改为从 table profile 读取“当前运行时必需表”，不再散落硬编码
- 已集成但未启用写面的表，会先以 `table_targets + profile` 形式存在，不强制进入 semantic write path

当前限制：

- 新增的 4 张表目前只是 profile 已建立，还没正式接入：
  - semantic write planning
  - live schema write path
- `客户关键人地图`、`合同清单` 当前只保留底层查询能力，不再默认拼进底座上下文
- `runtime/live_adapter.py` 当前只保留飞书资源探测、客户解析、schema 读取等薄适配能力
- 已新增按 `客户ID` 查询 `客户联系记录`、`行动计划`、`合同清单` 的薄查询能力，用于替代批量读取后本地筛选
- 当前 semantic slot 仍只覆盖 3 张核心表，这是刻意保持最小语义面的结果，不是遗漏
### 7. Capability Diagnostic

状态：`已完成并可运行`

运行命令：

```bash
python3 -m runtime .
```

当前真实输出结论：

- `base_access`: `available`
- `docs_access`: `available`
- `task_access`: `available`

当前口径：

- 诊断默认使用三档：`available / degraded / blocked`
- 输出会明确给出：结论、原因、下一步建议
- 当必需私有输入缺失时，应直接表现为 `blocked`，而不是回退到 repo 文档猜测资源

## 当前阻点

当前没有新的运行前权限阻点，也没有主线 phase 阻断项。

当前剩余事项主要是非阻断型：

- backlog Phase 999.1 仍是可选清理项，不属于 mainline milestone blocker
- 部分 live-only 验证仍需要真实 workspace 和个人权限环境，不适合直接固化为仓库内 fixture
- scene skill / bootstrap-admin / cache artifact 的运行时落地仍属于下一轮里程碑，而不是当前 v1.0 未完成项

## 下一步

当前最自然的下一步是：

1. 如果要继续清理 planning 历史，可选处理 backlog Phase 999.1
2. 如果要继续产品化，开启下一轮 milestone，把 scene skill 和 bootstrap/admin 从架构合同推进到可运行实现
3. 如果要进一步压缩人工验证面，继续把 live-only safe-write 和 fallback 检查转成自动化或半自动验证

## 更新时间

- 2026-04-16
