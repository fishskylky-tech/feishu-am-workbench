# Milestone Context — v1.3

**Created:** 2026-04-19
**Source:** Discussion during v1.2 closeout and v1.3 planning session

---

## v1.2 状态对齐（会前完成）

- GitHub Issues 已关闭：#32（场景缺失，已在 v1.2 proposal+proposal 解决）、#38（AM日常场景，部分覆盖）、#20/#21/#22（M3 子项）
- GitHub Issues 保持 Open（v1.3 候选）：#9, #12, #13, #14, #15
- REQUIREMENTS.md 13/13 需求全部标记为 shipped ✅
- v1.2 milestone audit PASSED (13/13, 24/24 VAL-05 tests)

---

## v1.3 目标

**主题：** 阶段性回顾和巩固，并为下阶段（开源仓库）做好准备

### 两个 Phase 拆分

| Milestone | 范围 |
|-----------|------|
| **v1.3.1** | 开源安全 + 发版 |
| **v1.3.2** | Skill 规范化 + agency-agents 引入 |

---

## v1.3.1: 开源准备

### 核心原则

> 只公布对使用者操作 skill 有帮助的内容。开发/调试用的文件本地保留，远端干净。

### 文件分类决策

#### 🚨 隐私/安全（必须处理）

| 文件/目录 | 问题 | 决策 |
|-----------|------|------|
| `.planning/` | milestone 笔记、用户 context、内部决策全暴露 | `git rm --cached` + 本地保留 + .gitignore |
| `archive/validation-reports/*-unilever-*` | 真实客户名在文件名 | 重命名脱敏后移入 .gitignore |
| `tests/fixtures/transcripts/*.txt` | 真实客户/项目中文名在文件名 | 移入 .gitignore |
| `.env` | 含 Feishu token | 已在 .gitignore，本地保留 |

#### ✅ 公布（帮助使用者操作 skill）

`SKILL.md` / `README.md`（需重写） / `GETTING-STARTED.md` / `AGENTS.md` / `SECURITY-MODEL.md` / `WORKFLOW.md` / `CHANGELOG.md` / `CONFIGURATION.md` / `VERSION` / `LICENSE`（需添加） / `.gitignore` / `.github/PULL_REQUEST_TEMPLATE.md`

#### ❌ 归档（对使用者无直接帮助，贡献者参考放 DEVELOPMENT.md）

`CLAUDE.md` / `ARCHITECTURE.md` / `DEVELOPMENT.md` / `TESTING.md` / `VALIDATION.md` / `ASSESSMENT.md` / `STATUS.md` / `ROADMAP.md` / `CONFIG-MODEL.md` → 移入 .gitignore

#### 📁 不确定（需确认）

`archive/` 目录其他文件 — 需评估内容是否含敏感信息

### README 重写要求

- 对齐当前 v1.2 真实状态
- 面向开源使用者/贡献者友好
- 包含：功能概览、快速开始、场景列表、配置说明

---

## v1.3.2: Skill 规范化 + agency-agents 引入

### agency-agents 引入决策

**选择方案：C — 独立 scene 配置文件**

> 像把专家卡片做成活页夹，每个场景需要时，从活页夹里抽出对应的专家页插进去。

- 专家角色单独一个文件存在
- scene 运行时读取对应的专家配置
- 增删专家只需要动活页夹，不动生产线
- 不改现有 scene 核心逻辑，可插拔

**引入目的：** 在关键节点让"专家"帮忙把关输入/输出的准确性和业务专业性

- 用户输入 → 先让"风险分析师"过一遍，检查遗漏风险信号
- 输出的 Todo/建议 → 让"经营顾问"审核，判断建议是否专业

### Skill 规范化参考

1. **agentskills.io 标准** — 对齐 Agent Skills 格式规范
2. **Google ADK Agent Skills 构建指南** — `https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/`
3. **anthropics/skills** — `https://github.com/anthropics/skills`
4. **darwin-skill** — `https://github.com/alchaincyf/darwin-skill`

### agency-agents 参考

- **GitHub**: `https://github.com/msitarzewski/agency-agents`
- **理念**：多角色专家框架，每个 agent 有独立 personality + deliverables
- **可借鉴的模式**：Engineering Division / Reddit Community 等角色卡片的组织方式

### 其他 v1.3.2 参考

- **GSD skill 设计规范** — `.planning/` 里的 questioning.md / project.md / requirements.md 等模板
- **目标**：SKILL.md 精简到 <2,000 tokens，保持 L1/L2/L3 边界

---

## 遗留 Open Issues（v1.3 范围外，可选纳入）

| # | 标题 | 优先级 |
|---|------|--------|
| #9 | SKILL.md 精简到 <2,000 tokens | P1 |
| #12 | Workspace 配置层抽象 | P1 |
| #13 | 架构可视化图 + 快速上手指南 | P2 |
| #14 | Context Hydrator 独立为 runtime/ | P2 |
| #15 | CI/CD 自动化测试集成 | P2 |

---

## GSD 相关 Skill/模板参考

| 类型 | 路径/名称 | 用途 |
|------|---------|------|
| Workflow | `gsd-new-milestone` | milestone 初始化流程 |
| Workflow | `gsd-plan-phase` | phase 规划 |
| Workflow | `gsd-execute-phase` | phase 执行 |
| Workflow | `gsd-verify-work` | 验证 |
| Template | `$HOME/.claude/get-shit-done/templates/project.md` | PROJECT.md 模板 |
| Template | `$HOME/.claude/get-shit-done/templates/requirements.md` | REQUIREMENTS.md 模板 |
| Reference | `$HOME/.claude/get-shit-done/references/questioning.md` | 需求收集方法论 |
| Reference | `$HOME/.claude/get-shit-done/references/ui-brand.md` | UI 品牌参考 |
| Workflow | `$HOME/.claude/get-shit-done/workflows/next.md` | next 路由判断 |

---

## 待确认事项（进入 milestone 后细化）

- [ ] archive/ 目录其他文件的内容审查（是否含敏感信息）
- [ ] README 重写具体内容
- [ ] agency-agents 专家角色的具体场景映射（哪些 scene 用哪些专家）
- [ ] SKILL.md 精简的具体取舍（L1/L2/L3 各保留什么）
