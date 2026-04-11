# Status

本文档记录 `feishu-am-workbench` 当前阶段的实际实现状态，避免“部分完成但后面忘了”。

它和其他文档的分工是：

- [ROADMAP.md](/Users/liaoky/.codex/skills/feishu-am-workbench/ROADMAP.md)
  - 记录后续要做什么
- [CHANGELOG.md](/Users/liaoky/.codex/skills/feishu-am-workbench/CHANGELOG.md)
  - 记录已经改了什么
- [VALIDATION.md](/Users/liaoky/.codex/skills/feishu-am-workbench/VALIDATION.md)
  - 记录应该怎么验证
- `STATUS.md`
  - 记录“现在到底做到哪了、卡在哪、下一步是什么”

## 当前结论

当前仓库已经进入“底座可执行、但未完全收口”的阶段。

- Base: 已可 live 读取
- Todo: 已可 live 读取
- Docs / Drive folder: 已可 live 读取
- Meeting 场景: 还没正式接回主流程验证

## 模块状态

### 1. Runtime 底座

状态：`已实现第一版`

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

- 上层业务场景尚未系统接入这套底座

### 2. Live Resource 接入

状态：`已完成当前个人环境接入`

已完成：

- 当前个人环境真实入口已记录在 [references/live-resource-links.md](/Users/liaoky/.codex/skills/feishu-am-workbench/references/live-resource-links.md)
- runtime 已能从该文件解析：
  - Base token
  - `客户主数据` table id
  - customer archive folder
  - meeting-note folder
  - tasklist guid

当前限制：

- 目前只覆盖你当前个人环境
- 还没设计成更广义的资源发现层

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

状态：`已移出底座主实现`

已完成：

- 底座默认 gateway 已不再自动执行“客户背景恢复”
- `live_adapter.py` 中的默认业务查询实现已删除

当前限制：

- 当前 meeting notes 仍主要按文件名中的 `客户ID` 做匹配
- 还没补更强的文档筛选和相关性排序

### 5. Live Schema

状态：`已实现第一版，未完全收口`

已完成：

- [references/live-schema-preflight.md](/Users/liaoky/.codex/skills/feishu-am-workbench/references/live-schema-preflight.md) 契约已存在
- runtime 里已有：
  - [runtime/schema_preflight.py](/Users/liaoky/.codex/skills/feishu-am-workbench/runtime/schema_preflight.py)
  - [runtime/live_adapter.py](/Users/liaoky/.codex/skills/feishu-am-workbench/runtime/live_adapter.py)
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
- `live_adapter.py` 当前只保留飞书资源探测、客户解析、schema 读取等薄适配能力
- 已新增按 `客户ID` 查询 `客户联系记录`、`行动计划`、`合同清单` 的薄查询能力，用于替代批量读取后本地筛选
- 当前 semantic slot 仍只覆盖 3 张核心表，这是刻意保持最小语义面的结果，不是遗漏
### 7. Capability Diagnostic

状态：`已完成并可运行`

运行命令：

```bash
python3 -m runtime /Users/liaoky/.codex/skills/feishu-am-workbench
```

当前真实输出结论：

- `base_access`: `available`
- `docs_access`: `available`
- `task_access`: `available`

## 当前阻点

当前没有新的运行前权限阻点。

当前更偏实现层的待补项是：

- 会议纪要目录命中策略仍偏简单
- live schema 还没完全覆盖 Todo / write guard 的真实写回联调验证
- 上层业务场景还没正式接入这套底座做系统验证
- 多维表格扩表还没按统一接入模型推进到查询优化和写面，目前写面仍只覆盖 3 张核心表
- 新增表目前只完成 profile 层，尚未进入真实读写链路
- Base 查询目前仍有“先拉再本地筛”的实现，需要继续收口到精准查询优先

## 下一步

当前最自然的下一步是：

1. 把会议场景正式接回到底座做真实验证
2. 补更强的 meeting-note 命中和排序策略
3. 继续收口 live schema 的 Todo / write guard 相关真实联调验证
4. 把 Base 读取从“大批量读取后本地筛选”继续改成“精准查询优先”

## 更新时间

- 2026-04-11
