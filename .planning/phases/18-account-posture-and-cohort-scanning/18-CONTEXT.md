# Phase 18: Account Posture And Cohort Scanning - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Make recent-status analysis more decision-ready for a single account (STAT-01) and add the first user-triggered cohort analysis scene (SCAN-01) on top of the Phase 16 expert-analysis foundation.

**What this phase delivers:**
- STAT-01: Single-customer recent-status output uses fixed lenses for risk, opportunity, relationship, and project-progress
- SCAN-01: User can request a class of customers and receive grouped signals, common issues, and suggested actions
- Both remain recommendation-first and analytical (not scheduled auto巡检)

**What this phase does NOT add:**
- Automatic writes without confirmation
- Scheduled or proactive scanning
- Changes to the SceneResult contract established in Phase 12/16

</domain>

<decisions>
## Implementation Decisions

### Account Posture Lenses (STAT-01)
- **D-01:** Four-lens output (risk/机会, opportunity/机会, relationship/关系, project-progress/进展) presented as labeled sub-items within the judgments field — each lens produces 1-3 scannable conclusions
- **D-02:** STAT-01 implemented as an upgrade to the existing `customer-recent-status` scene — not a new standalone scene — reusing the existing scene function and adding four-lens lens output

### Cohort Definition (SCAN-01)
- **D-03:** User defines the cohort via dynamic condition query (e.g., "customers with activity in last 3 months") — natural language description interpreted into filter criteria
- **D-04:** Cohort scan limit is configurable with a default of 10 customers; when the result set exceeds the limit, the user is prompted to narrow the scope rather than producing bloated output

### Cohort Output Structure (SCAN-01)
- **D-05:** Cohort output uses an "aggregated summary + key customers" structure:
  - Aggregated layer: 2-3 common signals, 2-3 common issues across the cohort
  - Individual layer: 3-5 customers flagged as highest risk or biggest opportunity
- **D-06:** Each customer's individual entry follows the same four-lens framing (risk, opportunity, relationship, project-progress) when surfaced in the cohort context

### Cohort Recommendations (SCAN-01)
- **D-07:** Recommendations come in two tiers:
  - Cohort-level recommendations addressing common issues and shared signals (1-3 items)
  - Per-customer individual follow-up recommendations for key flagged customers (1-2 per customer)
- **D-08:** Total recommendation count capped at ~10 to keep output actionable rather than overwhelming

### Technical Boundary (carried forward from Phase 16/17)
- **D-09:** ExpertAnalysisHelper stays thin — assembly/combination only; lens assignment and judgment remain at the scene layer
- **D-10:** EvidenceContainer tracks source evidence per lens — each lens draws from relevant sources (e.g., relationship lens draws from contact logs, key people; project-progress lens draws from tasks, meeting notes)
- **D-11:** SceneResult contract unchanged — scene continues to return facts, judgments, recommendations, fallback_category, write_ceiling
- **D-12:** Cohort scanning is user-triggered analytical entry, NOT a scheduled automatic巡检 system — confirmed from STATE.md notes

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 16 foundation (prerequisite)
- `.planning/phases/16-expert-analysis-foundation-and-multi-source-evidence/16-CONTEXT.md` — EvidenceContainer, ExpertAnalysisHelper, fallback preservation, D-04 scene-layer judgment principle
- `runtime/expert_analysis_helper.py` — existing assembly/combination logic that Phase 18 lens routing extends

### Phase 17 post-meeting structure (template for four-section output)
- `.planning/phases/17-post-meeting-and-todo-expert-upgrade/17-CONTEXT.md` — D-02 four fixed sections for post-meeting (风险, 机会, 干系人变化, 下一轮推进路径) — STAT-01 uses a parallel four-lens structure

### Existing customer-recent-status scene
- `runtime/scene_runtime.py` — `run_customer_recent_status_scene()` — STAT-01 upgrades this, not replaces

### Scene runtime contract (unchanged)
- `runtime/scene_registry.py` — scene dispatch mechanism; new cohort scene registers the same way
- `runtime/models.py` — shared SceneResult/SceneRequest data shapes

### Requirements
- `.planning/REQUIREMENTS.md` — STAT-01 (account-posture lenses) and SCAN-01 (cohort scanning) are the primary requirements
- `.planning/ROADMAP.md` — Phase 18 goal, success criteria, dependency on Phase 16

### State notes
- STATE.md — "Cohort scanning in v1.2 is user-triggered analytical entry, not a scheduled automatic巡检 system" — key constraint confirmed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_customer_recent_status_scene()` in `runtime/scene_runtime.py` — existing scene to be upgraded with four-lens output
- `EvidenceContainer` and `ExpertAnalysisHelper` in `runtime/expert_analysis_helper.py` — Phase 16 foundation for multi-source evidence
- `scene_registry.py` — scene registration mechanism for the new cohort scene

### Established Patterns
- Four-section output pattern from Phase 17 (风险, 机会, 干系人变化, 下一轮推进路径) — STAT-01 uses parallel lens framing
- Structured Chinese field naming from Phase 17
- Recommendation-first with explicit confirmation before writes

### Integration Points
- New `run_cohort_scan_scene()` registers alongside existing scene dispatch
- Four-lens EvidenceContainer routing extends Phase 16 container with lens-aware source tracking
- Cohort scan results route to the same output text and payload structure as other scenes

</code_context>

<specifics>
## Specific Ideas

- Cohort scan is explicitly on-demand, not scheduled — per STATE.md notes
- Four lenses parallel the Phase 17 post-meeting section style but apply to account-level judgment
- Dynamic condition query is the primary cohort definition mechanism — not tag-based or manual selection

</specifics>

<deferred>
## Deferred Ideas

- SCAN-02 (scheduled or semi-automatic customer scanning) — noted in REQUIREMENTS.md as future requirement, out of scope for Phase 18

</deferred>

---

*Phase: 18-account-posture-and-cohort-scanning*
*Context gathered: 2026-04-17*
