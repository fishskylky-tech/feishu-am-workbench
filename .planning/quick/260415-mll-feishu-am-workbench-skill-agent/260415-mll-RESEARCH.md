# Quick Task 260415-mll Research

**Date:** 2026-04-15
**Task:** 对 feishu-am-workbench 做多子 skill + 专家 agent 协同演进评估
**Mode:** quick-task with research

## Research Question

当前 feishu-am-workbench 是否适合从单一 skill 继续演进为多子 skill + 专家 agent 协同模式；如果适合，应如何拆分而不破坏现有 runtime、安全边界和验证闭环。

## External Framework Signals

### GSD

- 核心方法不是把主 agent 做大，而是让薄编排器驱动专门子 agent，并把状态和决策沉到文件中。
- 价值点在于：主上下文不承担所有重活，研究、规划、执行、验证分别由专门角色处理。
- 对本仓库的含义是：如果未来引入专家 agent，最合理的位置是场景编排层，而不是让 runtime 直接长出业务判断。

### Google ADK Skills

- 明确反对 monolithic prompt，推荐 progressive disclosure：L1 metadata、L2 instructions、L3 resources。
- file-based skill 和 external skill 适合把复杂能力拆成可独立加载、复用和演进的目录单元。
- meta-skill 或 skill factory 说明“生成新 skill”是后续能力，但前提仍然是描述准确、边界清晰、资源按需加载。
- 对本仓库的含义是：现有 references 分层已经是 skill 化的前置条件，但还没有完成到“每个能力一个自包含 folder”的打包粒度。

### Anthropic Skills

- 推荐形态是 self-contained skill folder：SKILL.md 负责触发与操作说明，resources 负责细节知识。
- skill 的 description 是激活边界，skill folder 的自包含性决定了它能否稳定被复用。
- 对本仓库的含义是：当前根级 SKILL.md 已具备 skill 规范意识，但整仓仍然是一个大 skill，场景边界主要通过 references/ 约定，而非真正的子 skill 目录隔离。

## Repository Evidence

### Supports Evolution

- SKILL.md 已显式采用 L1/L2/L3 progressive disclosure，并把 references 分为 meeting、write、customer、extraction、common、on-demand 几类。
- ARCHITECTURE.md 与 references/feishu-workbench-gateway.md 已经把场景编排层与飞书底座分开，符合“薄协调层 + 共享底座”的原则。
- runtime/models.py 已定义 GatewayResult、ContextRecoveryResult、WriteCandidate、WriteExecutionResult 等 typed handoff contract，天然适合多 agent 协作。
- runtime/semantic_registry.py 与 references/base-integration-model.md 已经把 live schema 与业务语义面拆开，减少子 skill 被字段细节绑死的风险。
- VALIDATION.md、STATUS.md、evals/meeting_output_bridge.py 和 tests/ 说明当前最小 live-first 闭环已经可验证，不需要为 skill 拆分先重写 runtime。

### Blocks Or Slows Evolution

- 当前只有一个根级 SKILL.md，项目内没有真正的 project-scoped 子 skill 目录可供自动发现和独立激活。
- references/ 已按主题分层，但不是按“能力包”收口，导致复用单位更像文档集合，而不是可单独触发的 skill。
- 当前最成熟的真实闭环主要是 post-meeting 和 Todo；合同、关键人、竞品虽然已有 profile，但场景链路不够成熟，不适合立刻拆成多个专家 skill。
- STATE/STATUS 记录了 phase 进展，但技能执行本身还没有统一的 runtime artifact 协议来持久化 agent 间交接结果。

## Recommended Direction

### Architecture Style

- 保留一个总入口 skill 作为路由层。
- 保留现有 runtime 作为共享底座，不把业务专家逻辑沉到 runtime。
- 先按已验证场景拆 skill，再按成熟场景引入专家 agent。

### First-Wave Skill Boundaries

1. gateway-foundation
2. post-meeting-interpreter
3. meeting-prep
4. account-review-archive-refresh
5. safe-writeback

### Agent Roles

1. coordinator
2. gateway-researcher
3. meeting-interpreter
4. account-strategist
5. write-planner
6. write-executor

## Main Risks

- 过早按表拆专家：会得到很多“有名无实”的 skill，因为当前真实场景闭环并未覆盖全部表。
- 把 runtime 做成万能上下文装配器：会破坏当前已经写清楚的 foundation 边界。
- 先做重型平台化：会分散对个人高频价值和稳定性的投入。

## Research Conclusion

适合演进，但不适合直接从“一个大 skill”跳到“很多平行专家”。最稳妥路径是：

1. 保留单一入口 skill
2. 先把最成熟场景拆成子 skill
3. 用 typed contract 串联专家 agent
4. 最后再收缩根 skill，只保留路由、共识规则和安全红线