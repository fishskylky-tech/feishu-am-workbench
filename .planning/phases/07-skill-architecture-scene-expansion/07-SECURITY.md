---
phase: 07
slug: skill-architecture-scene-expansion
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-16
---

# Phase 07 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| root skill -> scene skills | 根入口只能做路由和顶层交互，不应把 scene-specific authority 吞回根级 skill | routing decision, write-mode choice, scene selection |
| scene skills -> runtime foundation | scene skills 可以决定读取和推理范围，但 shared foundation 仍负责 live access 和 write safety | customer resolution, targeted reads, preflight, guard |
| admin/bootstrap -> live workspace | bootstrap 可以做 compatibility / repair / controlled setup，但不得越过 daily safety boundary | config guidance, cache refresh, controlled remote initialization |
| cache artifacts -> scene reasoning / write planning | cache 只允许做 routing 和 early reasoning，加速不能替代 live truth | schema snapshots, manifest/index hints, semantic mappings |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-07-01 | Elevation of Privilege | SKILL.md / ARCHITECTURE.md | mitigate | 将 root skill 明确限定为 thin entry and orchestration layer，避免把 scene-specific write authority 收回根级入口 | closed |
| T-07-02 | Tampering | references/scene-skill-architecture.md | mitigate | 以 workflow 而不是 raw table 定义 scene skills，并锁定 first-wave/deferred scenes，避免后续拆分漂移回表驱动架构 | closed |
| T-07-03 | Information Disclosure | references/cache-governance.md | mitigate | 将 schema、manifest/index、semantic cache 全部定义为 subordinate acceleration layers，并要求 critical reads / writes live confirm | closed |
| T-07-04 | Elevation of Privilege | references/workspace-bootstrap.md | mitigate | 把 bootstrap 限定为 admin-only path，并要求任何 remote initialization 都走 strong confirmation | closed |

*Status: open · closed*  
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-16 | 4 | 4 | 0 | GitHub Copilot |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-16
