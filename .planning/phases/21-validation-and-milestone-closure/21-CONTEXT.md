# Phase 21: Validation And Milestone Closure - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Lock the upgraded and new scenes with regression evidence, documentation alignment, and milestone closeout readiness. This phase delivers VAL-05 on top of the Phase 16-20 expert-analysis and new-scene foundation.

**What this phase delivers:**
- Regression coverage for 6 scenes × 4 case types (happy-path, limited-context, unresolved-customer, blocked-write) at scene-contract level
- Documentation alignment: scene-runtime-contract, scene-skill-architecture, SKILL.md, README.md, CHANGELOG.md, VERSION, VALIDATION.md
- v1.2 milestone closeout artifacts with extended structure (audit + traceability matrix + regression report)

**What this phase does NOT add:**
- New scene capabilities
- Changes to existing scene behavior
- Changes to the SceneResult contract

</domain>

<decisions>
## Implementation Decisions

### Regression Coverage Strategy (VAL-05)
- **D-01:** Full matrix coverage: 6 scenes × 4 case types = 24 primary coverage paths
- **D-02:** Scene list in scope:
  1. `post-meeting-synthesis` — upgraded in Phase 17 (four-section output, Todo with intent classification)
  2. `customer-recent-status` — upgraded in Phase 18 (four-lens account posture)
  3. `archive-refresh` — upgraded in Phase 19 (five-dimension structured output)
  4. `cohort-scan` — new in Phase 18
  5. `meeting-prep` — new in Phase 19
  6. `proposal` — new in Phase 20
- **D-03:** Case type definitions:
  - happy-path: all context available, customer resolved, write-able
  - limited-context: partial evidence sources, scene still produces output with fallback visibility
  - unresolved-customer: customer not found or ambiguous, scene handles gracefully
  - blocked-write: write guard blocks, scene outputs recommendation without write

### Test Organization
- **D-04:** Per-scene files in `tests/` — each scene gets its own test file (new or expanded), covering all 4 case types within that file
- **D-05:** Pattern: `test_post_meeting_scene.py`, `test_customer_recent_status_scene.py`, `test_archive_refresh_scene.py` (already exists, expand), `test_cohort_scan_scene.py` (already exists, expand), `test_meeting_prep_scene.py` (already exists, expand), `test_proposal_scene.py` (already exists, expand)
- **D-06:** Tests are scene-contract level: verify dispatch succeeds, result shape is correct, fallback behavior is correct, write boundaries are respected — not full integration tests

### Documentation Alignment Scope
- **D-07:** Update all of the following:
  - `references/scene-runtime-contract.md` — add cohort-scan, meeting-prep, proposal scene registrations
  - `references/scene-skill-architecture.md` — sync scene list with 7 scenes
  - `SKILL.md` — update scene capabilities description to reflect v1.2 additions
  - `README.md` — v1.2 value narrative from business perspective; version 1.2.0; minimize technical barriers for non-technical readers
  - `CHANGELOG.md` — v1.2 changes from business value perspective; minimize jargon
  - `VERSION` — 1.2.0
  - `VALIDATION.md` — update scene descriptions to reflect upgraded/new scenes

### ROADMAP Phase Completion Status
- **D-08:** ROADMAP.md 各 phase 需补充完成状态：Phase 16-20 shipped 日期，Phase 21 当前状态；确保可以看到路线进度全景

### Milestone Closeout Structure (Extended v1.1)
- **D-09:** Create `v1.2-MILESTONE-AUDIT.md` — milestone audit following v1.1 pattern: requirements satisfaction, phase verification coverage, integration findings, e2e flow findings
- **D-10:** Create `v1.2-ROADMAP.md` — archived copy of v1.2 roadmap at closeout
- **D-11:** Create `v1.2-REQUIREMENTS.md` — archived copy of v1.2 requirements at closeout
- **D-12:** Update `.planning/MILESTONES.md` — add v1.2 entry with link to audit
- **D-13:** Create VAL-05 traceability matrix — scene × case-type × test coverage evidence
- **D-14:** Regression test run report — summary of all per-scene test results

### README/CHANGELOG Writing Style
- **D-15:** README and CHANGELOG are written from business scenario and value perspective, not implementation detail
- **D-16:** Non-technical readers can understand what v1.2 enables and why it matters

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 16-20 context (what was built)
- `.planning/phases/16-expert-analysis-foundation-and-multi-source-evidence/16-CONTEXT.md` — EvidenceContainer, ExpertAnalysisHelper, fallback preservation
- `.planning/phases/17-post-meeting-and-todo-expert-upgrade/17-CONTEXT.md` — post-meeting four-section output, Todo intent classification
- `.planning/phases/18-account-posture-and-cohort-scanning/18-CONTEXT.md` — four-lens STAT-01, cohort-scan SCAN-01
- `.planning/phases/19-archive-refresh-and-meeting-prep-paths/19-CONTEXT.md` — archive-refresh five-dimension, meeting-prep, WRITE-02 checklist
- `.planning/phases/20-proposal-reporting-and-resource-coordination/20-CONTEXT.md` — proposal scene, five-dimension output, WRITE-01 routing

### Scene runtime contract
- `runtime/scene_registry.py` — 7 registered scenes; Phase 21 regression tests target this dispatch contract
- `runtime/scene_runtime.py` — SceneRequest/SceneResult contract; unchanged by Phase 21

### v1.1 milestone pattern (reference for closeout structure)
- `.planning/v1.1-MILESTONE-AUDIT.md` — v1.1 audit pattern to extend for v1.2

### Requirements
- `.planning/REQUIREMENTS.md` — VAL-05 is the primary requirement: "Regression coverage demonstrates upgraded and new scene behavior across happy-path, limited-context, unresolved-customer, and blocked-write cases at the scene-contract level"
- `.planning/ROADMAP.md` — Phase 21 goal, success criteria, dependency on Phase 17-20

### Existing test files (to expand)
- `tests/test_proposal_scene.py` — existing 25 tests; expand to cover 4 case types
- `tests/test_meeting_prep_scene.py` — existing tests; expand to cover 4 case types
- `tests/test_cohort_scan.py` — existing tests; expand to cover 4 case types
- `tests/test_archive_refresh_scene.py` — existing tests; expand to cover 4 case types
- `tests/test_scene_runtime.py` — post-meeting and customer-recent-status tests; expand for 4 case types

### Documentation to update
- `references/scene-runtime-contract.md` — add new scene registrations
- `references/scene-skill-architecture.md` — sync scene list
- `SKILL.md` — update scene capabilities
- `README.md` — v1.2 value narrative, version 1.2.0
- `CHANGELOG.md` — v1.2 business-value changelog
- `VERSION` — 1.2.0
- `VALIDATION.md` — update scene descriptions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 20 `test_proposal_scene.py` with 25 tests — expand for 4 case types
- Phase 19 `test_meeting_prep_scene.py`, `test_archive_refresh_scene.py` — expand for 4 case types
- Phase 18 `test_cohort_scan.py` — expand for 4 case types
- `tests/test_scene_runtime.py` — post-meeting and customer-recent-status scene tests; expand for 4 case types
- v1.1 `v1.1-MILESTONE-AUDIT.md` — pattern for milestone closeout structure

### Established Patterns
- Scene-contract level testing: verify dispatch, result shape, fallback behavior, write boundaries — not full integration
- Per-scene test files: consistent with existing test organization
- Fallback behavior already tested in v1.1; Phase 21 extends to cover all 6 upgraded/new scenes

### Integration Points
- All 6 scenes share the same `dispatch_scene()` entry and `SceneResult` contract
- Regression tests target the scene registry dispatch, not internal implementation

</code_context>

<specifics>
## Specific Ideas

- README and CHANGELOG should read like a product changelog for a business tool, not a dev changelog — focus on what the AM can now do that they couldn't before
- ROADMAP phase completion status should be visible at a glance — use shipped dates and status chips

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 21 scope.

</deferred>

---

*Phase: 21-validation-and-milestone-closure*
*Context gathered: 2026-04-18*
