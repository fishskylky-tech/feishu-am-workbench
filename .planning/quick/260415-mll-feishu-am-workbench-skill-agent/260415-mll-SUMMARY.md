# Quick Task 260415-mll Summary

> Superseded: this first-pass assessment has been refined by [260415-nz8-SUMMARY.md](../260415-nz8-feishu-am-workbench-skill-skill/260415-nz8-SUMMARY.md). Use the refined summary as the default input for later architecture decisions.

**Date:** 2026-04-15
**Status:** Completed
**Type:** External-methodology architecture review

## Executive Conclusion

当前 feishu-am-workbench 适合继续演进为“单一入口 skill + 多子 skill + 按需专家 agent 协同”的模式，但不适合直接从现在的一体化 skill 跳到大量并行专家。最佳路线是保留现有共享 runtime 和安全边界，先把已验证成熟的场景拆成子 skill，再在场景编排层上引入窄角色 agent。

## Direct Answers

### 1. 是否应该拆成多个子 skill

应该，但不是立即把所有客户经营能力按表或按对象拆开。

原因：

- 当前根级 SKILL.md 已经太像一个“能力总包”，其中 L1/L2/L3 分层、场景规则、硬规则和资源索引都已具备拆分前提。
- 现有仓库已经具备 progressive disclosure 结构，但打包粒度仍停留在“一个 skill + 一组 references”，这会让后续场景越堆越厚。
- runtime 已经把资源解析、客户解析、preflight、guard 与业务判断分开，允许多个子 skill 共用底座而不是重复实现。

不建议的拆法：

- 不建议第一波就按 合同、关键人、竞品、联系记录 这种表级边界拆，因为这些场景链路还没有像 meeting 一样完成闭环验证。

建议的第一波拆分：

1. gateway-foundation
2. post-meeting-interpreter
3. meeting-prep
4. account-review-archive-refresh
5. safe-writeback

### 2. 是否适合引入专家角色 agent

适合，但角色要放在场景 skill 之上，且保持薄协调。

最合适的模式是：

- 一个 coordinator 负责识别任务意图和路由
- 一个 gateway-researcher 负责 live context 恢复
- 场景专家负责深度解释
- 一个 write-planner 负责归一写回建议
- 一个 write-executor 在确认后执行

不建议的模式是：

- 让 runtime 直接承担专家判断
- 让多个 agent 深度递归调用彼此
- 为所有表面向未来预先造专家角色

### 3. 当前 roadmap、phase、runtime、skill 文档结构的支持与阻碍

支持点：

- ROADMAP.md 已经明确反对“继续堆一个更长的 skill”，而是倾向能力包方向。
- ARCHITECTURE.md 已把场景编排层、抽取与判断层、飞书底座层分开，这正是 skill 化和 agent 化的前置边界。
- runtime/models.py 与 runtime/semantic_registry.py 提供了 typed contract 和最小语义面，天然适合多 skill 共用。
- SKILL.md 已采用 ADK 风格的 progressive disclosure 和按需 references 加载。
- STATUS.md 说明当前最成熟的真实闭环已经是 meeting + Todo，这为第一波拆分提供了优先级依据。

阻碍点：

- 当前只有一个根 skill，没有项目内真正可单独激活的子 skill 目录。
- references/ 更像按主题拆文档，而不是按能力包组织。
- 扩展表仍处于 profile-ready、多数场景未闭环状态，不适合过早角色化。
- 当前 STATE/STATUS 记录了 phase 进展，但缺少围绕场景专家协作的显式交接 artifact 约定。

### 4. 如果采用这种模式，推荐目标架构

#### Target Shape

- 单一入口 skill：只负责识别场景、声明共识规则和路由到子 skill
- foundation skill：封装 gateway、resource resolution、customer resolution、preflight、guard
- scene skills：meeting-prep、post-meeting、account-review、archive-refresh
- writeback skill：确认后的统一写回
- expert agents：由场景 skill 在必要时触发，而不是全局常驻并列运行

#### Recommended Agent Roles

1. coordinator
2. gateway-researcher
3. meeting-interpreter
4. account-strategist
5. write-planner
6. write-executor

#### Trigger Relationships

- 会议纪要或 transcript
  - coordinator -> gateway-researcher -> meeting-interpreter -> write-planner -> 用户确认 -> write-executor
- 会前准备
  - coordinator -> gateway-researcher -> meeting-prep skill
- 客户经营盘点
  - coordinator -> gateway-researcher -> account-strategist -> 可选 write-planner
- 明确写回请求
  - coordinator -> gateway-researcher -> write-planner -> 用户确认 -> write-executor

### 5. 对当前规划和架构的 review 结论

保留：

- 共享 runtime 底座
- live-first 与 recommendation-first
- 最小语义面而非全量 schema mirror
- 场景层决定读取什么，foundation 不做默认上下文拼装
- meeting 场景作为当前最高优先的真实闭环

调整：

- 把根 skill 收缩成入口 skill，而不是继续累加所有场景细节
- 把 references 从“主题平铺”逐步调整为“能力包聚合”
- 在 ARCHITECTURE.md 中显式补上 coordinator 与 handoff contract
- 在 ROADMAP.md 中把 M3/M2 的部分目标重新表述为“专家化子 skill 的优先落地路径”

新增：

- 子 skill 目录结构与命名约定
- 专家 agent 角色与触发矩阵
- 面向 skill 协作的 artifact 或 contract 说明
- 针对新子 skill 的评估与验证样例

### 6. 迁移路径

1. 维持当前根 skill 与 runtime 不动，先把这次结论纳入规划。
2. 首先把 post-meeting interpreter 独立成第一个场景子 skill，因为它已有最强验证基础。
3. 再拆 meeting-prep 与 account-review-archive-refresh。
4. 待场景 skill 稳定后，再将 safe-writeback 从场景层逻辑中进一步抽离。
5. 最后再考虑更细的领域专家，例如合同、关键人、竞品，但前提是这些链路已形成真实验证闭环。

## File-Based Review Notes

- ROADMAP.md 已经口头上支持能力包与角色化，但还没有把这件事落实成阶段目标和触发矩阵。
- ARCHITECTURE.md 的层次划分很适合继续演进，只差把“入口 skill / coordinator”和“专家 handoff contract”补进去。
- SKILL.md 已经符合 ADK/Anthropic 的 skill 规范思路，但粒度仍过粗。
- runtime/gateway.py、runtime/models.py、runtime/semantic_registry.py 是这次演进里最值得保留的基础设施。
- STATUS.md 明确提示：现在应该优先围绕已成熟场景拆，而不是围绕未来表结构拆。

## Final Recommendation

结论不是“继续维持单一 skill”，也不是“立刻多 agent 大拆”。

更准确的建议是：

- 近期保留单一入口 skill
- 中期形成 3 到 5 个场景化子 skill
- 按需触发少量专家 agent
- 始终复用现有 runtime、安全边界和验证资产

这样能同时满足三件事：

1. 不破坏当前 live-first 闭环
2. 控制 prompt 复杂度和上下文膨胀
3. 为后续多 host portability 留出清晰边界