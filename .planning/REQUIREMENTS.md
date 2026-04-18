# Requirements: Feishu AM Workbench

**Defined:** 2026-04-19
**Milestone:** v1.3 开源准备与Skill巩固
**Core Value:** Use one live-first, safety-first skill to turn AM inputs into actionable customer operating context and guarded write plans inside the existing Feishu workbench.

## Milestone Focus

阶段性巩固 v1.0-v1.2 已完成的能力，安全干净地发布到 GitHub public，为后续 Skill 生态扩展打基础。

## Requirements

### v1.3.1 — 开源安全 + 发版

**（开头）全面评估**
- [ ] **ASSESS-01**: 全面评估当前仓库状态：
  - 隐私/安全风险：哪些文件含敏感信息（客户名、token、路径等）
  - 开源就绪度：哪些文件符合开源发布标准
  - 文档完整性：现有文档是否对齐 v1.2 真实状态
  - 外部依赖：lark-cli / Python 环境要求是否清晰

**（中间）清理与归档**
- [ ] **CLEAN-01**: `.planning/` 目录从 git 跟踪中移除，加入 `.gitignore`，本地保留供后续开发参考
- [ ] **CLEAN-02**: 脱敏敏感文件名（unilever 等客户名出现在 archive 文件名中）
- [ ] **CLEAN-03**: 添加 MIT LICENSE 文件
- [ ] **CLEAN-04**: 所有决定公开的文档重写为开源使用者/贡献者友好标准
- [ ] **CLEAN-05**: 其他内部文档归档（移入 .gitignore）

**（结尾）全面检查复核**
- [ ] **CHECK-01**: 全面复核清理结果：
  - 远端仓库无敏感信息泄露
  - 公开文档内容准确、对齐 v1.2 状态
  - 必要时有外部检查（如安全扫描、文档可读性验证）

### v1.3.2 — Skill 规范化 + 能力深化巩固

#### 能力复盘

- [ ] **ASSESS-03**: 基于 v1.0-v1.2 代码、ROADMAP、REQUIREMENTS 进行全面复盘，识别未完全完成的模块和有提升空间的领域
- [ ] **ASSESS-04**: 根据评估结果制定针对性深化或巩固方案

#### Skill 规范化

- [ ] **NORM-02**: 对标外部 Skill 标准：
  - agentskills.io 格式规范
  - https://github.com/anthropics/skills
  - https://github.com/alchaincyf/darwin-skill
  - https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/
- [ ] **NORM-01**: SKILL.md 精简到 <2,000 tokens，保持 L1/L2/L3 渐进式披露边界

#### agency-agents 引入

- [ ] **AGENT-01**: 引入独立 scene 配置文件机制（方案 C — 活页夹式专家卡片管理）
- [ ] **AGENT-02**: 在关键 scene 节点增加专家审核层：
  - 输入审核：用户材料经专家视角过一遍，检查遗漏信号
  - 输出审核：Todo/建议经经营顾问审核，判断专业性和业务逻辑

## Out of Scope

| Feature | Reason |
|---------|--------|
| 新增业务场景 | v1.3 聚焦巩固，不扩展 scene |
| CI/CD 自动化测试集成 | Issue #15，暂不纳入主线 |
| Workspace 配置层抽象 | Issue #12，暂不纳入主线 |
| 架构可视化图 | Issue #13，暂不纳入主线 |
| Context Hydrator 独立 | Issue #14，暂不纳入主线 |

## External References

| Reference | URL | Used In |
|-----------|-----|---------|
| anthropics/skills | https://github.com/anthropics/skills | NORM-02 |
| darwin-skill | https://github.com/alchaincyf/darwin-skill | NORM-02 |
| Google ADK Agent Skills Guide | https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/ | NORM-02 |
| agency-agents | https://github.com/msitarzewski/agency-agents | AGENT-01, AGENT-02 |

## Traceability

| Requirement | Phase |
|-------------|-------|
| ASSESS-01 | Phase 1 |
| CLEAN-01 | Phase 1 |
| CLEAN-02 | Phase 1 |
| CLEAN-03 | Phase 1 |
| CLEAN-04 | Phase 1 |
| CLEAN-05 | Phase 1 |
| CHECK-01 | Phase 1 |
| ASSESS-03 | Phase 2 |
| ASSESS-04 | Phase 2 |
| NORM-01 | Phase 2 |
| NORM-02 | Phase 2 |
| AGENT-01 | Phase 2 |
| AGENT-02 | Phase 2 |

## Archived Requirement Sets

- v1.2 archive: [.planning/milestones/v1.2-REQUIREMENTS.md](.planning/milestones/v1.2-REQUIREMENTS.md)
- v1.1 archive: [.planning/milestones/v1.1-REQUIREMENTS.md](.planning/milestones/v1.1-REQUIREMENTS.md)
- v1.0 archive: [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md)

---
*Requirements defined on 2026-04-19 for milestone v1.3*
