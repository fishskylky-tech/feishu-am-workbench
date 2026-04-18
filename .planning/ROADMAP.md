# Roadmap: Feishu AM Workbench

**Created:** 2026-04-17
**Milestone:** v1.2 Expert Customer Operating Scenes
**Mode:** Interactive
**Granularity:** Standard
**Execution:** Parallel where dependencies allow

## Summary

v1.2 shifts the project from "scene surfaces are executable" to "scene outputs feel like a customer-operating expert workbench". The milestone deepens four shipped scenes and adds three new recommendation-first scenes without weakening live-first and guarded-write boundaries.

**5 active phases** | **13 requirements mapped** | **2 archived milestones** | **1 optional backlog item outside mainline**

## Current Planning State

- Active mainline milestone: v1.2 Expert Customer Operating Scenes
- The most recent shipped milestone is v1.1 Executable Scene Runtimes.
- Backlog Phase 999.1 remains optional historical cleanup and does not block v1.2 mainline execution.

## Active Milestone

### Phase 16: Expert Analysis Foundation And Multi-Source Evidence

**Goal:** Add the reusable expert-analysis and evidence-fusion substrate that upgraded scenes will depend on.
**Depends on:** v1.1 archived milestone outputs
**Requirements:** CORE-01, SAFE-02

**Success criteria:**
1. Scene runtime can assemble multi-source evidence bundles from transcript, recovered context, archive materials, and optional external inputs without bypassing current gateway and guard boundaries.
2. Expert-analysis orchestration is explicit at the scene layer rather than hidden inside foundation defaults.
3. Scene results preserve fallback visibility when one or more evidence sources are unavailable.
4. Safety rules remain live-first, recommendation-first, and guarded-write after the expert-analysis layer is introduced.

**Plans:** 3/3 plans complete
**Status:** shipped 2026-04-17

Plans:
- [x] 16-01-PLAN.md — EvidenceContainer model and ExpertAnalysisHelper utility module
- [x] 16-02-PLAN.md — Refactor scene implementations to use EvidenceContainer and ExpertAnalysisHelper
- [x] 16-03-PLAN.md — Verify registry dispatch and add tests for evidence assembly and fallback behavior

### Phase 17: Post-Meeting And Todo Expert Upgrade

**Goal:** Upgrade post-meeting synthesis and Todo follow-on from structured summaries into customer-operating judgments with typed action recommendations.
**Depends on:** Phase 16
**Requirements:** CORE-02, TODO-01, TODO-02
**Status:** shipped 2026-04-17

**Success criteria:**
1. Post-meeting output contains explicit sections for risks, opportunities, stakeholder changes, and next-round推进 path.
2. Todo follow-on recommendations are classified by customer-operating intent rather than emitted as generic tasks.
3. Todo candidates are preceded by expert rationale that explains why each action matters.
4. Confirmed Todo writes still run through the existing unified writer path.

Plans:
- [x] 17-01-PLAN.md — Post-meeting four-section output and Todo intent classification
- [x] 17-02-PLAN.md — Expert rationale for Todo candidates
- [x] 17-03-PLAN.md — Todo writer upgrade with dedupe
- [x] 17-04-PLAN.md — Regression tests

### Phase 18: Account Posture And Cohort Scanning

**Goal:** Make recent-status analysis more decision-ready for a single account and add the first user-triggered cohort analysis scene.
**Depends on:** Phase 16
**Requirements:** STAT-01, SCAN-01
**Status:** shipped 2026-04-17

**Success criteria:**
1. Single-customer recent-status output uses fixed lenses for risk, opportunity, relationship, and project progress.
2. User can request a class of customers and receive grouped signals, common issues, and suggested actions without invoking a full auto-scanner.
3. Cohort analysis remains recommendation-first and clearly scoped to analytical output.

Plans:
- [x] 18-01-PLAN.md — Four-lens account posture (STAT-01) implementation
- [x] 18-02-PLAN.md — Cohort scan scene (SCAN-01) implementation

### Phase 19: Archive Refresh And Meeting Prep Paths

**Goal:** Turn archive refresh into a structured archive-update path and add the first recommendation-first meeting prep scene.
**Depends on:** Phase 16, Phase 18
**Requirements:** ARCH-01, PREP-01, WRITE-02
**Status:** shipped 2026-04-17

**Success criteria:**
1. Archive refresh output proposes canonical archive updates around customer history, key people, risk, opportunity, and operating posture.
2. Meeting prep produces a reusable brief with current status, key people, objectives, risks, opportunities, suggested questions, and suggested next steps.
3. Durable outputs in these scenes present an explicit confirmation checklist before any write plan is executed.

**Plans:** 3/3 plans complete

### Phase 20: Proposal, Reporting, And Resource Coordination

**Goal:** Add a structured scene for proposal/report generation and resource-coordination support with Feishu-native output routing.
**Depends on:** Phase 16, Phase 19
**Requirements:** PROP-01, WRITE-01
**Status:** shipped 2026-04-18

**Success criteria:**
1. User can provide customer, goal, and multiple materials and receive a structured proposal/report/resource-coordination draft.
2. Outputs include objective, core judgment, main narrative, resource asks, and open questions rather than summary text only.
3. Default durable-output routing points to Feishu-native destinations and can be linked back into customer-operating context.

**Plans:** 3/3 plans complete

Plans:
- [x] 20-01-PLAN.md — Core proposal scene infrastructure: build_proposal_checklist(), run_proposal_scene(), scene registry
- [x] 20-02-PLAN.md — Feishu-native output routing: type-based routing, routing payload, destination inference
- [x] 20-03-PLAN.md — Testing: test_proposal_scene.py with five-dimension, type-emphasis, checklist, and routing tests

### Phase 21: Validation And Milestone Closure

**Goal:** Lock the upgraded and new scenes with regression evidence, documentation alignment, and milestone closeout readiness.
**Depends on:** Phase 17, Phase 18, Phase 19, Phase 20
**Requirements:** VAL-05
**Status:** shipped 2026-04-18

**Success criteria:**
1. Regression coverage exists for happy-path, limited-context, unresolved-customer, and blocked-write cases across the upgraded and new scenes at the scene-contract level.
2. Root docs and validation guidance describe the new scene surfaces, expert-output boundaries, and durable-output routing rules accurately.
3. Requirements traceability is complete and milestone closeout can be audited without relying on undocumented behavior.

Plans:
- [x] 21-01-PLAN.md — Regression tests: post-meeting, customer-recent-status, archive-refresh
- [x] 21-02-PLAN.md — Regression tests: cohort-scan, meeting-prep, proposal
- [x] 21-03-PLAN.md — Documentation updates: scene-runtime-contract, scene-skill-architecture, SKILL.md, VALIDATION.md
- [x] 21-04-PLAN.md — README, CHANGELOG, VERSION, ROADMAP completion
- [x] 21-05-PLAN.md — Milestone closeout: audit, archives, traceability, regression report

## Archived Milestones

### v1.1: Executable Scene Runtimes

- Status: shipped 2026-04-17
- Phases: 12-15 complete
- Archive: [.planning/milestones/v1.1-ROADMAP.md](.planning/milestones/v1.1-ROADMAP.md)
- Requirements: [.planning/milestones/v1.1-REQUIREMENTS.md](.planning/milestones/v1.1-REQUIREMENTS.md)
- Audit: [.planning/v1.1-MILESTONE-AUDIT.md](.planning/v1.1-MILESTONE-AUDIT.md)
- Summary: scene runtime contract is now executable and archived as a shipped milestone, not an active mainline roadmap

### v1.0: Milestone

- Status: shipped 2026-04-16
- Phases: 1-11 complete
- Archive: [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md)
- Requirements: [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md)
- Audit: [.planning/v1.0-MILESTONE-AUDIT.md](.planning/v1.0-MILESTONE-AUDIT.md)

## Backlog

### Phase 999.1: Follow-up — Phase 1 incomplete discussion artifacts (BACKLOG)

**Goal:** Optional historical metadata cleanup for earlier Phase 1 discussion wording; not a mainline delivery phase
**Source phase:** 1
**Deferred at:** 2026-04-16 during /gsd-next advancement to Phase 4
**Status:** Non-blocking and outside v1.1 closeout scope
**Plans:**
3/3 plans complete

## Recommended Next Step

Start execution with `/gsd-execute-phase 21`, or optionally execute backlog cleanup via `/gsd-plan-phase 999.1` outside the v1.2 mainline.
