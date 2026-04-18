# Phase 16: Expert Analysis Foundation And Multi-Source Evidence - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Add the reusable expert-analysis and evidence-fusion substrate that upgraded scenes will depend on. This is the foundation layer for all v1.2 expert-augmented scenes. The foundation must assemble multi-source evidence bundles (transcript + recovered context + archive materials + optional external inputs) without bypassing current gateway and guard boundaries, and make expert-analysis orchestration explicit at the scene layer rather than hidden inside foundation defaults.

Phase 16 does not add new scene capabilities. It establishes the shared infrastructure that Phases 17-20 will build on.

</domain>

<decisions>
## Implementation Decisions

### Evidence Assembly Strategy
- **D-01:** Use a unified EvidenceContainer — all evidence sources are collected into a structured container with source labels, quality indicators, and missing-source flags before being passed to any scene.
- **D-02:** The container provides a consistent interface so scenes do not need to handle raw source heterogeneity (different formats, different quality levels, different availability).

### Expert-analysis Orchestration Location
- **D-03:** Common analysis patterns (multi-source weighting, judgment priority, conflict detection) are extracted into a shared "ExpertAnalysisHelper" — a utility module, not a business-logic black box.
- **D-04:** The helper is kept deliberately thin: it provides assembly and combination logic. Specific judgment decisions (what this evidence means for this customer) remain at the scene layer.
- **D-05:** Scene code must remain readable and self-contained — a developer can read a scene's logic without tracing through deep helper chains.

### Fallback Preservation Rules
- **D-06:** When one or more evidence sources are unavailable, scenes continue to produce output with explicit fallback visibility — results show which sources were used, which were missing, and how that affects confidence.
- **D-07:** Missing-source annotation is honest and actionable: users can see exactly what is missing and decide whether to supplement before acting.
- **D-08:** The write safety boundary is unchanged — even when material is partial, write operations still go through schema preflight, guard, and writer. Partial context never bypasses safety checks.
- **D-09:** When critical sources are missing beyond a defined threshold, the scene should stop with a clear "cannot proceed" message rather than producing misleadingly confident output.

### Scene Result Contract
- **D-10:** All scenes continue to return the standard result shape from Phase 12: facts, judgments, open_questions, recommendations, fallback_category, and write_ceiling.
- **D-11:** Expert-analysis additions layer on top of the existing contract, not replacing it. The existing SceneResult fields remain the canonical interface.

### Carry-forward Decisions from Prior Phases
- **D-12:** Scene results use fixed fields: scene_name, resource_status, customer_status, context_status, used_sources, facts, judgments, open_questions, recommendations, fallback_category, fallback_reason, fallback_message, write_ceiling, output_text (Phase 12).
- **D-13:** Gateway + guard + writer remain the non-bypass shared safety boundary. Expert-analysis layer does not add new write paths.
- **D-14:** Foundation stays thin — scene-specific logic lives at the scene layer, not in the foundation.
- **D-15:** Admin/bootstrap behavior remains outside daily scene execution.

### Expert's Discretion
- Exact naming of the EvidenceContainer class and its fields, as long as source/quality/missing indicators are clearly tracked.
- Exact threshold for "critical source missing" that triggers a hard stop vs a soft warning, as long as the distinction is business-readable.
- Exact internal structure of the ExpertAnalysisHelper, as long as scene code remains readable and self-contained.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scene runtime foundation
- `runtime/scene_runtime.py` — existing SceneRequest/SceneResult contract, four shipped scene implementations (post-meeting-synthesis, customer-recent-status, archive-refresh, todo-capture-and-update), and the standard result field definitions.
- `runtime/scene_registry.py` — existing scene registry and dispatch mechanism that Phase 16 foundation must integrate with.
- `runtime/gateway.py` — existing live-first orchestration boundary that the evidence container and expert-analysis helper must reuse without bypassing.
- `runtime/models.py` — existing shared runtime data shapes that the new EvidenceContainer should extend rather than duplicate.

### Prior phase context
- `.planning/phases/12-scene-runtime-contract-and-boundary-freeze/12-CONTEXT.md` — locked shared result shape, boundary freeze strength, and thin-main-skill decisions that Phase 16 must preserve.
- `.planning/phases/14-customer-recent-status-scene-runtime/14-CONTEXT.md` — existing customer-recent-status scene implementation showing how facts/judgments/recommendations are produced.
- `.planning/phases/15-archive-and-todo-scene-expansion-closure/15-CONTEXT.md` — boundary rules that still apply: no second write path, recommendation-first when safe writer surface unavailable.

### Project requirements
- `.planning/REQUIREMENTS.md` — CORE-01 (multi-source evidence bundle assembly) and SAFE-02 (live-first, recommendation-first, guarded-write with explicit fallback visibility) are the primary requirements Phase 16 satisfies.
- `.planning/ROADMAP.md` — Phase 16 goal, success criteria, and dependency relationship with v1.1 archived milestone outputs.

### Codebase conventions
- `.planning/codebase/CONVENTIONS.md` — recommendation-first, live-first, and facts-vs-judgment conventions that Phase 16 must preserve.
- `references/scene-skill-architecture.md` — canonical first-wave scene list and workflow-shaped scene boundary rules that Phase 16 foundation must support.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SceneRequest` and `SceneResult` dataclasses in `runtime/scene_runtime.py` — already define the standard result contract; Phase 16 extends these rather than replacing them.
- `recover_live_context()` in `evals/meeting_output_bridge.py` — already assembles multi-source evidence for the meeting scene; its pattern of source tracking and missing-source detection is the model for the new EvidenceContainer.
- `gateway.run()` and `LarkCliBaseQueryBackend` — already provide the live-first orchestration boundary that Phase 16 must reuse.
- Existing `_classify_fallback()` in `runtime/scene_runtime.py` — already implements fallback category classification; Phase 16's missing-source handling extends this pattern.

### Established Patterns
- Scenes consistently return structured results with distinct facts/judgments/recommendations fields.
- Live systems are treated as truth; cached or inferred material is secondary.
- Writes go through schema preflight, guard, and writer checks regardless of scene type.
- Facts, judgments, and action proposals are clearly distinguished in output.

### Integration Points
- The new EvidenceContainer and ExpertAnalysisHelper must integrate with the existing scene dispatch in `scene_registry.py` — new scenes register the same way as existing ones.
- The existing four scene implementations (post-meeting, customer-recent-status, archive-refresh, todo-capture-and-update) should be refactored to use the new shared infrastructure without breaking their existing result contracts.
- Fallback classification in `_classify_fallback()` should be extended rather than replaced.

</code_context>

<specifics>
## Specific Ideas

- "EvidenceContainer should feel like a well-organized research folder — you can see at a glance what you have and what is missing."
- "The helper should not become another hidden business-context assembler — it assembles evidence, it does not interpret it for the scene."
- "When a source is missing, the output should read like a honest intelligence report: here's what I found, here's what I couldn't find, here's what that means."

</specifics>

<deferred>
## Deferred Ideas

- None — Phase 16 discussion stayed within the foundation scope.

</deferred>

---

*Phase: 16-expert-analysis-foundation-and-multi-source-evidence*
*Context gathered: 2026-04-17*
