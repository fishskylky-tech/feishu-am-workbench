# Roadmap: Feishu AM Workbench

**Created:** 2026-04-17
**Last updated:** 2026-04-19 after v1.3 initialization
**Mode:** Interactive
**Granularity:** Standard
**Execution:** Sequential within each phase

## Current Planning State

- Active mainline milestone: v1.3 开源准备与Skill巩固
- Previous shipped milestone: v1.2 Expert Customer Operating Scenes

## Active Milestone

### Phase 22: 开源安全与发版准备

**Goal:** 安全、干净地将仓库发布到 GitHub public，无隐私泄露，文档完整准确。

**Depends on:** v1.2 archived milestone outputs

**Requirements:** ASSESS-01, CLEAN-01, CLEAN-02, CLEAN-03, CLEAN-04, CLEAN-05, CHECK-01

**Success criteria:**
1. ASSESS-01 完成：全面评估当前仓库状态，覆盖隐私/安全、开源就绪度、文档完整性、外部依赖
2. CLEAN-01 完成：.planning/ 从 git 移除，.gitignore 更新，本地文件保留
3. CLEAN-02 完成：所有含敏感客户名的文件名脱敏
4. CLEAN-03 完成：MIT LICENSE 文件存在且有效
5. CLEAN-04 完成：所有公开文档（README、GETTING-STARTED、AGENTS 等）重写为开源友好版本
6. CLEAN-05 完成：内部文档全部移入 .gitignore，远端干净
7. CHECK-01 完成：最终复核通过，无敏感信息泄露，必要时外部安全扫描通过

**Plans:** 9/10 plans executed

**Plan list:**
- [x] 22-01-PLAN.md — Wave 1: 全面评估（ASSESS-01）
- [x] 22-02-PLAN.md — Wave 2: 清理与脱敏（CLEAN-01~04）
- [x] 22-04-PLAN.md — Wave 2b: 内部文档归档与Git历史清理（CLEAN-05）
- [x] 22-03-PLAN.md — Wave 3: 最终复核（CHECK-01）
- [x] 22-05-PLAN.md — Wave 1: Gap3 - LICENSE Copyright 修复
- [x] 22-06-PLAN.md — Wave 1: Gap1 - README.md AM视角重写
- [x] 22-07-PLAN.md — Wave 1: Gap2 - GETTING-STARTED.md 优化
- [x] 22-08-PLAN.md — Wave 1: Gap4 - GitHub仓库对齐milestone 1.3
- [x] 22-09-PLAN.md — Wave 1: Gap5 - AGENTS/SECURITY-MODEL/WORKFLOW 中文改写
- [ ] 22-10-PLAN.md — Wave 1: Git历史/标签/gitignore 补充修复

### Phase 23: Skill 规范化与能力深化巩固

**Goal:** 基于 v1.0-v1.2 完成度评估，进行针对性深化巩固；引入 agency-agents 专家审核层；SKILL.md 精简对标外部标准。

**Depends on:** Phase 22

**Requirements:** ASSESS-03, ASSESS-04, NORM-02, NORM-01, AGENT-01, AGENT-02

**Success criteria:**
1. ASSESS-03 完成：v1.0-v1.2 全面复盘完成，识别出至少 3 个有提升空间的领域
2. ASSESS-04 完成：针对评估结果制定了具体的深化或巩固方案
3. NORM-02 完成：对标 agentskills.io / anthropics/skills / darwin-skill / Google ADK 标准
4. NORM-01 完成：SKILL.md 精简到 <2,000 tokens，L1/L2/L3 边界清晰
5. AGENT-01 完成：独立 scene 配置文件机制建立（方案 C），可插拔
6. AGENT-02 完成：至少 2 个 scene 接入专家审核层（输入或输出）

**Plans:** pending

## Archived Milestones

### v1.2: Expert Customer Operating Scenes

- Status: shipped 2026-04-18
- Phases: 16-21 complete
- Archive: [.planning/milestones/v1.2-ROADMAP.md](.planning/milestones/v1.2-ROADMAP.md)
- Requirements: [.planning/milestones/v1.2-REQUIREMENTS.md](.planning/milestones/v1.2-REQUIREMENTS.md)
- Audit: [.planning/milestones/v1.2-MILESTONE-AUDIT.md](.planning/milestones/v1.2-MILESTONE-AUDIT.md)

### v1.1: Executable Scene Runtimes

- Status: shipped 2026-04-17
- Phases: 12-15 complete
- Archive: [.planning/milestones/v1.1-ROADMAP.md](.planning/milestones/v1.1-ROADMAP.md)
- Requirements: [.planning/milestones/v1.1-REQUIREMENTS.md](.planning/milestones/v1.1-REQUIREMENTS.md)
- Audit: [.planning/v1.1-MILESTONE-AUDIT.md](.planning/v1.1-MILESTONE-AUDIT.md)

### v1.0: Milestone

- Status: shipped 2026-04-16
- Phases: 1-11 complete
- Archive: [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md)
- Requirements: [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md)
- Audit: [.planning/v1.0-MILESTONE-AUDIT.md](.planning/v1.0-MILESTONE-AUDIT.md)

---

*Last updated: 2026-04-19 after v1.3 initialization*
