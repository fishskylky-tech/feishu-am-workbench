# Requirements: Feishu AM Workbench

**Defined:** 2026-04-17
**Milestone:** v1.2 Expert Customer Operating Scenes
**Core Value:** Use one live-first, safety-first skill to turn AM inputs into actionable customer operating context and guarded write plans inside the existing Feishu workbench.

## Milestone Focus

Turn the current executable scene runtime surface into a more professional customer-operating workbench by adding expert analysis, multi-source evidence fusion, stronger durable-output routing, and the next three high-value AM scenes: cohort scanning, meeting prep, and proposal/report/resource coordination.

## Requirements

### Expert-Augmented Core Scenes

- [x] **CORE-01**: User can run post-meeting synthesis on transcript plus recovered history, customer archive, and optional external materials as one evidence bundle before judgment is generated
- [x] **CORE-02**: User receives post-meeting output with fixed customer-operating sections for risks, opportunities, stakeholder changes, and next-round推进 path instead of a generic summary only
- [x] **TODO-01**: User receives follow-on Todo recommendations classified by customer-operating intent, including risk intervention, expansion push, relationship maintenance, and project progression
- [x] **TODO-02**: User can review expert rationale before any Todo candidate is proposed for write-back
- [x] **STAT-01**: User can query one customer and receive a current account-posture readout structured into risk, opportunity, relationship, and project-progress lenses — Phase 18 ✅
- [x] **ARCH-01**: User receives archive refresh recommendations as a structured customer-history synthesis covering historical arc, key people, risks, opportunities, and operating posture instead of a loose refresh note — Phase 19 ✅

### New Customer-Operating Scenes

- [x] **SCAN-01**: User can ask for a class of customers and receive grouped risk, opportunity, and common-issue analysis without requiring a fully automatic巡检系统 — Phase 18 ✅
- [x] **PREP-01**: User can request meeting prep with customer name, meeting information, and an optional target, and receive a recommendation-first prep brief containing current status, key people, objectives, risks, opportunities, suggested questions, and suggested next steps — Phase 19 ✅
- [x] **PROP-01**: User can request proposal, reporting, or resource-coordination support with customer, goal, and multiple materials, and receive a structured draft that includes objective, core judgment, main narrative, resource asks, and open questions — Phase 20 ✅

### Output Routing, Safety, And Verification

- [x] **WRITE-01**: User sees Feishu-native durable-output targets proposed by default for prep, archive, proposal, and reporting artifacts rather than the local workspace being treated as the default sink — Phase 20 ✅
- [x] **WRITE-02**: User sees an explicit confirmation checklist for durable expert outputs, including audience, purpose, external/internal use, resource-coordination need, and whether the result should update action plans or archives — Phase 19 ✅
- [x] **SAFE-02**: All expert-augmented and newly added scenes remain live-first, recommendation-first, and guarded-write, with explicit fallback visibility when context or permissions are partial
- [x] **VAL-05**: Regression coverage demonstrates upgraded and new scene behavior across happy-path, limited-context, unresolved-customer, and blocked-write cases at the scene-contract level — Phase 21 ✅

## Future Requirements

- [ ] **OPS-01**: Produce weekly or monthly operating summaries across the customer portfolio
- [ ] **OPS-02**: Add proactive reminders or triggers for risk, renewal, and opportunity changes
- [ ] **SCAN-02**: Add scheduled or semi-automatic customer scanning beyond user-triggered analytical entrypoints

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full automatic customer巡检 or scheduled reporting in v1.2 | The milestone should first validate on-demand analytical entrypoints before adding proactive cadence and automation |
| Automatic archive, document, or master-data writes without confirmation | Violates the project safety model |
| Bootstrap/admin operator-path execution as the mainline theme for v1.2 | Lower leverage than customer-operating scene depth for the current milestone |
| Generic local-workspace document output as the preferred durable destination | Conflicts with the Feishu workbench operating model highlighted by issue feedback |

## Traceability

| Requirement | Planned Phase | Status |
|-------------|---------------|--------|
| CORE-01 | Phase 16 | shipped ✅ |
| CORE-02 | Phase 17 | shipped ✅ |
| TODO-01 | Phase 17 | shipped ✅ |
| TODO-02 | Phase 17 | shipped ✅ |
| STAT-01 | Phase 18 | shipped ✅ |
| ARCH-01 | Phase 19 | shipped ✅ |
| SCAN-01 | Phase 18 | shipped ✅ |
| PREP-01 | Phase 19 | shipped ✅ |
| PROP-01 | Phase 20 | shipped ✅ |
| WRITE-01 | Phase 20 | shipped ✅ |
| WRITE-02 | Phase 19 | shipped ✅ |
| SAFE-02 | Phase 16 | shipped ✅ |
| VAL-05 | Phase 21 | shipped ✅ |

## Archived Requirement Sets

- v1.1 archive: [.planning/milestones/v1.1-REQUIREMENTS.md](.planning/milestones/v1.1-REQUIREMENTS.md)
- v1.0 archive: [.planning/milestones/v1.0-REQUIREMENTS.md](.planning/milestones/v1.0-REQUIREMENTS.md)

---
*Requirements defined on 2026-04-17 for milestone v1.2*