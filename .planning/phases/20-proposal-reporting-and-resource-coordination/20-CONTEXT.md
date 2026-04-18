# Phase 20: Proposal, Reporting, And Resource Coordination - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a structured proposal/report/resource-coordination scene with Feishu-native output routing. This phase delivers PROP-01 and WRITE-01 on top of the Phase 16 expert-analysis foundation, Phase 19 confirmation checklist infrastructure, and Phase 19 meeting-prep scene.

**What this phase delivers:**
- Unified `proposal` scene supporting three types via `proposal_type` parameter: proposal (提案), report (报告), resource-coordination (资源协调)
- Five-dimension structured output: objective, core judgment, main narrative, resource asks, open questions
- Feishu-native durable-output routing by default (Drive docs, Task, or Base tables based on type)
- Pre-scene confirmation checklist (WRITE-02) adapted for proposal scene

**What this phase does NOT add:**
- Agency / autonomous agent behavior — project remains recommendation-first and human-in-the-loop
- Automatic writes without confirmation
- Scheduled or proactive execution
- Changes to the SceneResult contract established in Phase 12/16

</domain>

<decisions>
## Implementation Decisions

### Scene Architecture (PROP-01)
- **D-01:** Single unified `proposal` scene registered in scene registry — three types differentiated by `proposal_type` parameter (proposal / report / resource-coordination), not separate scenes
- **D-02:** Three types share the same input structure (customer + goal + materials) and the same five-section output format, with type-specific emphasis in content depth
- **D-03:** Scene handler: `run_proposal_scene()` registered as `proposal` in scene_registry.py

### Input Materials Assembly
- **D-04:** User explicitly names primary reference materials (e.g., "based on last week's meeting notes" or "reference this proposal draft")
- **D-05:** System auto-supplements relevant context via EvidenceContainer: customer archive, recent contact logs, action plans, key people — same pattern as Phase 19 meeting-prep
- **D-06:** EvidenceContainer presents "I found these materials" before scene execution, user can supplement or confirm scope

### Output Structure (PROP-01)
- **D-07:** Fixed five-section output for all three types:
  1. **Objective（目的）** — 1-2 sentences on the goal of this proposal/report/coordination
  2. **Core Judgment（核心判断）** — 2-4 scannable expert assessments based on provided materials
  3. **Main Narrative（主要叙事）** — structured key arguments built from the materials
  4. **Resource Asks（资源请求）** — what resources, support, or investment is needed (most prominent for resource-coordination type)
  5. **Open Questions（待确认问题）** — unresolved items requiring user or stakeholder confirmation
- **D-08:** Type-specific emphasis: proposal emphasizes core judgment + narrative; report emphasizes narrative; resource-coordination emphasizes resource asks
- **D-09:** Output delivered as structured text + SceneResult.payload, same pattern as Phase 17/18/19

### Expert Judgment Relationship
- **D-10:** PROP-01 "core judgment" reuses ExpertAnalysisHelper for evidence assembly, but judgment logic is implemented independently at the proposal scene layer — not shared with Phase 17/18 judgment frameworks
- **D-11:** Each scene (Phase 17 post-meeting, Phase 18 account-posture, Phase 19 archive/meeting-prep, Phase 20 proposal) has its own judgment logic — shared infrastructure (EvidenceContainer, ExpertAnalysisHelper), independent scene-layer judgment

### Feishu-Native Output Routing (WRITE-01)
- **D-12:** Default routing by proposal type:
  - `proposal` → Drive customer archive folder (new or existing doc under customer folder)
  - `report` → Drive customer archive folder or weekly-report folder
  - `resource-coordination` → Task module or Base 行动计划 table
- **D-13:** Routing is recommendation + confirmation (same as Phase 19 WRITE-02 pattern) — system suggests destination based on type, user confirms or modifies
- **D-14:** WRITE-01 applies to proposal and reporting artifacts — meeting-prep and archive-refresh routing handled in Phase 19

### Confirmation Checklist Design (WRITE-02 adaptation)
- **D-15:** Reuses Phase 19 `confirmation_checklist.py` infrastructure — same `ChecklistItem` and `ConfirmationChecklist` patterns
- **D-16:** Proposal scene checklist: WRITE-02 universal four items (audience, purpose, internal_external, resource_coordination) + scene-specific items
- **D-17:** Scene-specific items (minimum per user choice):
  - `proposal_type` — proposal / report / resource-coordination (determines default output routing)
  - `output_destination` — system-suggested Feishu destination based on type, user confirms
- **D-18:** Minimal-questions principle (Phase 19 D-11): system infers suggestions from EvidenceContainer, user only confirms or modifies — no redundant questions

### No Agency Introduction
- **D-19:** Phase 20 does not introduce agency or autonomous agent behavior — project remains recommendation-first and human-in-the-loop
- **D-20:** Future agency capability would require a dedicated milestone with authority boundaries, safety confirmations, and accountability models — noted as potential future milestone, out of scope for v1.2

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 16 foundation (prerequisite)
- `.planning/phases/16-expert-analysis-foundation-and-multi-source-evidence/16-CONTEXT.md` — EvidenceContainer, ExpertAnalysisHelper, fallback preservation, D-04 scene-layer judgment principle
- `runtime/expert_analysis_helper.py` — existing assembly/combination logic

### Phase 19 confirmation checklist (WRITE-02 infrastructure)
- `.planning/phases/19-archive-refresh-and-meeting-prep-paths/19-CONTEXT.md` — confirmation checklist design, minimal-questions principle, D-10-D-17 checklist item definitions
- `runtime/confirmation_checklist.py` — existing `ChecklistItem`, `ConfirmationChecklist`, `build_archive_refresh_checklist()`, `build_meeting_prep_checklist()` — proposal checklist extends same patterns

### Phase 19 meeting-prep scene (parallel scene)
- `runtime/scene_runtime.py` — `run_meeting_prep_scene()` — Phase 20 proposal scene follows same scene pattern

### Scene runtime contract (unchanged)
- `runtime/scene_registry.py` — scene dispatch mechanism; new `run_proposal_scene()` registers as `proposal`
- `runtime/scene_runtime.py` — SceneRequest/SceneResult contract, existing scene implementations
- `runtime/models.py` — shared runtime data shapes

### Requirements
- `.planning/REQUIREMENTS.md` — PROP-01 (proposal/report/resource-coordination structured draft), WRITE-01 (Feishu-native durable-output routing)
- `.planning/ROADMAP.md` — Phase 20 goal, success criteria, dependency on Phase 16 and Phase 19

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `confirmation_checklist.py` — Phase 19 infrastructure with `ChecklistItem`, `ConfirmationChecklist`, suggestion+confirmation pattern — proposal scene adds `build_proposal_checklist()` following same conventions
- `EvidenceContainer` and `ExpertAnalysisHelper` in `runtime/expert_analysis_helper.py` — Phase 16 foundation for multi-source evidence assembly
- `scene_registry.py` — `build_default_scene_registry()` already has 6 scenes; Phase 20 adds `run_proposal_scene` as 7th
- `run_meeting_prep_scene()` in `runtime/scene_runtime.py` — parallel scene implementation to use as template

### Established Patterns
- Pre-scene confirmation checklist (WRITE-02) already implemented in Phase 19 — proposal scene reuses same infrastructure with scene-specific items
- Five-dimension output format (Phase 19 archive-refresh has 5 dims, Phase 17 post-meeting has 4 sections) — PROP-01's 5-section format is consistent with this pattern
- Suggestion + confirmation model — system recommends routing destination based on type, user confirms or modifies

### Integration Points
- New `run_proposal_scene()` registers as `proposal` in scene registry
- Confirmation checklist calls `build_proposal_checklist()` which extends Phase 19 checklist patterns
- ExpertAnalysisHelper assembles materials into EvidenceContainer before scene execution
- Confirmed writes route through existing unified writer path (same as Todo, post-meeting, archive-refresh writes)

</code_context>

<specifics>
## Specific Ideas

- Proposal scene should feel like a professional report generation tool — structured, scannable, ready to present or send
- Minimal-questions principle is important: the checklist should feel like a quick confirmation, not a long form
- Resource-coordination type's resource asks section should be most prominent — this is the primary deliverable for that type
- Agency/agent capability is out of scope for v1.2 — noted as potential future milestone requiring separate boundary definition

</specifics>

<deferred>
## Deferred Ideas

- **Agency / autonomous agent capability** — discussed but explicitly out of scope for v1.2. Would require dedicated milestone covering authority boundaries, safety confirmations, and accountability models. Noted as potential future consideration.
- **Shared judgment framework across scenes** — user chose scene-independent judgment per Phase 17/18/19/20, so no shared framework needed now. Revisit if scenes converge significantly in future phases.

---

*Phase: 20-proposal-reporting-and-resource-coordination*
*Context gathered: 2026-04-18*
