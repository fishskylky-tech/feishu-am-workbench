# EVALUATION_REPORT — feishu-am-workbench → ClientOS

**评估时间：** 2026-04-28  
**评估人：** Copilot（高级软件架构师角色）  
**评估基准：** PRD.md v0.1 + EVALUATION_TASK.md

---

## 1. Executive Summary

`feishu-am-workbench` 是一个由 Codex Skill 包装的实际业务应用，已在 ~8 天内从 v1.0 迭代到 v1.3.1。核心业务逻辑（7 个场景、schema preflight、expert 系统）已实现且测试覆盖基本到位，可认为是验证可行性的"概念证明"。  

然而，与 PRD 所描述的 ClientOS 目标相比，存在三个根本性结构障碍：**没有 MCP Server**（整体产品形态不匹配）、**没有 Platform Adapter 抽象**（所有 I/O 硬绑定飞书/lark-cli）、**没有本地知识库层**（无 Kuzu、无 ChromaDB）。这三个缺口不是可以修补的细节——它们影响整个架构骨架。

现有代码中值得保留的是：场景业务逻辑模式（context recovery、write guard、expert cards 设计思路）、数据模型概念（客户、联系记录、行动计划、档案）、以及测试框架。直接 reuse 的代码比例估计在 30-40%，剩余需要重写或丢弃。

---

## 2. Reuse Map

### 2.1 目录级别

| 路径 | 用途说明 | ClientOS 价值 | 复用结论 |
|---|---|---|---|
| `runtime/models.py` | 数据模型（WriteCandidate、EvidenceContainer 等） | 核心数据概念可沿用，但字段高度 Feishu 耦合 | **REFACTOR** |
| `runtime/gateway.py` | Feishu 写入编排入口 | 逻辑结构有价值，但整体绑定 Feishu | **REFACTOR** |
| `runtime/scene_runtime.py` | 7 个场景实现（1916 行） | 场景业务逻辑有价值，但直接调用 LarkCli | **REFACTOR** |
| `runtime/live_adapter.py` | lark-cli 的所有 Feishu 读写适配（1151 行） | 可成为 FeishuAdapter 实现，但当前无接口契约 | **REFACTOR** |
| `runtime/lark_cli.py` | lark-cli 二进制 subprocess 封装（101 行） | 底层平台传输层，对应 FeishuAdapter 内部 | **REFACTOR** |
| `runtime/schema_preflight.py` | Schema 合法性检查 | 逻辑可用，但需对接新 PlatformAdapter 接口 | **REFACTOR** |
| `runtime/write_guard.py` | 写操作最终安全门 | 逻辑完整，接口干净，可基本直接复用 | **REUSE** |
| `runtime/todo_writer.py` | Feishu Todo 写入（599 行） | 完全 Feishu 特定，迁移到 FeishuAdapter | **REFACTOR** |
| `runtime/semantic_registry.py` | 硬编码 Schema（中文字段名） | 概念保留，具体字段需变为动态 | **REFACTOR** |
| `runtime/expert_card_loader.py` | Expert card YAML 加载 | 设计思路好，可复用 | **REUSE** |
| `runtime/expert_agent_invoker.py` | 专家调用编排、Circuit Breaker | Circuit Breaker、AggregatedFailureResult 可复用 | **REUSE** |
| `runtime/expert_analysis_helper.py` | EvidenceContainer、EvidenceSource | 数据模型概念良好，可直接复用 | **REUSE** |
| `runtime/default_llm_adapter.py` | OpenAI/Anthropic API 封装 | 完整可复用 | **REUSE** |
| `runtime/diagnostics.py` | Capability check | 逻辑可用，需对接新 Adapter 接口 | **REFACTOR** |
| `runtime/customer_resolver.py` | 客户 ID 解析 | 核心业务逻辑，需对接新数据层 | **REFACTOR** |
| `runtime/scene_registry.py` | 场景注册表 | 结构简洁，可直接复用 | **REUSE** |
| `runtime/confirmation_checklist.py` | 确认清单渲染 | 小工具，可复用 | **REUSE** |
| `scenes/` | 每个场景的 expert-cards.yaml | YAML 结构可复用 | **REUSE** |
| `agents/` | 专家 MD 文件 + agent-registry.yaml | 可直接复用，MD 内容有价值 | **REUSE** |
| `references/` | 21 个参考文档 | 业务规则文档，部分仍有效 | **REFACTOR** |
| `tests/` | 399 个测试（342 pass, 57 skip） | 测试框架和 mock 模式可沿用 | **REFACTOR** |
| `evals/` | Eval runner + evals.json | 可直接复用 eval 框架 | **REUSE** |
| `SKILL.md` | Codex Skill 入口定义 | 产品形态已变，但场景列表可参考 | **DISCARD** |
| `config/` | example.yaml + template.yaml | 需完全重写为 ClientOS config.yaml 格式 | **DISCARD** |
| `.env.example` | 环境变量示例 | 飞书特定，需重写 | **DISCARD** |
| `docs/` | 内部文档 | 视内容决定，不影响代码 | **DISCARD** |

### 2.2 文件级别重点

| 文件 | 结论 | 理由 |
|---|---|---|
| `runtime/write_guard.py` | **REUSE** | 逻辑完全可平台无关 |
| `runtime/expert_agent_invoker.py` | **REUSE** | Circuit Breaker + 聚合失败处理是通用能力 |
| `runtime/expert_analysis_helper.py` | **REUSE** | EvidenceContainer 数据模型通用 |
| `runtime/default_llm_adapter.py` | **REUSE** | LLM 调用层与平台无关 |
| `runtime/lark_cli.py` | **REFACTOR** | 成为 FeishuAdapter 内部实现的一部分 |
| `runtime/live_adapter.py` | **REFACTOR** | 大量可用逻辑，但需加 PlatformAdapter 抽象 |
| `runtime/semantic_registry.py` | **REFACTOR** | 动态 schema 替换硬编码 |
| `runtime/scene_runtime.py` | **REFACTOR** | 太大（1916 行），场景逻辑需拆分 |

---

## 3. Stability Assessment（写操作路径分析）

### 3.1 写操作路径全景

系统有 5 条写路径：

| 写路径 | 调用链 | Schema 验证 | 错误处理 | 已知风险 |
|---|---|---|---|---|
| **Feishu Base 记录写入** | `SceneRequest` → `FeishuWorkbenchGateway.run()` → `SchemaPreflightRunner` → `WriteGuard` → `lark-cli base +record-create/update` | ✅ preflight + guard | ✅ LarkCliCommandError 捕获 | lark-cli 不可用时静默失败；无事务支持，多步写入部分失败无法回滚 |
| **Feishu 文档写入（档案/会议记录）** | `SceneResult.payload` → LLM 提示执行 → `lark-cli drive` | ❌ 无 schema 验证 | ⚠️ 依赖 LLM 自行判断 | 这是最危险的路径：文档写入完全由 LLM prompt 驱动，无代码层验证 |
| **Todo 写入** | `TodoWriter.create()` → preflight → guard → `lark-cli task` | ✅ preflight | ✅ LarkCliCommandError | 去重逻辑依赖语义判断，存在误判风险 |
| **客户主数据更新** | `WriteGuard.evaluate()` 检查 allowlist → lark-cli | ✅ allowlist 防护 | ✅ | `next_action_summary`、`last_contact_at` 可直接写；strategy 字段走 recommendation-only |
| **Feishu 表详情行（行动计划/联系记录）** | 同 Base 记录写入 | ✅ preflight | ✅ | 无事务；多行写入失败后无回滚 |

### 3.2 关键漏洞

**最高风险：文档写入路径**  
- 客户档案文档和会议记录文档的写入，不经过代码层的 schema validation
- 写操作事实上由 LLM prompt 编排，靠 SKILL.md 里的规则约束
- PRD 明确指出这是前身项目的根本性问题（"Skill/prompt 文档约束 LLM 写操作，导致结构化写入不稳定"）
- 这个漏洞在当前代码里没有修复，只是在 Base 表写入层面加了 preflight，文档层仍然是 prompt-driven

**中等风险：无事务支持**  
- `write_order`（先写 Base 表，再写文档，最后写 Todo）是靠代码顺序保证的
- 如果步骤 2 失败，步骤 1 的写入已生效，没有回滚机制
- 代码中有"report completed writes and remaining failures"的设计，但没有补偿逻辑

**低风险：lark-cli 二进制依赖**  
- `lark-cli` 不是 Python 包，`pip install` 无法安装
- 版本没有锁定（代码里没有 version check）
- 如果 lark-cli API 变更，所有 JSON 解析会静默地返回错误数据
- 目前在测试中通过 mock runner 绕过，57 个真实 E2E 测试被 skip

### 3.3 已知 Bug（来自 PRD + CHANGELOG）

| Bug | 描述 | 状态 |
|---|---|---|
| record_id 与字段值混淆 | PRD 直接点名的前身问题，Skill prompt 无法保证 record_id 正确 | 在 Base 写入层面已有防护，文档层未修复 |
| RegistryCache 失效逻辑 | v1.3.1 修复了监控文件而非目录 | ✅ 已修复 |
| prompt_file 路径规范化 | v1.3.1 修复 | ✅ 已修复 |
| async 阻塞事件循环 | v1.3.1 修复 | ✅ 已修复 |

---

## 4. Architecture Assessment

### 4.1 飞书平台耦合度

**高度耦合，无抽象边界。**

- `runtime/live_adapter.py`（1151 行）：全部是 Feishu 特定代码（`lark-cli base`、`lark-cli drive`、`lark-cli task`、`lark-cli todo`）
- `runtime/lark_cli.py`：直接 subprocess 调用 `lark-cli` 二进制
- `runtime/semantic_registry.py`：硬编码中文表名（`客户主数据`、`行动计划`等）
- `runtime/scene_runtime.py`：每个场景 handler 直接实例化 `LarkCliClient`、`LiveWorkbenchConfig`

PRD 要求的 `PlatformAdapter(ABC)` 接口**不存在**。`LarkCliCustomerBackend`、`LarkCliSchemaBackend`、`LarkCliBaseQueryBackend` 这些类的功能正好对应 PRD 中 `PlatformAdapter` 的各个方法，但没有抽象契约，直接由场景代码持有。

### 4.2 场景逻辑 vs 平台 I/O 的分离程度

**部分分离，不彻底。**

- **有价值的分离：** `SceneRequest/SceneResult` 数据结构是平台无关的。`WriteGuard`、`SchemaPreflightRunner` 的核心逻辑通过 `SchemaBackend` 协议注入（Protocol），有最小化的接口抽象。
- **问题：** 但各个 `run_*_scene()` 函数直接构造 `LarkCliClient()`、`LiveWorkbenchConfig.from_sources()`，平台实例化在场景内部，而不是从外部注入。这导致测试中只能 mock 底层 `subprocess.run`，而不是替换整个 Adapter。

### 4.3 lark-cli 依赖风险评估

| 维度 | 结论 |
|---|---|
| 是否 Python 包？ | ❌ 不是，`pip install lark-cli` 无效 |
| 是否版本锁定？ | ❌ 代码中无 version check，requirements.txt 中未列出 |
| 是否活跃维护？ | 未知（仓库中无版本信息，无 URL 引用，只有二进制名 `lark-cli`） |
| API 变更影响？ | lark-cli JSON 格式若变化，`_extract_base_tables`、`_extract_list` 等解析代码会返回空数据，且无明显报错 |
| CI 中能否运行真实测试？ | ❌ 57 个涉及 lark-cli 的测试全部 skip（需要真实 lark-cli + Feishu 凭证） |

**结论：lark-cli 是一个不透明的外部二进制依赖，是现有架构最脆弱的组件之一。**

### 4.4 Expert System 评估

当前机制：
- 每个场景有 `expert-cards.yaml`，定义 `input_review` 和 `output_review`
- 路由是**静态的**（场景和专家绑定在 YAML 里）
- 冲突解决：不存在。多专家时只有 sequential 或 council 模式，没有冲突处理逻辑
- 平台 capabilities（openclaw、hermes、claude_code 等）在 `scene_runtime.py` 里硬编码，其中 hermes、claude_code、codex 标注为 **ASSUMED**（未验证）
- LLM fallback → keyword 模式的降级机制已实现，有 Circuit Breaker

---

## 5. Test Coverage

### 5.1 总体数字

| 类别 | 数量 |
|---|---|
| 总测试数 | 399 |
| 通过 | 342 (85.7%) |
| 跳过（需要真实 Feishu 环境） | 57 (14.3%) |
| 失败 | 0 |

### 5.2 覆盖情况

| 测试文件 | 覆盖内容 | 质量评估 |
|---|---|---|
| `test_scene_runtime.py` | 场景结果形状、EvidenceContainer helpers | ✅ 有效，核心路径有测试 |
| `test_live_bitable_integration.py` | 真实 Feishu 集成 | ❌ 全部 skip，CI 中无法运行 |
| `test_lark_doc.py` / `test_lark_task.py` | 文档/任务 lark-cli E2E | ❌ 需要真实环境，大量 skip |
| `test_meeting_output_bridge.py` | 会议输出桥接逻辑 | ✅ 有 mock 测试 |
| `test_expert_agent_adapter.py` | LLM expert 调用 | ✅ mock 测试 |
| `test_scene_e2e/` | 4 个场景的 E2E 测试 | ✅ 有效，但用 mock client |
| `test_portability_contract.py` | 可移植性合规检查 | ✅ 结构验证 |
| `test_skill_tokens.py` | SKILL.md token limit | 特定于 Codex Skill，新架构无关 |

### 5.3 关键路径覆盖情况

| 关键路径 | 有无测试 |
|---|---|
| Base 表记录写入（有 mock client） | ✅ |
| Todo 写入（有 mock client） | ✅ |
| 客户档案文档写入（实际文档操作） | ❌ 无测试（测试中只验证"建议输出"，不验证实际文档写入） |
| Schema preflight（mock schema） | ✅ |
| WriteGuard allowlist | ✅ |
| 真实 Feishu schema 探测 | ❌ skip |
| 多步写入失败回滚 | ❌ 无测试（功能本身也不存在） |
| customer resolver 模糊匹配 | ✅ |

---

## 6. Scene Gap Analysis Against PRD P1 Scenes

PRD 第 5.1 节标题写"共 13 个"，但实际表格列出 15 行——因为 `relationship-graph` 和 `periodic-report` 两个原属 P2 的场景后来被提前到 P1，正文有说明，但标题计数未同步更新。本报告以表格实际行数（15 个）为准。

| 场景 ID | PRD 说明 | 现有覆盖 | Gap | 复用潜力 |
|---|---|---|---|---|
| `customer-onboarding` | 新客建档 + 历史数据导入 | ❌ 不存在 | 完整 Gap：无建档流程，无历史导入管道 | 低（全新功能）|
| `opportunity-create` | 商机立项，与客户档案双向关联 | ❌ 不存在 | 完整 Gap | 低（全新功能）|
| `meeting-prep` | 七维简报生成 | ✅ `run_meeting_prep_scene` 已实现 | 需评估七维输出是否完整；无法使用 Kuzu 图谱数据 | 高：业务逻辑可复用 |
| `proposal` | 结构化方案框架（五维） | ✅ `run_proposal_scene` 已实现 | 无图谱数据输入；输出写入仍是 prompt-driven | 高：业务逻辑可复用 |
| `project-initiation` | 合同签后结构化录入 SOW/里程碑/团队 | ❌ 不存在 | 完整 Gap | 低（全新）|
| `kickoff-prep` | SOW+客户背景+关键人整合 | ❌ 不存在 | 完整 Gap | 中（可复用 meeting-prep 模式）|
| `project-tracking` | 周例会 → 进展/风险/行动项提取 | ❌ 不存在 | 完整 Gap | 中（可复用 post-meeting 模式）|
| `post-meeting-synthesis` | 会议记录 → 客户状态/行动项/关键人动态 | ✅ `run_post_meeting_scene` 已实现 | 文档写入仍 prompt-driven；无图谱更新 | 高：核心业务逻辑可复用 |
| `customer-recent-status` | 四维全貌查询 | ✅ `run_customer_recent_status_scene` 已实现 | 无 Kuzu 图谱查询能力 | 高：可复用 |
| `todo-capture` | 行动项提取 + 写入 | ✅ `run_todo_capture_and_update_scene` 已实现 | 基本完整，需对接 MCP 接口 | 高 |
| `archive-refresh` | 多源合并更新档案叙事 | ✅ `run_archive_refresh_scene` 已实现 | 外部导入源（Confluence/Jira）不支持 | 高：核心叙事更新逻辑可复用 |
| `external-import` | Confluence/Jira/本地文件/URL → 档案 | ❌ 不存在 | 完整 Gap（架构上完全缺失） | 低（全新）|
| `cohort-scan` | 群体风险/机会聚合分析 | ✅ `run_cohort_scan_scene` 已实现 | 仅基于 Feishu Base 数据，无图谱增强 | 中：逻辑可复用，需数据层升级 |
| `relationship-graph` | 决策链/影响路径查询（提前到 P1） | ❌ 不存在 | 完整 Gap（需要 Kuzu）| 低（全新，且需图谱层）|
| `periodic-report` | 聚合所有客户变化的经营报告（提前到 P1） | ❌ 不存在 | 完整 Gap | 中（可复用 cohort-scan 模式）|

**小结：** 7/15 场景有现有实现可复用；8/15 需全新开发。现有 7 个场景中，所有涉及"写回"的路径都需要重构以对接 PlatformAdapter 接口和 MCP 协议。

---

## 7. Platform Adapter Feasibility

### 7.1 现有飞书集成可以成为 FeishuAdapter 的哪些部分

| 现有类 | 对应 PlatformAdapter 方法 |
|---|---|
| `LarkCliCustomerBackend.search_customer_master()` | `read_customer_records(filters)` |
| `LarkCliCustomerBackend._list_records()` | `read_customer_records(filters)` |
| `LarkCliBaseQueryBackend.query_rows_by_customer_id()` | 通用 read 方法 |
| `LarkCliSchemaBackend.get_table_schema()` | `get_schema()` |
| `TodoWriter.create()` / `update()` | `write_task(task)` |
| `LarkCliBaseQueryBackend.discover_archive_candidates()` | `read_documents(doc_id)` 的候选发现部分 |
| 无 | `write_customer_record(record_id, fields)` — 当前散布在场景代码中 |
| 无 | `read_tasks(filters)` — 只有写，无系统化读 |

### 7.2 什么是硬编码的迁移阻碍

1. **中文表名**：`客户主数据`、`行动计划`、`客户联系记录` 直接作为字符串出现在多处（semantic_registry.py、live_adapter.py、scene_runtime.py）。企微/钉钉的字段名必然不同，无法 reuse。
2. **lark-cli 命令结构**：`base +record-create`、`drive files list`、`task tasklists list` 等 CLI 命令是飞书特有的，其他平台没有对应命令。
3. **todo_tasklist_guid / todo_priority_field_guid**：飞书 Todo 的自定义字段结构是飞书特有的。
4. **Feishu Drive 文件夹 token**：档案 folder_token 格式是飞书特有的。
5. **Schema 字段 ID**：`field_id` 是飞书 Base 的概念，DingTalk/WeChatWork 用不同的字段标识方式。

### 7.3 估算

| 方案 | 工作量估计 | 风险 |
|---|---|---|
| **Refactor**：提取 PlatformAdapter 接口 + 将现有飞书代码整理为 FeishuAdapter | 4-6 天 | 中：需要确保现有测试仍通过 |
| **Rewrite**：从 PRD 接口定义重写整个 Adapter 层 | 3-5 天 | 低：干净起点，但现有代码里的细节（lark-cli 命令参数、error type 处理）需要重新摸索 |

**建议选 Rewrite**：`live_adapter.py` 是 1151 行的单一大文件，里面有大量飞书特定的字段解析细节。在这上面做 refactor 比重写更容易引入隐性 bug。

---

## 8. Knowledge Graph Readiness

### 8.1 现有数据模型是否映射到图实体

| 业务实体 | 在现有代码中的存储 | 可成为图节点 |
|---|---|---|
| 客户（Customer） | 客户主数据 Base 表 | ✅ 主节点 |
| 联系人 / 关键人（Contact） | 客户联系记录表（推断） | ✅ |
| 商机（Opportunity） | 无独立表 | ❌ 目前不存在 |
| 合同（Contract） | semantic_registry 中有 `合同` | ✅ |
| 行动计划（ActionItem） | 行动计划表 | ✅ |
| 档案（Archive） | Feishu 文档（Drive） | ⚠️ 文档 token 可以是节点，但内容未结构化 |
| 集成商（Integrator） | 无 | ❌ |
| 竞品（Competitor） | semantic_registry 中有 `竞品` | ⚠️ |

### 8.2 隐性关系结构（应变为图的显性边）

| 隐性关系 | 当前实现 | 图中应建的边 |
|---|---|---|
| 客户 → 关键人 | 散落在联系记录表文本字段中 | `(Customer)-[:HAS_CONTACT]->(Person)` |
| 客户 → 商机 | 不存在 | `(Customer)-[:HAS_OPPORTUNITY]->(Opportunity)` |
| 商机 → 决策链 | 完全没有 | `(Opportunity)-[:INVOLVES]->(Person{role: decision_maker})` |
| 跨客户共同集成商 | 完全没有 | `(Customer)-[:USES]->(Integrator)<-[:USES]-(Customer)` |
| 风险传导路径 | 隐含在 cohort_scan 的关键词分析里 | 需要显性建模 |

### 8.3 结论

**现有代码中没有任何图数据库代码**，Kuzu 为零集成。要实现 `relationship-graph` 场景和 PRD 中的图谱推理能力，需要从零设计 Graph Schema 并实现同步管道。这是新架构中最大的新增工作量之一。

---

## 9. Expert System Evaluation

### 9.1 当前路由机制

- **静态绑定**：每个场景的 `expert-cards.yaml` 固定了该场景使用哪个专家（最多 1 个 input 专家 + 1 个 output 专家）。
- **无动态路由**：系统不根据输入内容的"风险级别"或"类型"动态选择专家，只是按场景名固定调用。
- **触发路径**：`scene_runtime.py` 中各场景函数调用 `ExpertCardLoader.load_expert_card(scene_name)` 获取配置，然后判断是走 LLM 模式还是 keyword 模式。

### 9.2 冲突解决现状

**不存在。** 当前设计：
- 每个场景最多同时触发 1 input + 1 output 专家
- `select_orchestration_strategy()`：1-2 专家用 sequential，3+ 专家才可能用 council
- 没有"专家 A 说 FLAG、专家 B 说 PASS"时的仲裁逻辑
- `AggregatedFailureResult` 处理的是 LLM 调用失败，不是观点冲突

### 9.3 `agents/` 文件夹结构的复用性

**可以直接复用**，具体情况：
- 4 个专家 MD 文件：内容质量高，业务知识密集，可直接复用
- `agent-registry.yaml`：YAML 结构清晰，有 `enabled/disabled`、`platform`、`prompt_file` 字段，可沿用
- 现有专家覆盖面：销售策略、客户服务、方案策略（对应 PRD 专家集合中的多个角色）
- 缺失：关系风险专家、交付风险专家、合同/法务专家、客户成功专家（PRD 专家集合中的 4 个）

### 9.4 与 PRD 新设计的差距

| PRD 新需求 | 现状 | Gap |
|---|---|---|
| 动态路由（根据内容类型和风险级别选 1-N 专家） | 静态路由（场景→专家固定绑定） | 需要新增路由引擎 |
| Host agent 原生 sub-agent 机制 | 自己实现了 `ExpertAgent` ABC + `DefaultLLMExpertAgent` | 方向不一致：PRD 依赖 host agent（OpenClaw/Hermes）的原生并行，现有实现是独立 LLM 调用 |
| 默认注释模式（专家意见附在主输出旁） | LLM 模式返回 findings 列表，scene_runtime 不处理注释模式 | 需要新增输出渲染层 |
| 可配置门控模式（高风险写操作需专家 PASS） | 存在 `write_guard.py` 但不与专家意见联动 | 需要连接 WriteGuard 和 ExpertReviewResult |

---

## 10. Technical Debt Inventory

### P0 — 阻断新架构的问题

| # | 问题 | 具体表现 |
|---|---|---|
| P0-01 | **没有 MCP Server** | 整个系统是 Codex Skill，没有任何 MCP 协议实现（无 `server.py`，无 `mcp` 依赖）。PRD 要求的产品形态从零开始。 |
| P0-02 | **没有 PlatformAdapter 抽象** | 飞书 I/O 直接散布在场景代码中，无法替换为企微/钉钉，也无法进行平台无关测试。 |
| P0-03 | **lark-cli 是无版本锁定的外部二进制** | 无法在 CI 中运行真实集成测试，无法保证 API 兼容性，57 个 E2E 测试长期 skip。 |
| P0-04 | **没有本地知识库层（Kuzu + ChromaDB）** | 图谱查询、向量检索功能为零，8 个新 P1 场景中有 2 个强依赖图谱（`relationship-graph`、`periodic-report`）。 |

### P1 — 必须在首次发布前修复

| # | 问题 | 具体表现 |
|---|---|---|
| P1-01 | **文档写入仍是 prompt-driven** | 客户档案和会议记录文档的写入不经过代码层验证，PRD 明确指出这是需要解决的根本性问题 |
| P1-02 | **Schema 硬编码** | `semantic_registry.py` 的中文字段名硬编码，多用户场景下无法复用 |
| P1-03 | **写操作无事务支持** | 多步写入部分失败时无补偿逻辑，数据一致性靠用户手动修复 |
| P1-04 | **8 个新 P1 场景完全缺失** | `customer-onboarding`、`opportunity-create`、`project-initiation`、`kickoff-prep`、`project-tracking`、`external-import`、`relationship-graph`、`periodic-report` 均未实现 |
| P1-05 | **对话初始化流程不存在** | PRD 要求非技术用户通过 agent 对话完成全自动安装+初始化，目前需要手动写 .env 文件 |

### P2 — 应修复但可以绕过发布

| # | 问题 | 具体表现 |
|---|---|---|
| P2-01 | `scene_runtime.py` 过大（1916 行） | 7 个场景全挤在一个文件，可维护性差，合并冲突频繁 |
| P2-02 | Platform capabilities 有 ASSUMED 标注 | `hermes`、`claude_code`、`codex` 的并行能力是假设的，从未验证 |
| P2-03 | 专家冲突解决机制缺失 | 多专家观点不同时无仲裁逻辑 |
| P2-04 | 外部导入管道不存在 | Confluence/Jira/本地文件 → 档案的转换管道为零 |
| P2-05 | `todo-capture` 与 `archive-refresh` 部分功能重叠 | 职责边界不清晰，action item 的归属判断有歧义 |

### P3 — 期望修复但优先级低

| # | 问题 | 具体表现 |
|---|---|---|
| P3-01 | 没有 Schema 自动探测 | `get_schema()` 依赖用户手动配置字段，PRD 要求自动探测适配 |
| P3-02 | cohort-scan 的四维分析基于关键词匹配 | 当客户记录内容简短时，keyword 匹配率极低，分析结果价值有限 |
| P3-03 | SKILL.md 的 token 限制测试 | `test_skill_tokens.py` 在新架构（非 Skill）中完全无意义 |
| P3-04 | references/ 部分文档包含飞书特定内容 | 如果复用文档到新架构，需要去 Feishu-specific 语言 |
| P3-05 | `config/` 中 example.yaml 格式与 PRD 的 config.yaml 不兼容 | 需要完全重新设计 |

---

## 11. Recommendation

### 什么可以直接复用（无需重写）

1. **Expert 系统基础设施**：`ExpertAgent` ABC、`CircuitBreaker`、`AggregatedFailureResult`、`DefaultLLMExpertAgent`、`ExpertCardLoader`
2. **EvidenceContainer 数据模型**：`EvidenceContainer`、`EvidenceSource`、`EvidenceQuality` — 概念通用
3. **WriteGuard 逻辑**：`WriteGuard.evaluate()` 可平台无关，仅需替换 allowlist 来源
4. **agents/ MD 文件**：4 个专家 prompt 文件内容质量高，直接继续使用
5. **场景业务逻辑模式**：context recovery 流程、lens 分析框架、output 结构定义
6. **evals/ 框架**：eval runner 和 evals.json 格式

### 什么需要重写

1. **整个 I/O 层**：`live_adapter.py` 全部重写为 `FeishuAdapter(PlatformAdapter)` 实现，同时设计抽象接口
2. **产品入口**：从 `SKILL.md`（Codex Skill）改为 `server.py`（MCP Server，使用 Anthropic mcp SDK）
3. **Schema 层**：从 `semantic_registry.py` 硬编码改为动态 Schema 探测（`config.yaml` + `schema.json`）
4. **配置和初始化流程**：从 `.env` + runtime_sources 改为对话驱动初始化

### 建议的重构顺序

```
Phase 1（1-2周）：建基础设施
  ├─ 新建 PlatformAdapter(ABC) 接口
  ├─ 将现有 live_adapter.py 重组为 FeishuAdapter 实现
  ├─ 新建 MCP Server 骨架（server.py，注册现有 7 个场景）
  └─ 现有 7 个场景通过 MCP Tools 暴露，确保测试仍通过

Phase 2（2-3周）：知识库层
  ├─ 集成 Kuzu（图谱 schema 设计：Customer、Contact、Opportunity、Contract 节点）
  ├─ 集成 ChromaDB（会议记录、档案片段向量化）
  └─ 实现 external-import 管道（Confluence/Jira/本地文件）

Phase 3（2-3周）：新增场景
  ├─ customer-onboarding
  ├─ opportunity-create
  ├─ relationship-graph（依赖 Phase 2 Kuzu）
  ├─ periodic-report
  └─ 其余 4 个新场景

Phase 4（1周）：对话初始化 + 发布
  ├─ 实现对话初始化流程
  ├─ 完成 README（对应 PRD 第 6 节体验要求）
  └─ 修复写操作事务问题（P1-03）
```

**总工程量估计：** 7-9 周（1 名工程师）。主要风险是 Kuzu 图谱 Schema 设计，一旦设计不当后期迁移代价高。

---

*本报告已完成，等待 review。不开始架构设计。*
