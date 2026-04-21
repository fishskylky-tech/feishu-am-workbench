# Milestones

## v1.3 — 开源准备与Skill巩固

**Shipped:** 2026-04-19
**PR:** v1.3-skill-and-open-source-prep → main (merged d521217)
**Phases:** 22-23 (15 plans total), 27
**Status:** 🔄 IN PROGRESS

### Accomplishments

1. **Phase 22 (开源安全与发版准备):** 全面仓库评估（35+ git历史泄露）、`.planning/`和`archive/`从git移除、MIT LICENSE添加、所有公开文档重写（中文AM视角）、敏感信息全量脱敏
2. **Phase 23 (Skill规范化与能力深化巩固):** SKILL.md从~22KB精简至1,349 tokens (<2,000)、Expert Card活页夹机制建立、2个scene接入输入/输出审核层
3. **外部标准对齐:** SKILL.md frontmatter对齐agentskills.io格式（name/version/description/triggers/load_strategy/tier）
4. **GitHub安全验证:** GitHub Secret Scanning已启用、detect-secrets pre-commit hook v1.5.0配置

### Known Deferred Items

- 2 quick tasks (260415-mll-*, 260415-nz8-*) acknowledged at close — see `.planning/quick/` for details

### Stats

- **Timeline:** 2026-04-19 (single day milestone, PR merged 23:02)
- **Contributors:** Fisher (112 commits), fishskylky-tech (26), anthropic-code-agent[bot] (3), Copilot (2), Claude (2)
- **Files changed:** 259 files (+1,890 / -29,531)

### Phase 27: expert-review-eval-infrastructure

**Goal:** 补充 Phase 26 评估覆盖的3个 CRITICAL gap
**Source:** 26-EVAL-REVIEW.md

| Gap | 描述 | 性质 |
|-----|------|------|
| G-01 | LLM expert review 参考数据集缺失 | 必须修复 |
| G-02 | evals/runner.py 未集成到 CI | 必须修复 |
| G-03 | hallucination guardrail 缺失 | 必须修复 |

**Status:** 🔄 PLANNING

### Phase 28: Summary Artifact Closure

**Goal:** 补全 Phase 24-25 缺失的 phase 级汇总文档
**Source:** v1.3.1-MILESTONE-AUDIT.md tech_debt

| Gap | 描述 | 性质 |
|-----|------|------|
| TD-01 | Phase 24 缺少 phase 级 SUMMARY.md | MEDIUM |
| TD-02 | Phase 25 缺少 phase 级 SUMMARY.md | MEDIUM |

**Status:** 🆕 NEW

### Phase 29: VALID_SCENES DRY Fix

**Goal:** 消除 expert_card_loader.py 和 scene_registry.py 中 VALID_SCENES frozenset 重复定义
**Source:** v1.3.1-MILESTONE-AUDIT.md tech_debt

| Gap | 描述 | 性质 |
|-----|------|------|
| TD-03 | VALID_SCENES frozenset 两处重复定义 | LOW |

**Status:** 🆕 NEW

### Phase 30: AI Integration Phase Review

**Goal:** 评估 v1.3.1 Phases 24-27 中哪些应该使用 gsd-ai-integration-phase 但没有使用
**Source:** user request

| Gap | 描述 | 性质 |
|-----|------|------|
| AI-01 | Phase 24-27 未经过 gsd-ai-integration-phase 评估 | SHOULD |

**Status:** 🆕 NEW

### Phase 31: Lark E2E Testing Enhancement

**Goal:** 评估现有测试方式，新增/更新通过 lark-cli 操作飞书多维表格、任务和文档的 E2E 测试
**Source:** user request

| Gap | 描述 | 性质 |
|-----|------|------|
| E2E-01 | 飞书任务 (Task) 操作缺少 E2E 测试 | SHOULD |
| E2E-02 | 飞书文档 (Doc) 操作缺少 E2E 测试 | SHOULD |
| E2E-03 | Bitable tests 可补充覆盖 | NICE |

**Status:** 🆕 NEW

### Phase 32: Phase 30 Gap Fixes

**Goal:** Fix 3 production gaps from Phase 30 (AI Integration Phase Review)
**Source:** 30-GAP-REPORT.md

| Gap | 描述 | 性质 |
|-----|------|------|
| E-26-01 | LLM mode never activated (expert-cards.yaml missing prompt_file) | CRITICAL |
| E-26-02 | Hallucination guardrail raises ValueError on empty check_signals | HIGH |
| E-27-01 | Only 3 of 15 eval cases run in CI | HIGH |

**Status:** ✅ COMPLETE

---

## v1.2 — 场景扩展与架构巩固

**Archived:** 2026-04-15
**Phases:** 14-21
**Status:** ✅ SHIPPED

### Accomplishments

1. 场景runtime架构冻结（Phase 12）
2. 规范化post-meeting scene runtime（Phase 13）
3. customer-recent-status scene runtime（Phase 14）
4. archive/todo scene扩展（Phase 15）
5. 专家分析基础与多源证据（Phase 16）
6. post-meeting/todo专家升级（Phase 17）
7. account posture与cohort扫描（Phase 18）
8. archive刷新与meeting-prep路径（Phase 19）
9. proposal报表与资源协调（Phase 20）
10. 验证与milestone收尾（Phase 21）

---

## v1.1 — 核心场景完善

**Archived:** 2026-04-14
**Phases:** 7-13
**Status:** ✅ SHIPPED

### Accomplishments

1. Skill架构与scene扩展架构定义（Phase 7）
2. 审核证据与指导对齐（Phase 8）
3. 上下文与账户验证收尾（Phase 9）
4. 安全写入与E2E收尾（Phase 10）
5. 收尾清理（Phase 11）

---

## v1.0 — MVP

**Archived:** 2026-04-09
**Phases:** 1-6
**Status:** ✅ SHIPPED

### Accomplishments

1. Brownfield基线建立（Phase 01）
2. Live runtime硬化（Phase 02）
3. 核心上下文恢复（Phase 03）
4. 统一安全写入（Phase 04）
5. 扩展账户模型（Phase 05）
6. 验证与可移植性（Phase 06）

---

*Last updated: 2026-04-21*
