# Phase 17: Post-Meeting And Todo Expert Upgrade - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Upgrade post-meeting synthesis and Todo follow-on from generic summaries into customer-operating judgments with typed action recommendations and expert rationale. This phase delivers CORE-02, TODO-01, and TODO-02 on top of the Phase 16 expert-analysis foundation.

**What this phase delivers:**
- Post-meeting output with fixed sections: risks, opportunities, stakeholder changes, next-round推进 path
- Todo candidates classified by customer-operating intent with expert rationale preceding each candidate
- Confirmed writes still go through the existing unified writer path (no new write path introduced)

**What this phase does NOT add:**
- New scene capabilities beyond post-meeting and Todo follow-on
- Automatic writes without confirmation
- Changes to the SceneResult contract established in Phase 12/16

</domain>

<decisions>
## Implementation Decisions

### Post-Meeting Output Format
- **D-01:** Output uses structured list format (2-5 bullet points per section) — concise and scannable for AM workflow pace
- **D-02:** Four fixed sections required: 风险 (risks), 机会 (opportunities), 干系人变化 (stakeholder changes), 下一轮推进路径 (next-round advancement path)
- **D-03:** Each section contains named, scannable items rather than dense narrative paragraphs
- **D-04:** "下一轮推进" section may use short sentences rather than bullet lists, as it represents action sequences not analysis

### Todo Intent Classification
- **D-05:** Four fixed intent categories: 风险干预, 扩张推进, 关系维护, 项目进展
- **D-06:** These four categories cover the majority of AM work — additional categories may be added when actual cases don't fit these four
- **D-07:** New category creation: either user manually specifies a tag OR the system (expert analysis helper) auto-infers a new category — both are acceptable
- **D-08:** Classification is stored in a structured field, not just human-readable text

### Expert Rationale Storage
- **D-09:** Expert rationale is stored in a structured field (中文命名), not only displayed as human-readable text
- **D-10:** Rationale field name: use Chinese (e.g., 判定理由 or similar)
- **D-11:** Rationale serves both purposes: readable for immediate user comprehension AND structured for downstream traceability and reuse

### Technical Boundary (carried forward from Phase 15/16)
- **D-12:** Todo writes still route through the existing unified writer path — no new write path introduced
- **D-13:** ExpertAnalysisHelper does assembly/combination only; specific judgment decisions remain at the scene layer (from Phase 16 D-04)
- **D-14:** SceneResult contract unchanged: scene_name, resource_status, customer_status, context_status, used_sources, facts, judgments, open_questions, recommendations, fallback_category, fallback_reason, fallback_message, write_ceiling, output_text (from Phase 12/16)
- **D-15:** Fallback visibility preserved when sources are missing — output honestly annotates what was used and what was missing (from Phase 16 D-06-D-09)

### Expert's Discretion
- Exact bullet count per section (D-02 allows flexibility within 2-5 range)
- Exact internal field name for intent classification, as long as structured and traceable
- Exact format of the structured rationale field (paragraph vs. list vs. key-value pairs) — scene layer decides
- How to handle cases where a Todo spans multiple intent categories

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 16 foundation (prerequisite)
- `.planning/phases/16-expert-analysis-foundation-and-multi-source-evidence/16-CONTEXT.md` — EvidenceContainer, ExpertAnalysisHelper, fallback preservation rules, D-04/D-05 scene-layer judgment principle
- `runtime/expert_analysis_helper.py` — existing assembly/combination logic that Phase 17 will extend, not replace

### Scene runtime contract (unchanged)
- `runtime/scene_runtime.py` — SceneRequest/SceneResult contract, run_post_meeting_scene(), run_todo_capture_and_update_scene() — Phase 17 upgrades these, not replaces
- `runtime/scene_registry.py` — scene dispatch mechanism
- `runtime/models.py` — shared runtime data shapes

### Prior scene implementations
- `.planning/phases/13-canonical-post-meeting-scene-runtime/13-CONTEXT.md` — existing post-meeting scene closure
- `.planning/phases/15-archive-and-todo-scene-expansion-closure/15-CONTEXT.md` — Todo write path boundary rules

### Requirements
- `.planning/REQUIREMENTS.md` — CORE-02 (post-meeting fixed sections), TODO-01 (intent classification), TODO-02 (expert rationale) are the primary requirements
- `.planning/ROADMAP.md` — Phase 17 goal, success criteria, dependency on Phase 16

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_post_meeting_scene()` in `runtime/scene_runtime.py` — already returns facts, judgments, recommendations; Phase 17 upgrades to add structured sections
- `run_todo_capture_and_update_scene()` in `runtime/scene_runtime.py` — already builds WriteExecutionCandidates; Phase 17 adds intent classification and rationale
- `build_meeting_output_artifact()` in `evals/meeting_output_bridge.py` — produces output text; needs extension for structured sections
- `EvidenceContainer` and `ExpertAnalysisHelper` in `runtime/expert_analysis_helper.py` — Phase 16 foundation to build on

### Established Patterns
- Scene results always distinguish facts, judgments, and action proposals
- Write operations go through schema preflight, guard, and writer — unchanged in Phase 17
- Live systems are truth; cached/inferred material is secondary

### Integration Points
- New structured sections plug into the existing post-meeting scene result output
- Intent classification and rationale fields extend the existing WriteExecutionCandidate payload
- Existing unified Todo writer path handles confirmed writes

</code_context>

<specifics>
## Specific Ideas

- Four intent category names are final: 风险干预, 扩张推进, 关系维护, 项目进展
- Rationale field should use Chinese naming
- Category extension can be either manual user tag or auto-inferred by system — both acceptable

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within Phase 17 scope

</deferred>

---

*Phase: 17-post-meeting-and-todo-expert-upgrade*
*Context gathered: 2026-04-17*
