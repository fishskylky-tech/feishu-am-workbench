# Requirements: Feishu AM Workbench

**Defined:** 2026-04-14
**Core Value:** Use one live-first, safety-first skill to turn AM inputs into actionable customer operating context and guarded write plans inside the existing Feishu workbench.

## v1 Requirements

### Foundation

- [ ] **FOUND-01**: Repository contains a brownfield GSD initialization baseline with codebase map, project context, requirements, roadmap, and state artifacts
- [ ] **FOUND-02**: Runtime can load private `FEISHU_AM_*` configuration from shell env or local `.env`, with explicit env taking precedence
- [ ] **FOUND-03**: Skill and runtime preserve the documented live-first / recommendation-first operating rules across supported scenes
- [ ] **FOUND-04**: Project guidance artifacts stay aligned with actual repo state, validation assets, and next executable phases

### Live Runtime

- [ ] **LIVE-01**: Runtime can resolve Base, archive folder, meeting-note folder, and tasklist from private runtime sources without committed secrets
- [ ] **LIVE-02**: Runtime can report Base / Docs / Task capability status before business reasoning starts
- [ ] **LIVE-03**: Runtime can resolve a customer from live 客户主数据 by customer name or customer ID
- [ ] **LIVE-04**: Runtime can recover minimum scenario context from 客户主数据, 客户联系记录, 行动计划, and archive link for a resolved customer

### Workbench Model

- [ ] **WORK-01**: Runtime maintains a minimal semantic contract for 客户主数据, 客户联系记录, and 行动计划
- [ ] **WORK-02**: Runtime keeps extensible table profiles for 合同清单, 客户关键人地图, 竞品基础信息表, and 竞品交锋记录 without full field mirroring
- [ ] **WORK-03**: Skill can consistently connect customer archive docs and meeting-note docs back to customer context using durable identifiers and routing rules

### Meeting And Analysis

- [ ] **MEET-01**: Meeting and post-meeting flows execute the live-first gateway before formal analysis
- [ ] **MEET-02**: Meeting outputs expose auditable resource status, customer result, context status, used sources, write ceiling, and open questions
- [ ] **MEET-03**: Meeting flows can produce recommendation-mode Todo candidates with `operation`, `match_basis`, `source_context`, and `target_object`

### Safe Writes

- [ ] **WRITE-01**: Every write candidate passes through schema preflight and write guard before becoming write-ready
- [ ] **WRITE-02**: Todo writer returns normalized execution results with preflight status, guard status, dedupe decision, blocked reasons, and remote object metadata
- [ ] **WRITE-03**: High-risk customer master updates remain guarded and default to recommendation-only when confidence or schema safety is insufficient

### Validation And Portability

- [ ] **VAL-01**: Repo contains executable multi-case validation assets for representative AM meeting scenarios
- [ ] **VAL-02**: Runtime and meeting bridge have regression tests for key failure modes including fallback, dedupe, and context recovery
- [ ] **VAL-03**: Status, validation, changelog, version, and eval assets stay internally consistent as the project evolves
- [ ] **PORT-01**: Business operating logic remains usable from Hermes/OpenClaw/Codex-style agent hosts without embedding host-specific assumptions into the domain model

## v2 Requirements

### Proactive Operating Outputs

- **PROA-01**: Skill can generate weekly or monthly account operating summaries from existing workbench data
- **PROA-02**: Skill can proactively flag stale accounts, missing actions, and opportunity/risk gaps

### Deeper Context Intelligence

- **DEEP-01**: Skill can rank and read related archive docs and historical meeting-note bodies beyond link-level recovery
- **DEEP-02**: Skill can apply a multi-stage expert interpretation model for complex customer materials

### Broader Portability

- **PORT-02**: New AM users can bootstrap the same operating model against their own Feishu workspace with minimal manual remapping

### Skill Architecture And Bootstrap

- [x] **ARCH-01**: Repo defines a canonical thin-main-skill plus scene-skill plus expert-agent plus shared-foundation architecture contract
- [x] **ARCH-02**: First-wave scene skills are defined by AM workflows with explicit priority order and structured expert-agent handoff rules
- [x] **ARCH-03**: Admin/bootstrap behavior is separated from daily scene execution and defines compatibility, config guidance, and controlled setup boundaries
- [x] **ARCH-04**: Schema, manifest/index, and semantic caches have explicit trust hierarchy, refresh lifecycle, and live-confirm rules that keep live truth authoritative

## Out of Scope

| Feature | Reason |
|---------|--------|
| Fully autonomous writes to customer master / contracts / strategy fields | Conflicts with safety-first operating model |
| Full CRM or multi-tenant product UI | Not the current project scope or leverage point |
| Complete live schema mirroring inside prompt/runtime semantics | Too costly and brittle for this stage |
| Non-Feishu primary data platform support | Current operating model is explicitly Feishu-centered |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 8 | Pending |
| FOUND-02 | Phase 8 | Pending |
| FOUND-03 | Phase 8 | Pending |
| FOUND-04 | Phase 8 | Pending |
| LIVE-01 | Phase 8 | Pending |
| LIVE-02 | Phase 8 | Pending |
| LIVE-03 | Phase 8 | Pending |
| LIVE-04 | Phase 9 | Pending |
| WORK-01 | Phase 9 | Pending |
| WORK-02 | Phase 9 | Pending |
| WORK-03 | Phase 9 | Pending |
| MEET-01 | Phase 9 | Pending |
| MEET-02 | Phase 9 | Pending |
| MEET-03 | Phase 10 | Pending |
| WRITE-01 | Phase 10 | Pending |
| WRITE-02 | Phase 10 | Pending |
| WRITE-03 | Phase 10 | Pending |
| VAL-01 | Phase 10 | Pending |
| VAL-02 | Phase 10 | Pending |
| VAL-03 | Phase 8 | Pending |
| PORT-01 | Phase 8 | Pending |
| PORT-02 | Phase 7 | Pending |
| ARCH-01 | Phase 7 | Complete |
| ARCH-02 | Phase 7 | Complete |
| ARCH-03 | Phase 7 | Complete |
| ARCH-04 | Phase 7 | Complete |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-14*
*Last updated: 2026-04-16 after Phase 6 and Phase 5 closure audit*