from pathlib import Path

root = Path('/Users/liaoky/.codex/skills/feishu-am-workbench')
updates = []

arch = root / 'ARCHITECTURE.md'
text = arch.read_text(encoding='utf-8')
old = "## 目标扩展架构\n\nPhase 7 已锁定未来扩展的目标形态，但这不是说这些目录和技能今天都已经实现。\n"
new = "## 目标扩展架构\n\nPhase 7 已锁定未来扩展的目标形态，但这不是说这些目录和技能今天都已经实现。\n\n这一层的 canonical contract 由 3 份文档共同组成：\n\n- [references/scene-skill-architecture.md](references/scene-skill-architecture.md)\n  - 约束 scene skills 的场景边界、第一波优先级和 expert agents handoff\n- [references/workspace-bootstrap.md](references/workspace-bootstrap.md)\n  - 约束 admin/bootstrap path 的最小交付物、兼容性检查和强确认边界\n- [references/cache-governance.md](references/cache-governance.md)\n  - 约束 schema、manifest/index、semantic/ontology 三类 cache 的 trust hierarchy 与 refresh lifecycle\n"
if old not in text:
    raise SystemExit('ARCHITECTURE anchor 1 not found')
text = text.replace(old, new, 1)
old = "### 2. Scene skills\n\nscene skill 的边界必须按经营场景拆，而不是按表拆。\n"
new = "### 2. Scene skills\n\nscene skill 的边界必须按经营场景拆，而不是按表拆。\n\n具体的 scene contract、首波场景和 expert-agent return artifact，统一收口到 [references/scene-skill-architecture.md](references/scene-skill-architecture.md)，避免未来把这些规则重新塞回根级 skill。\n"
if old not in text:
    raise SystemExit('ARCHITECTURE anchor 2 not found')
text = text.replace(old, new, 1)
old = "### 5. Admin / bootstrap 与 cache\n\n安装检查、workspace compatibility、config 生成、cache 刷新，不属于日常主 skill 主流程，必须独立成 admin/bootstrap path。\n"
new = "### 5. Admin / bootstrap 与 cache\n\n安装检查、workspace compatibility、config 生成、cache 刷新，不属于日常主 skill 主流程，必须独立成 admin/bootstrap path。\n\nbootstrap/admin 的最低交付物、受控远端初始化边界，以及 cache 的 subordinate-to-live-truth 规则，分别由 [references/workspace-bootstrap.md](references/workspace-bootstrap.md) 和 [references/cache-governance.md](references/cache-governance.md) 负责承载。\n"
if old not in text:
    raise SystemExit('ARCHITECTURE anchor 3 not found')
text = text.replace(old, new, 1)
arch.write_text(text, encoding='utf-8')
updates.append('ARCHITECTURE.md')

skill = root / 'SKILL.md'
text = skill.read_text(encoding='utf-8')
old = "## Packaging Direction\n\nThe current root skill should evolve toward this boundary:\n\n- root skill = thin entry and orchestration layer\n- scene skills = workflow-specific capability packages\n- expert agents = scene-internal collaborators returning structured intermediate artifacts\n- runtime foundation = shared live access and safety layer\n- admin/bootstrap path = setup, compatibility, config, and cache lifecycle\n\nThis packaging direction is architectural guidance, not a claim that those scene-skill folders already exist today.\n"
new = "## Packaging Direction\n\nThe current root skill should evolve toward this boundary:\n\n- root skill = thin entry and orchestration layer\n- scene skills = workflow-specific capability packages\n- expert agents = scene-internal collaborators returning structured intermediate artifacts\n- runtime foundation = shared live access and safety layer\n- admin/bootstrap path = setup, compatibility, config, and cache lifecycle\n\nThe root skill should keep only the responsibilities that stay globally consistent:\n\n- scene detection\n- deciding whether live context is needed\n- coordinating the recommendation -> confirmation -> write flow\n- preserving one top-level interaction pattern across scenes\n\nDetailed workflow rules should move toward scene skills, and expert agents should be called by those scene skills on demand rather than by the root skill as a universal pipeline.\n\nCanonical Phase 7 contract references:\n\n- [references/scene-skill-architecture.md](./references/scene-skill-architecture.md)\n- [references/workspace-bootstrap.md](./references/workspace-bootstrap.md)\n- [references/cache-governance.md](./references/cache-governance.md)\n\nThis packaging direction is architectural guidance, not a claim that those scene-skill folders already exist today.\n"
if old not in text:
    raise SystemExit('SKILL anchor not found')
text = text.replace(old, new, 1)
skill.write_text(text, encoding='utf-8')
updates.append('SKILL.md')

cfg = root / 'CONFIG-MODEL.md'
text = cfg.read_text(encoding='utf-8')
old = "所以后续必须拆成三层：\n\n- `Core Skill`\n- `User Workspace Config`\n- `Safe Runtime Guardrails`\n"
new = "所以后续必须拆成三层：\n\n- `Core Skill`\n- `User Workspace Config`\n- `Safe Runtime Guardrails`\n\n同时还要明确一条新的边界：\n\n- 日常经营 scene 走主 skill / scene skill / runtime path\n- setup、diagnosis、compatibility、cache refresh 走单独的 admin/bootstrap path\n\n也就是说，`workspace config` 是环境边界，`bootstrap` 是围绕这个边界做初始化和检查的管理路径，`guardrails` 是真正拦住不安全写入的运行时边界。\n"
if old not in text:
    raise SystemExit('CONFIG anchor 1 not found')
text = text.replace(old, new, 1)
old = "如果不先做配置层，后续“给别人用”会变成复制一份你的个人 skill，而不是复用一个通用内核。\n"
new = "如果不先做配置层，后续“给别人用”会变成复制一份你的个人 skill，而不是复用一个通用内核。\n\n---\n\n## 八、Admin / Bootstrap 边界\n\n从 Phase 7 开始，bootstrap 不再被视为根级 skill 的日常路径，而是独立的 admin/bootstrap contract。\n\n这条路径最少要覆盖：\n\n- workspace compatibility 检查\n- 本地 workspace config 生成或更新建议\n- cache 初始化 / 刷新输出\n- drift 与风险报告\n- `lark-cli` 版本和可用命令面检查\n\n它可以做本地自动修复，但任何远端初始化或修复都必须走强确认，不得默默混入日常客户经营场景。\n\n相关 canonical references：\n\n- [references/workspace-bootstrap.md](./references/workspace-bootstrap.md)\n- [references/cache-governance.md](./references/cache-governance.md)\n"
if old not in text:
    raise SystemExit('CONFIG anchor 2 not found')
text = text.replace(old, new, 1)
cfg.write_text(text, encoding='utf-8')
updates.append('CONFIG-MODEL.md')

print('updated:', ', '.join(updates))
