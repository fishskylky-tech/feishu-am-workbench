# Phase 4: Unified Safe Writes - Research

**Date:** 2026-04-16
**Phase:** 4-Unified Safe Writes
**Question:** What do we need to know to plan this phase well?

## Scope Read

Phase 4 must make the existing mutation path trustworthy enough for day-to-day use without weakening the repo's live-first and recommendation-first contract. The locked decisions narrow the problem in three important ways:

- confirmed real writes should still center on Todo create/update first
- meeting scenes should emit cleaner normalized candidates, preferring same-meeting thematic consolidation over sentence-level fragmentation
- any widening beyond Todo must stay narrow, explicit, and limited to low-risk customer-master fact fields rather than a generic Base writer

This is therefore not a broad "write everything" phase. It is a hardening phase for candidate normalization, mandatory safety gates, normalized result contracts, and a tightly bounded next step beyond Todo.

## Current State

### Unified Todo writer already has a viable minimum loop
- `runtime/todo_writer.py` already supports `create`, `update`, duplicate detection, and recommendation-only subtask creation unless `source_context.confirm_create_subtask=true` is present.
- Live validation in `archive/validation-reports/2026-04-12-unified-todo-writer-live-validation.md` already proves four concrete paths in a real Feishu workspace: blocked, duplicate recommendation, duplicate -> update auto patch, and create.
- This means Phase 4 does not need to invent the Todo write surface from scratch. It needs to tighten contract edges, improve candidate quality, and make the output/result model stable enough for planning and validation.

### Safety gates exist, but they are still object-local and thin
- `runtime/schema_preflight.py` already enforces live table/field existence, type compatibility, select-option resolution, owner validity, and guarded-field write policies.
- `runtime/write_guard.py` currently adds only the last thin safety layer: blocked preflight propagation, protected field blocking, and owner-required enforcement.
- `runtime/gateway.py` already evaluates preflight and guard for all provided write candidates, but it does not yet guarantee that every write-ready scenario uses one normalized contract end-to-end.

### Candidate generation is still the weakest link
- `evals/meeting_output_bridge.py` already emits Todo candidates carrying `operation`, `match_basis`, `source_context`, and `target_object`, which satisfies the minimum shape requirement.
- The current bridge still emits a single small sample candidate and does not yet model same-meeting thematic consolidation, richer source-context grounding, or broader object-specific write routing.
- This makes the scene layer, not the writer layer, the main Phase 4 pressure point for `MEET-03`.

### The current result contract is normalized internally, but not yet clearly tiered for presentation
- `TodoWriteResult` and `WriteExecutionResult` already carry preflight status, guard status, dedupe decision, blocked reasons, drift items, and remote metadata.
- The user decision for this phase adds a presentation split: default output should stay natural-language-first, while the full structured envelope must remain available for validation, debugging, and inspection.
- This means the runtime contract can stay rich, but output rendering should become an explicit layer choice rather than an accident of current debug-oriented structures.

## Risks

1. If same-meeting consolidation is too aggressive, distinct action items may be merged into one vague Todo and lose execution usefulness.
2. If dedupe remains Todo-writer-local without stronger scene-level `match_basis`, candidate quality will plateau and duplicate handling will remain brittle.
3. If concise user-facing output is implemented by dropping internal fields rather than layering a renderer over the full envelope, validation and debugging will regress.
4. If low-risk customer-master writes are introduced through a generic Base mutation abstraction, the phase will violate the project's minimal-semantic-contract rule and create a larger trust surface than intended.
5. If high-risk vs low-risk customer-master policy is encoded only in prompts or docs instead of executable guard/preflight rules, downstream scenes will drift and Phase 6 validation will become weak.

## Recommended Implementation Shape

### 1. Keep candidate normalization in the scene layer, not in the writer
- Extend `evals/meeting_output_bridge.py` first so post-meeting extraction emits better normalized candidates before they reach the gateway or writer.
- Add a small scene-level consolidation rule for same-meeting same-theme actions, preserving explicit `operation`, `match_basis`, `source_context`, and `target_object` per candidate.
- Keep the writer focused on dedupe and execution. Do not move meeting-scene judgment into `runtime/todo_writer.py`.

### 2. Promote the full write-result envelope to a stable contract
- Treat `WriteExecutionResult` as the authoritative machine-facing result contract.
- Preserve `preflight_status`, `guard_status`, `dedupe_decision`, `blocked_reasons`, `drift_items`, `remote_object_id`, and `remote_url` on every executed or blocked path.
- Add a separate rendering or summarization layer for concise default user output rather than shrinking the underlying result schema.

### 3. Tighten the gateway-to-writer contract before widening scope
- Ensure every confirmed write path uses the same sequence: candidate -> preflight -> guard -> object writer -> normalized result.
- Keep `runtime/gateway.py` as the orchestrator for common safety evaluation, but let object-specific execution stay with writers.
- Prefer adding missing typed structures in `runtime/models.py` over passing ad hoc dicts between scene, gateway, and writer.

### 4. Introduce low-risk customer-master writes as a narrow policy slice, not a platform
- If this phase widens beyond Todo, it should do so through a tightly scoped customer-master fact path only.
- The allowed field family should stay operational and low-ambiguity: recent follow-up time, next follow-up date, clearly grounded current owner, and similarly factual slots.
- Semi-judgment or strategy-bearing fields should stay recommendation-only even if the schema technically allows them.
- The runtime implementation should favor a small explicit allowlist plus protected-field enforcement over a reusable generic "master-data writer" abstraction.

### 5. Reuse existing live validation evidence and extend it surgically
- The current live report already proves the Todo writer's minimum loop; Phase 4 should build on that rather than replace it with new manual rituals.
- Focus new regression coverage on candidate normalization, mandatory gate usage, result-envelope stability, and low-risk/high-risk customer-master routing decisions.
- Avoid broad refactors or new dependencies. The current repo already has enough substrate for this phase.

## Architectural Responsibility Map

### Scene layer
- Owns meeting/post-meeting extraction
- Decides which action items should consolidate into one candidate
- Chooses target object and prepares `match_basis` / `source_context`
- Decides whether a proposed customer-master update is in-scope for the low-risk path or must remain recommendation-only

### Gateway layer
- Collects preflight and guard evaluations consistently for all candidates
- Exposes normalized safety state back to the scene
- Must not silently decide scene semantics or consolidate business actions

### Writer layer
- Executes object-specific confirmed writes
- Applies object-level dedupe and returns normalized write results
- Must not infer meeting semantics or widen scope beyond its object contract

### Output layer
- Renders concise natural-language summaries for default user output
- Keeps full structured write result available for validation, debugging, and audits
- Must not erase or compress away blocked reasons and safety evidence from the underlying contract

## Planning Guidance

- Split the phase into at least two plans: one for candidate/result contract hardening around the meeting -> gateway -> Todo path, and one for the narrow customer-master risk-policy slice and presentation/verification alignment.
- Treat `evals/meeting_output_bridge.py` and `tests/test_meeting_output_bridge.py` as one hotspot; avoid parallel plans that modify them in the same wave.
- Keep `runtime/models.py`, `runtime/gateway.py`, `runtime/schema_preflight.py`, and `runtime/write_guard.py` as the shared contract surface. Any plan that changes them should do so deliberately and with direct regression coverage.
- Prefer small explicit policy structures over generic new abstractions. The repo's established pattern is thin runtime, small semantic contracts, and auditable scene logic.

## Validation Architecture

### Quick feedback surface
- Use `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` after tasks that touch candidate normalization, output rendering, or meeting-scene write routing.
- Use `./.venv/bin/python -m unittest tests.test_runtime_smoke -q` after tasks that touch gateway, preflight, guard, or normalized write results.

### Full phase surface
- Use `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner -q` after each wave.
- This keeps Phase 2 and Phase 3 hardening guarantees intact while Phase 4 changes write-path behavior.

### Required regression additions
- Candidate-consolidation tests showing same-meeting same-theme actions merge conservatively while preserving explicit normalized fields.
- Tests proving confirmed write paths always return a full normalized result envelope even when default user output becomes concise.
- Tests proving Todo duplicate handling still distinguishes `update_existing`, `create_subtask`, `create_new`, and blocked cases correctly.
- Tests proving high-risk customer-master updates remain recommendation-only and low-risk fact fields are the only candidates eligible for a narrowed direct-write path.

## Open But Non-Blocking

- The exact "same theme" consolidation heuristic can be chosen during planning as long as it is conservative and auditable.
- The exact low-risk customer-master allowlist can be finalized during planning, but it must stay small and fact-like.
- The exact concise-output wording can evolve during implementation as long as the structured result contract remains intact and testable.

---
*Research status: ready for planning*
