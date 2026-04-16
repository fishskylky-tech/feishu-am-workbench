# Roadmap: Feishu AM Workbench

**Created:** 2026-04-14
**Mode:** Interactive
**Granularity:** Standard
**Execution:** Parallel where dependencies allow

## Summary

This roadmap turns the existing repository from a docs-heavy brownfield into a GSD-managed delivery program rooted in the real Feishu workbench, existing runtime, and validated meeting/Todo path.

**11 phases** | **25 v1 requirements mapped** | Phase 11 closes remaining post-audit cleanup debt

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
| 8 | Audit Evidence And Guidance Alignment | Close audit blockers caused by missing verification metadata, missing phase closure artifacts, and drifted root guidance | FOUND-01, FOUND-02, FOUND-03, FOUND-04, LIVE-01, LIVE-02, LIVE-03, VAL-03, PORT-01 | 4 |
| 9 | Context And Account Verification Closure | Turn Phase 3 and Phase 5 context/account work into milestone-auditable verified capability | LIVE-04, WORK-01, WORK-02, WORK-03, MEET-01, MEET-02 | 4 |
| 10 | Safe Write And E2E Closure | Generalize meeting write candidates and finish the safe-write and validation closure needed for milestone pass | MEET-03, WRITE-01, WRITE-02, WRITE-03, VAL-01, VAL-02 | 4 |
| 11 | Closeout Cleanup For Planning Alignment And Live Write Operator Surface | Remove the last planning drift and promote confirmed-write operation to a first-class runtime entrypoint | FOUND-04, VAL-03, WRITE-02 | 3 |

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

**Plans:** 1 plan

Plans:
# Roadmap: Feishu AM Workbench

## Archived Milestones

### v1.0: Milestone

- Status: shipped 2026-04-16
- Phases: 1-11 complete
- Archive: [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md)
- Requirements: [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md)
- Audit: [.planning/v1.0-MILESTONE-AUDIT.md](.planning/v1.0-MILESTONE-AUDIT.md)

## Backlog

### Phase 999.1: Follow-up — Phase 1 incomplete discussion artifacts (BACKLOG)

**Goal:** Resolve Phase 1 discussion artifacts that never went through formal phase planning
**Source phase:** 1
**Deferred at:** 2026-04-16 during /gsd-next advancement to Phase 4
**Plans:**
- [ ] 01: Brownfield Baseline discussion/context exists without PLAN.md

## Recommended Next Step

Start the next milestone with `/gsd-new-milestone`, or plan backlog Phase 999.1 if you want to clean historical planning artifacts first.