# Feishu AM Workbench

## What This Is

Feishu AM Workbench is a personal AM skill project for Hermes/OpenClaw/Codex-style agents. It helps a Sensors Data AM use Feishu Base, Drive docs, and Task as a customer operating platform: recover live context, interpret customer materials, propose safe updates, and gradually evolve toward a reusable account-management operating model.

This is a brownfield project: the repository already has a working runtime, validation assets, a private GitHub collaboration surface, and a live Feishu workspace with customer master, contracts, actions, key people, competitors, archives, meeting notes, and a task module.

## Core Value

Use one live-first, safety-first skill to turn AM inputs into actionable customer operating context and guarded write plans inside the existing Feishu workbench.

## Requirements

### Validated

- ✓ Local runtime can resolve Feishu resource hints and render capability diagnostics — v1.0
- ✓ Meeting flow can execute live-first gateway with customer resolution and minimum context recovery — v1.0
- ✓ Todo write surface returns normalized preflight/guard/dedupe/write results — v1.0
- ✓ 客户主数据 / 客户联系记录 / 行动计划 already have a minimal semantic contract in runtime — v1.0
- ✓ Repository already contains real-case eval assets and regression tests for the current meeting/Todo path — v1.0
- ✓ Root guidance, milestone audit evidence, and runtime operator surface are aligned with shipped state — v1.0

- ✓ Add expert analysis and multi-source evidence fusion — Phase 16
- ✓ Upgrade post-meeting and Todo outputs with four-section customer-operating format (CORE-02) and structured 意图 + 判定理由 fields (TODO-01/02) — Phase 17
- [ ] Expand customer recent status from a single-account summary into account-posture analysis plus cohort-level risk/opportunity/common-issue scanning
- [ ] Add recommendation-first meeting prep and proposal/report/resource-coordination scenes with explicit write-back paths
- [ ] Standardize durable output routing, confirmation checklists, and archive/document update targets for expert-led scene outputs
- [ ] Preserve live-first, recommendation-first, guarded-write, and host-portable boundaries while scene intelligence expands

### Out of Scope

- Full SaaS CRM productization — current priority is personal AM value, not a multi-tenant app
- Automatic writes without confirmation — violates the project safety model
- Full-field mirroring of every Feishu table — too fragile and too expensive to maintain
- Generic platform abstraction that ignores the current Feishu workbench operating model — would dilute near-term value

## Context

- Shipped milestone: v1.0 archived on 2026-04-16 with roadmap, requirements, audit, and phase artifacts preserved under `.planning/milestones/`.
- Shipped milestone: v1.1 archived on 2026-04-17 with executable scene runtime roadmap, requirements, and audit artifacts preserved under `.planning/milestones/`.
- Local repo now documents architecture, status, validation protocol, security model, roadmap intent, and a runtime meeting write-loop operator surface.
- GitHub remote is active and private, with open issues, PRs, discussions, and one active Projects v2 board for 2026 roadmap execution.
- Live Feishu Base currently contains 8 business tables, including customer master, contracts, actions, key people, competitors, contact logs, and a potential-customer pool.
- Live customer archive folder already mixes canonical customer archives, a meeting-note folder, a weekly-info folder, and a template doc; this reflects real workflow value but also data quality risks.
- Live task module currently centers on a single 神策 tasklist, which is already part of the runtime write path.
- Existing docs now reflect a completed v1.0 brownfield milestone and are ready for the next milestone definition cycle.

## Constraints

- **Tech stack**: Python runtime + lark-cli + markdown skill docs — this is already the established execution surface
- **Security**: secrets and live resource identifiers stay in env/private runtime sources — required to avoid leaking personal customer workspace data
- **Safety**: writes must remain recommendation-first and guarded — high-risk master-data updates cannot become automatic
- **Brownfield**: roadmap must respect existing runtime, docs, tests, and live workspace structures — this is not a greenfield rewrite
- **Portability**: business logic should stay portable across agent hosts — the project is intended for Hermes/OpenClaw-style usage, not one locked host

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat the repo as a brownfield GSD project | Existing code, tests, docs, and live resources already prove non-trivial scope | — Pending |
| Keep the runtime thin and scene-driven | Foundation should resolve/protect, not over-assemble business context | ✓ Good |
| Model Base through minimal semantic contracts, not full mirrors | Reduces drift and maintenance cost | ✓ Good |
| Keep personal-value-first before generalization | Matches current user goal and existing roadmap language | ✓ Good |
| Use live Feishu structure as a planning input, not just local docs | Prevents roadmap drift from real workspace operations | ✓ Good |

## Current State

- v1.0 shipped with phases 1-11 complete and archived.
- v1.1 shipped with phases 12-15 complete and archived.
- v1.2 shipped with phases 16-21 complete and archived — 7 scenes, VAL-05 24/24 tests pass.
- Repository supports 7 executable scene runtimes on one shared contract: post-meeting-synthesis, customer-recent-status, archive-refresh, todo-capture-and-update, cohort-scan, meeting-prep, proposal.
- Live-first, recommendation-first, guarded-write boundaries proven in production.

## Most Recent Milestone: v1.2 Expert Customer Operating Scenes

**Outcome:** Upgrade executable scenes into expert-guided customer-operating workflows and add three new recommendation-first AM scenes.

**Delivered:**
- Expert-augmented post-meeting synthesis with multi-source evidence fusion (CORE-01, CORE-02, TODO-01, TODO-02)
- Four-lens account-posture analysis and cohort-scan scene (STAT-01, SCAN-01)
- Structured archive refresh with five-dimension synthesis (ARCH-01)
- Meeting prep and proposal scenes with confirmation checklists (PREP-01, PROP-01, WRITE-01, WRITE-02)
- VAL-05 regression: 24/24 tests pass across 6 scenes × 4 case types

## Current Milestone: v1.3 开源准备与Skill巩固

**Goal:** 阶段性巩固 v1.0-v1.2 已完成的能力，安全干净地发布到 GitHub public，为后续 Skill 生态扩展打基础。

**Target features:**

### v1.3.1 — 开源安全 + 发版
- 隐私文件清理（.planning/ → gitignore，本地保留）
- 敏感文件名脱敏（unilever 客户名等）
- 添加 MIT LICENSE
- 所有决定公开的文档统一重写为"开源使用者/贡献者友好"标准
- 其他文档评估与归档

### v1.3.2 — Skill 规范化 + 能力深化巩固
1. **整体完成度评估** — 基于 v1.0-v1.2 代码、ROADMAP、REQUIREMENTS 进行全面复盘，识别有提升空间的领域
2. **Skill 规范化** — SKILL.md 精简到 <2,000 tokens，保持 L1/L2/L3 边界；对标 agentskills.io / anthropics/skills / darwin-skill / Google ADK 标准
3. **agency-agents 引入** — 独立 scene 配置文件（方案 C），专家审核层：scene 输入/输出加专家把关

**Key constraints for v1.3:**
- 不增加新业务场景，聚焦巩固和规范化
- 开源原则：只公布对使用者有帮助的内容，开发文件本地保留
- agency-agents 引入不改核心 scene 逻辑

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-19 after v1.3 milestone initialization*