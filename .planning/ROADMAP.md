# Roadmap: Feishu AM Workbench

**Created:** 2026-04-14
**Mode:** Interactive
**Granularity:** Standard
**Execution:** Parallel where dependencies allow

## Summary

This roadmap turns the existing repository from a docs-heavy brownfield into a GSD-managed delivery program rooted in the real Feishu workbench, existing runtime, and validated meeting/Todo path.

**7 phases** | **25 v1 requirements mapped** | All v1 requirements covered ✓

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Brownfield Baseline | Turn the repo into a coherent GSD-managed project baseline | FOUND-01, FOUND-04, VAL-03 | 4 |
| 2 | Live Runtime Hardening | Stabilize resource resolution, capability diagnostics, and customer resolution | FOUND-02, LIVE-01, LIVE-02, LIVE-03 | 4 |
| 3 | Core Context Recovery | Make customer context recovery and meeting diagnostics reliable across core workbench objects | LIVE-04, WORK-01, WORK-03, MEET-01, MEET-02 | 5 |
| 4 | Unified Safe Writes | Mature normalized write preparation and guarded Todo-centric execution | MEET-03, WRITE-01, WRITE-02, WRITE-03 | 4 |
| 5 | Expanded Account Model | Bring contracts, key people, and competitor structures into targeted read/use paths safely | WORK-02 | 3 |
| 6 | Validation And Portability | Preserve trust, regression discipline, and host portability as capability breadth grows | FOUND-03, VAL-01, VAL-02, PORT-01 | 4 |
| 7 | Skill Architecture For Scene Expansion | Define the long-term main-skill plus scene-skill plus foundation architecture, bootstrap path, and cache strategy for expanding AM workflows safely | ARCH-01, ARCH-02, ARCH-03, ARCH-04 | 4 |

## Phase Details

### Phase 1: Brownfield Baseline

**Goal**

Create the durable project operating baseline: codebase map, brownfield project framing, requirements, roadmap, state, and aligned instructions for future GSD work.

**Requirements**

- FOUND-01
- FOUND-04
- VAL-03

**Success criteria**

1. `.planning/` contains codebase map, project, requirements, roadmap, and state artifacts anchored in the actual repo and live workspace
2. Project context explicitly reflects the private GitHub repo, live Feishu workspace structure, and current runtime status
3. Requirements and roadmap are traceable, phase-based, and ready for `/gsd-discuss-phase 1`
4. Project instructions point future agents at the planning workflow instead of ad hoc repo exploration

**Depends on**

- None

**UI hint**: no

### Phase 2: Live Runtime Hardening

**Goal**

Stabilize private configuration loading, capability reporting, resource source resolution, and customer resolution so live operations start from reliable ground truth.

**Requirements**

- FOUND-02
- LIVE-01
- LIVE-02
- LIVE-03

**Success criteria**

1. Runtime resolves Base, Drive, and Task hints from env/private runtime sources without leaking secrets into repo docs
2. Capability diagnostics clearly distinguish available, degraded, and blocked live states for all required resources
3. Customer resolution succeeds against live 客户主数据 with deterministic handling for ambiguity and missing matches
4. Runtime source handling is documented and regression-tested enough to support day-to-day use

**Depends on**

- Phase 1

**UI hint**: no

### Phase 3: Core Context Recovery

**Goal**

Make core customer context recovery dependable across meeting-related scenes by combining live Base reads, archive routing, and auditable diagnostics.

**Requirements**

- LIVE-04
- WORK-01
- WORK-03
- MEET-01
- MEET-02

**Success criteria**

1. Meeting/post-meeting flows execute gateway stages before formal analysis unless an allowed fallback reason is explicit
2. Context recovery pulls the minimum useful set from 客户主数据, 客户联系记录, 行动计划, and archive links for a resolved customer
3. Archive and meeting-note routing reduce false matches and surface duplicate/stale doc risks explicitly
4. Final scene output shows resource status, customer result, context status, used sources, write ceiling, and open questions
5. The semantic contract for the 3 core tables remains small, live-backed, and aligned with code/tests

**Depends on**

- Phase 2

**UI hint**: no

**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md - Lock the typed recovery contract and gateway-first three-core-table context path
- [x] 03-02-PLAN.md - Add constrained archive/meeting-note routing and confidence-aware audit output

### Phase 4: Unified Safe Writes

**Goal**

Strengthen write-candidate normalization, preflight, guard behavior, and Todo execution so the current mutation path is robust enough to trust.

**Requirements**

- MEET-03
- WRITE-01
- WRITE-02
- WRITE-03

**Success criteria**

1. Meeting flows emit normalized Todo candidates with explicit `operation`, `match_basis`, `source_context`, and `target_object`
2. Schema preflight and write guard are mandatory gates for all write-ready paths
3. Todo writer reliably returns normalized results with dedupe decisions, blocked reasons, and remote metadata
4. High-risk customer master updates remain recommendation-only unless safety and confidence requirements are satisfied

**Depends on**

- Phase 3

**UI hint**: no

### Phase 5: Expanded Account Model

**Goal**

Bring the broader customer operating model into active use by safely incorporating contracts, key people, and competitor structures.

**Requirements**

- WORK-02

**Success criteria**

1. Contracts, key people, and competitor tables have stable read profiles used by relevant scenes without full-schema mirroring
2. New targeted-read paths stay aligned with archive and customer context rather than becoming isolated data pulls
3. Expansion does not regress current meeting and Todo flows or inflate prompt/runtime complexity beyond the minimal semantic contract rule

**Depends on**

- Phase 3
- Phase 4

**UI hint**: no

### Phase 6: Validation And Portability

**Goal**

Keep the project trustworthy and portable while capabilities expand, using repeatable validation and host-agnostic operating logic.

**Requirements**

- FOUND-03
- VAL-01
- VAL-02
- PORT-01

**Success criteria**

1. Validation assets cover representative AM scenarios with executable assertions and release-ready evidence
2. Regression tests protect critical live-first, fallback, dedupe, and context-recovery behaviors
3. Skill operating rules remain consistent across repo docs, runtime behavior, and supported agent hosts
4. Host-specific integration details stay outside the core account-operating model so Hermes/OpenClaw/Codex usage can share one project core

**Depends on**

- Phase 4
- Phase 5

**UI hint**: no

### Phase 7: Skill Architecture For Scene Expansion

**Goal**

Define and lock a long-term extensible skill architecture so `feishu-am-workbench` can grow from one entry skill into a main-skill plus scene-skill system with on-demand expert agents, shared Feishu foundation capabilities, and safe bootstrap/cache extensions.

**Requirements**

- ARCH-01
- ARCH-02
- ARCH-03
- ARCH-04

**Success criteria**

1. The repo has a clear architecture contract for four layers: main skill, scene skills, expert agents, and runtime foundation capabilities
2. Scene-skill boundaries are defined by AM scenarios and workflows rather than raw Feishu tables
3. The design covers bootstrap or install behavior, workspace compatibility checks, and required local config boundaries without weakening live-first rules
4. The design defines how schema cache, manifest or index cache, and semantic or ontology cache can reduce API calls while remaining subordinate to live truth

**Depends on**

- Phase 6

**UI hint**: no

**Plans:** 3 plans

Plans:
- [x] 07-01-PLAN.md - Lock the four-layer architecture contract, first-wave scene boundaries, and expert-agent handoff model
- [x] 07-02-PLAN.md - Define the separate bootstrap/admin contract and subordinate cache governance model
- [x] 07-03-PLAN.md - Wire the Phase 7 packaging model into README, loading strategy, and reference indexing

## Dependency Notes

- Phase 1 is foundational and already completed by this initialization pass.
- Phase 2 must precede any substantial broadening of scene behavior.
- Phase 3 and Phase 4 form the core trust loop: recover context correctly, then write safely.
- Phase 5 should not outrun the protections established in Phases 2-4.
- Phase 6 runs throughout, but its formal completion depends on the earlier phases maturing.
- Phase 7 should consolidate the next-generation skill packaging and bootstrap model only after the current trust loop and portability baseline are explicit enough to support it.

## Backlog

### Phase 999.1: Follow-up — Phase 1 incomplete discussion artifacts (BACKLOG)

**Goal:** Resolve Phase 1 discussion artifacts that never went through formal phase planning
**Source phase:** 1
**Deferred at:** 2026-04-16 during /gsd-next advancement to Phase 4
**Plans:**
- [ ] 01: Brownfield Baseline discussion/context exists without PLAN.md

## Recommended Next Step

Proceed with `/gsd-execute-phase 7` once Phase 6 dependencies are in a state you are comfortable planning against, or resume `/gsd-discuss-phase 4` if you want to continue roadmap order strictly.

---
*Roadmap created: 2026-04-14 after brownfield GSD initialization*