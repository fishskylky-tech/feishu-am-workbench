# Validation

本文档定义 `feishu-am-workbench` 当前版本的多案例验证协议，用来判断：

- 当前分支是否真的比旧版更稳
- 它的改进是否能在真实会议材料中被观察到
- 哪些问题已经被规则兜住
- 哪些问题还需要继续补强

当前协议不是重型 benchmark 框架，而是可重复执行的最小闭环。

当前核心上下文恢复阶段的自动化与人工收尾结论是：

- 当前核心上下文恢复切片已通过：`tests.test_env_loader`、`tests.test_runtime_smoke`、`tests.test_meeting_output_bridge`
- 当前核心上下文恢复阶段 code review clean，security audit `threats_open: 0`
- human UAT 4/4 passed
- 仍保留一类人工项：真实飞书工作区中的 archive / meeting-note fallback 证据质量复核

本轮新增两条验证主线：

- 核心上下文恢复是否已经形成 gateway-first、confidence-aware 的稳定审计闭环
- 统一 Todo 写回通道是否已经形成最小闭环

## 验证目标

本轮验证的目标不是证明“自动写回 ready”，而是证明：

- skill 更容易被正确触发
- facts / judgment / open questions 能被更清楚地区分
- recommendation mode / no-write 边界更稳
- 关键 hard rules 对真实场景有实际约束力
- 会议分析前会先尝试 live-first gateway，而不是默认单文件分析
- meeting 场景的上下文恢复会把 fallback 证据、冲突候选和 write ceiling 显式暴露出来
- meeting 场景产出的 Todo candidate 已可进入统一 writer，并返回标准化 write result

## 样本范围

本轮固定使用 3 个真实案例：

1. 联合利华
   - 文件：`tests/fixtures/transcripts/20260410-联合利华 Campaign活动分析优化-阶段汇报.txt`
   - 类型：探索型阶段汇报
   - 风险：把探索性内容误写成成熟经营结论、误建 Todo、相对时间不归一
2. 永和大王
   - 文件：`tests/fixtures/transcripts/20260409 神策AI 产品和永和大王会议记录.txt`
   - 类型：产品 / 方案沟通
   - 风险：误识别为标准会后更新，错误生成客户经营写回计划
3. 达美乐
   - 文件：`tests/fixtures/transcripts/2026-3-18 达美乐神策会议纪要.txt`
   - 类型：广告追踪答疑 / 系统使用问题澄清
   - 风险：把“问题澄清会议”误判成经营推进会议，错误抽取行动计划或主数据更新

## RED / baseline

这一步不是跑自动写回，而是定义“如果没有这次分支优化，agent 最容易怎么错”。

每个案例都要记录：

1. 场景类型
2. 预期正确行为
3. 旧版或弱规则状态下最可能出现的错误行为
4. 为什么当前分支应该解决这些问题

本轮 baseline 重点看 5 类失败：

- 触发命中不足
- 规则只写结论、不写 why，导致机械执行或误执行
- reference 过多但导航不清，导致加载路径混乱
- recommendation mode / no-write 边界不稳
- meeting 场景没有先尝试 gateway Stage 1-3

## GREEN / current-branch

这一步验证当前分支是否带来了可观察的改善。

每个案例都要判断：

- 是否更容易正确触发 skill
- 是否能区分 facts / judgment / open questions
- 是否先尝试 gateway Stage 1 / 2 / 3
- 是否能显式记录 resource resolution、customer resolution、context status 和 used Feishu sources / fallback reason
- 是否能给出 context status 和 write ceiling
- fallback 候选冲突或弱证据是否会显式降级，而不是被隐藏
- 是否能保持 recommendation mode，而不是越权写回
- 是否把该类会议归到正确输出重心

### 联合利华通过标准

- 先尝试 gateway Stage 1 / 2 / 3
- 不直接生成 `客户主数据` 写回
- 不自动创建 Todo
- 明确 open questions、write ceiling、context status
- 相对时间改成绝对时间，或明确标注 precision gap

### 永和大王通过标准

- 先尝试 gateway；若未执行，fallback 原因必须合规
- 不把产品能力讨论误当作标准客户经营更新
- 不默认产出典型的 `客户联系记录` / `行动计划` / `客户主数据` 更新建议
- 输出重点放在问题理解、能力边界、后续跟进建议

### 达美乐通过标准

- 先尝试 gateway；若未执行，fallback 原因必须合规
- 不伪造客户经营进展
- 不把广告追踪答疑错误转成主数据变化或经营结论
- 输出重点放在系统解释需求、口径澄清、后续支持动作建议

## REFACTOR / regression

在 baseline 和 current-branch 对照完成后，再检查验证资产本身是否可重复使用。

本轮 regression 检查项：

- `CHANGELOG.md`、`VERSION`、`evals/evals.json` 版本是否一致
- `evals/evals.json` 是否纳入 3 个真实案例
- `VALIDATION.md` 是否明确 baseline / green / regression 的执行协议
- 是否明确 live-first 是会议案例的强制前置条件
- 是否已有最小 runner 能执行结构化断言
- 是否已有统一的多案例验证报告

如果 runner 存在，后续会议案例应优先通过 runner 复核；人工复核只作为补充说明，不再是唯一执行方式。

## 通用检查项

每个案例都要检查：

- 是否先尝试 gateway
- 是否完成 context recovery，或明确声明 `not_run` / `context-limited`
- 是否写明 fallback 原因
- 是否说明 write ceiling
- 是否把 facts 和 judgment 分开
- 是否标注 blocked items 和 open questions
- 是否遵守 no-write fallback
- 是否避免盲猜字段名
- 是否把输出重心放在该场景真正需要的内容上

如果场景涉及 Todo，还要额外检查：

- 是否产出结构化 Todo candidate
- candidate 是否带 `operation`、`match_basis`、`source_context`、`target_object`
- 是否显示 dedupe 决策
- 是否显示 preflight / guard / blocked 结果
- recommendation mode 和 confirmed write mode 是否分离清楚
- 若命中 `create_subtask`：
   - 默认是否保持 recommendation-only
   - 仅在显式确认（`source_context.confirm_create_subtask=true`）时才执行真实写入

## 当前执行方式

本轮默认使用三层验证资产：

1. 文档层
   - 本文档定义执行协议
   - 多案例验证报告记录 baseline 与 current-branch 结论
2. 数据层
   - `evals/evals.json` 保存真实案例、预期行为和断言
3. 执行层
  - `evals/runner.py` 读取案例和 agent 输出，并逐条执行断言
  - `evals/meeting_output_bridge.py` 把 transcript + gateway 结果拼成 runner 可复核的最小输出
  - bridge 既支持手工注入 `GatewayResult`，也支持先执行 gateway 再生成输出
  - bridge 现在可继续执行最小 Stage 3 context recovery：读取 `客户联系记录`、`行动计划` 和客户档案链接
   - bridge 现在会在显式链接缺失时进行受限 fallback 搜索，并把冲突候选与 `写回上限` 降级显式写入输出
  - bridge 现在可生成最小 Todo candidate，并在确认后调用统一 Todo writer

## 当前验证报告

- [2026-04-10-unilever-campaign-phase-report.md](./archive/validation-reports/2026-04-10-unilever-campaign-phase-report.md)
  - 单案例探索型阶段汇报验证
- [2026-04-11-multi-case-skill-validation.md](./archive/validation-reports/2026-04-11-multi-case-skill-validation.md)
  - 本轮 3 案例 baseline / current-branch / regression 统一结论

## 验证完成标准

本轮可以宣告“测试完成”的条件是：

- 3 个案例都完成 baseline 与 current-branch 对照判定
- runner 能对 3 个案例执行结构化断言
- `evals/evals.json` 覆盖 3 个真实案例并与验证口径一致
- `CHANGELOG.md`、`VERSION`、`evals/evals.json` 版本一致
- 统一验证报告已经产出
- 可以给出按 P1 / P3 排序的修改建议
- 至少 1 个 meeting 场景已验证统一 Todo writer 的 candidate -> result 闭环

## Durable-Output Routing Rules

Each scene routes its durable output to a specific Feishu destination:

| Scene | Destination | Output Type |
|-------|-------------|-------------|
| `post-meeting-synthesis` | Feishu Todo | Task creation with customer/priority fields |
| `customer-recent-status` | Feishu Docs | Structured account posture note |
| `archive-refresh` | Feishu Docs | Structured archive update note |
| `cohort-scan` | Feishu Docs | Cohort analysis summary |
| `meeting-prep` | Feishu Docs | Seven-dimension meeting brief |
| `proposal` | Feishu Docs or Todo | Structured proposal draft or action items (depending on proposal_type) |
| `todo-capture-and-update` | Feishu Todo | Task creation/update |

Routing behavior:
- `proposal` scene routes to Docs for proposal/report drafts, or to Todo for action items, based on the `proposal_type` field
- All scenes follow the recommendation-first principle before any write is executed
- Write execution requires explicit user confirmation through the confirmation checklist
