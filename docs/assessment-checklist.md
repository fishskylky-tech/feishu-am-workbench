# Assessment Checklist

这个清单用于让仓库内的能力评估保持同一口径。

当前与 [ASSESSMENT.md](../ASSESSMENT.md) 对齐的 6 个维度如下。

## 1. Architecture

- **Criteria**: 场景层、runtime 底座、live adapter、writer 与验证资产是否边界清晰；是否继续保持 live-first、recommendation-first 与 non-bypass safety path。
- **Scoring Formula**: 10 分表示架构边界清楚、扩展路径明确、没有明显耦合回退；7-8 分表示主路径合理但仍有局部耦合或扩展风险；6 分及以下表示核心边界混乱或未来扩展会明显受阻。
- **Improvement Path**: 优先减少跨层耦合、收紧 scene contract、避免把场景逻辑重新塞回 foundation 或 CLI 入口。

## 2. Implementation Completeness

- **Criteria**: 当前里程碑承诺的能力是否真的落地；关键场景、回退路径和写回护栏是否都已有实现或明确阻断。
- **Scoring Formula**: 10 分表示 milestone 范围内能力、边界和证据都闭环；7-8 分表示主功能已到位但仍有缺口或只完成部分路径；6 分及以下表示主要承诺仍停留在文档层或缺少关键执行面。
- **Improvement Path**: 先补核心场景与 blocker，再补边缘路径；不要用文档宣称替代可执行实现。

## 3. Code Quality

- **Criteria**: 代码是否可读、可测、可维护；是否存在明显重复、脆弱分支、魔法值蔓延或安全边界绕过风险。
- **Scoring Formula**: 10 分表示结构清晰、测试友好、重复度低；7-8 分表示总体可维护但仍有局部技术债；6 分及以下表示质量问题已开始影响改动速度或正确性。
- **Improvement Path**: 收敛重复逻辑、补类型和测试、让关键路径更多依赖共享抽象而不是一次性分支。

## 4. Documentation

- **Criteria**: README、STATUS、VALIDATION、WORKFLOW、CONFIGURATION、TESTING 等主文档是否与当前代码和 planning 状态一致。
- **Scoring Formula**: 10 分表示主文档、验证文档和 milestone 事实同步；7-8 分表示大方向正确但局部口径滞后；6 分及以下表示文档会直接误导使用者或评审者。
- **Improvement Path**: 每次涉及用户可见行为、主线状态、配置或验证口径变化时同步更新对应主文档，并用只读核验或测试检查事实一致性。

## 5. Maintainability

- **Criteria**: 后续新增 scene、调整 schema、补验证或切换宿主时，当前实现是否容易演进；是否被过时假设、硬编码或隐式依赖拖慢。
- **Scoring Formula**: 10 分表示演进路径明确、替换点清楚；7-8 分表示可继续演进但有局部摩擦；6 分及以下表示每次改动都需要高成本理解或连带修复。
- **Improvement Path**: 优先清理硬编码资源假设、减少文档和实现分叉、把可复用规则沉到共享 contract 或 reference 中。

## 6. Multi-platform Adaptation

- **Criteria**: 核心 runtime、scene contract 和输出语义是否保持 host-agnostic，避免被单一 agent 平台、消息格式或交互假设锁死。
- **Scoring Formula**: 10 分表示 contract 与业务语义可跨宿主复用；7-8 分表示总体可迁移但仍有少量平台痕迹；6 分及以下表示平台绑定已进入核心执行面。
- **Improvement Path**: 保持 scene result、gateway 语义和验证资产平台无关，把宿主特定行为放在外层包装而不是核心 runtime。

## 使用说明

- 做阶段性评估时，先对照这 6 个维度逐项给出分数、发现、blockers 和改进动作。
- 如果某次评估是历史快照，应在评估文档中明确标注日期，避免被误读为当前状态。
- 如果新增评估维度，先同步更新这个清单，再更新 [ASSESSMENT.md](../ASSESSMENT.md) 的结构。