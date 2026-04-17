# Phase 19: Archive Refresh And Meeting Prep Paths - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn archive refresh into a structured archive-update path and add the first recommendation-first meeting prep scene. This phase delivers ARCH-01, PREP-01, and WRITE-02 on top of the Phase 16 expert-analysis foundation and Phase 18 account-posture infrastructure.

**What this phase delivers:**
- Archive refresh output with structured five-dimension synthesis: historical arc, key people, risks, opportunities, operating posture
- Meeting prep scene producing a recommendation-first brief: current status, key people, objectives, risks, opportunities, suggested questions, suggested next steps
- Pre-scene confirmation checklist for durable expert outputs (WRITE-02) — intent-driven, scene-specific, minimal-questions principle

**What this phase does NOT add:**
- Automatic writes without confirmation
- Post-meeting synthesis changes (that's Phase 17)
- Proposal/report/resource-coordination scene (that's Phase 20)

</domain>

<decisions>
## Implementation Decisions

### Archive Refresh Output Structure (ARCH-01)
- **D-01:** Five-dimension structured format: 历史弧线 + 关键人物 + 风险 + 机会 + 运营姿态
- **D-02:** Each dimension produces 1-3 scannable conclusions, labeled and readable
- **D-03:** This is a distinct format from Phase 17 (meeting post-mortem) and Phase 18 (account health lenses) — archive refresh is a retrospective synthesis, not an event-driven or health-check view

### Archive Refresh Write-Back Targets
- **D-04:** All applicable Feishu write-back locations are supported: customer archive doc, key people table (Base), action plans (Task), meeting notes folder
- **D-05:** Update proposals use a suggestion + checklist confirmation model — system recommends location and granularity, user confirms
- **D-06:** Update granularity is guided by the pre-scene checklist — user selects from document-level (append section to archive doc), record-level (create/modify key people table entry), or field-level (update specific fields) based on what's appropriate

### Meeting Prep Brief Structure (PREP-01)
- **D-07:** Seven-dimension custom format: 当前状态 + 关键人物 + 目的 + 风险 + 机会 + 建议问题 + 建议后续步骤
- **D-08:** 当前状态 dimension should leverage STAT-01 four-lens output when available — reuse the existing account-posture analysis rather than regenerating it
- **D-09:** Meeting prep is a new standalone scene (not an upgrade to existing scene) — registers as `meeting-prep` in scene registry alongside existing scenes

### Confirmation Checklist Design (WRITE-02)
- **D-10:** Checklist is filled BEFORE the scene executes — intent-driven output generation
- **D-11:** Minimal-questions principle: system prioritizes existing data (EvidenceContainer, recovered context, archive, STAT-01 output) and only asks user for information that is genuinely missing AND critical to output quality
- **D-12:** Checklist is scene-specific, not standardized across scenes

### Archive Refresh Checklist (scene-specific)
- **D-13:** Includes WRITE-02 universal items: audience (受众), purpose (目的), internal/external use (内部/外部), resource-coordination need (是否需要资源协调), whether to update action plans or archives (是否更新行动计划或档案)
- **D-14:** Adds scene-specific item: refresh type (补充历史 vs 校正现有档案)
- **D-15:** Archive location and key people sync questions are system-inferred where possible, surfaced as suggestions for user confirmation rather than requiring user input

### Meeting Prep Checklist (scene-specific)
- **D-16:** Minimal: WRITE-02 universal four items only (audience, purpose, internal/external, resource-coordination)
- **D-17:** Meeting-specific details (meeting type, agenda, prior meeting reference) are inferred from available evidence and surfaced as suggestions — not user input requests

### Technical Boundary (carried forward from Phase 16/17/18)
- **D-18:** ExpertAnalysisHelper stays thin — assembly/combination only; synthesis judgments remain at the scene layer
- **D-19:** EvidenceContainer tracks sources per dimension (e.g., historical arc draws from archive docs, meeting notes; key people draws from key people table)
- **D-20:** SceneResult contract unchanged — scenes continue to return facts, judgments, recommendations, fallback_category, write_ceiling
- **D-21:** No automatic writes — confirmed writes route through existing unified writer path (same as Todo and post-meeting writes)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 16 foundation (prerequisite)
- `.planning/phases/16-expert-analysis-foundation-and-multi-source-evidence/16-CONTEXT.md` — EvidenceContainer, ExpertAnalysisHelper, fallback preservation, D-04 scene-layer judgment principle
- `runtime/expert_analysis_helper.py` — existing assembly/combination logic

### Phase 18 account posture (PREP-01 uses STAT-01 output)
- `.planning/phases/18-account-posture-and-cohort-scanning/18-CONTEXT.md` — four-lens (risk/机会/关系/进展) STAT-01 implementation; D-01-D-02 meeting prep brief should reuse this

### Phase 17 post-meeting structure (parallel to ARCH-01)
- `.planning/phases/17-post-meeting-and-todo-expert-upgrade/17-CONTEXT.md` — D-02 four fixed sections for post-meeting; ARCH-01 uses a distinct five-dimension format (not the same as Phase 17)

### Existing scene implementations
- `runtime/scene_runtime.py` — `run_archive_refresh_scene()` — Phase 19 upgrades this, not replaces
- `runtime/scene_registry.py` — scene dispatch mechanism; new `run_meeting_prep_scene()` registers alongside existing ones
- `runtime/models.py` — shared SceneResult/SceneRequest data shapes

### Requirements
- `.planning/REQUIREMENTS.md` — ARCH-01 (archive refresh structured synthesis), PREP-01 (meeting prep brief), WRITE-02 (confirmation checklist)
- `.planning/ROADMAP.md` — Phase 19 goal, success criteria, dependency on Phase 16 and Phase 18

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_archive_refresh_scene()` in `runtime/scene_runtime.py` — existing scene to be upgraded with five-dimension structured output
- `run_customer_recent_status_scene()` in `runtime/scene_runtime.py` — STAT-01 four-lens output that meeting prep can reuse for 当前状态 dimension
- `EvidenceContainer` and `ExpertAnalysisHelper` in `runtime/expert_analysis_helper.py` — Phase 16 foundation for multi-source evidence
- `scene_registry.py` — scene registration mechanism for the new meeting-prep scene
- Existing Todo and post-meeting write paths — confirmed writes route through these same paths

### Established Patterns
- Pre-scene confirmation checklist (WRITE-02) is new — this is the first phase that implements intent-driven output generation where checklist answers precede scene execution
- Four-dimension (Phase 18) and five-dimension (Phase 19) output formats coexist — distinct by design
- Scene-specific checklist design (not standardized) — each scene has tailored questions
- Suggestion + confirmation model — system recommends, user confirms

### Integration Points
- New `run_meeting_prep_scene()` registers as `meeting-prep` in scene registry
- Archive refresh upgrade: five-dimension output layers on top of existing EvidenceContainer tracking
- Meeting prep: STAT-01 lens output can be called as a subroutine for 当前状态 dimension
- Confirmed writes: both archive refresh and meeting prep route through existing unified writer path (no new write path)

</code_context>

<specifics>
## Specific Ideas

- Archive refresh five-dimension format is intentionally distinct from Phase 17 post-meeting format and Phase 18 account-posture lenses — retrospective synthesis has its own logic
- Minimal-questions principle is important: the system should feel like it already knows your workspace, only asking when it genuinely cannot infer
- Meeting prep 当前状态 should automatically leverage STAT-01 output when the customer has been queried recently — avoid regenerating the same analysis
- WRITE-02 confirmation checklist is a new pattern in Phase 19 that later phases (Phase 20 for PROP-01) will also use — design it so it can be reused with different scene-specific questions

</specifics>

<deferred>
## Deferred Ideas

- PROP-01 (proposal/report/resource-coordination scene) will also use WRITE-02 confirmation checklist — design the checklist infrastructure to be scene-adaptable for Phase 20 reuse
- SCAN-02 (scheduled or semi-automatic customer scanning) — noted in REQUIREMENTS.md as future requirement, out of scope for Phase 19

---

*Phase: 19-archive-refresh-and-meeting-prep-paths*
*Context gathered: 2026-04-17*
