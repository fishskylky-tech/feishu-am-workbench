# Phase 7: Skill Architecture For Scene Expansion - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 defines the architecture contract for expanding `feishu-am-workbench` from one entry skill into a layered system: a thin main skill, multiple scene skills, on-demand expert agents, shared runtime foundation capabilities, and an admin/bootstrap path with subordinate cache layers. This phase locks architecture and boundary decisions; it does not require immediate implementation of every new scene, cache, or bootstrap mutation path.

</domain>

<decisions>
## Implementation Decisions

### Main skill boundary
- **D-01:** The main skill should remain a thin entry and orchestration layer, not a larger all-in-one business prompt.
- **D-02:** The main skill is responsible for scene detection, deciding whether live context is needed, coordinating the recommendation -> confirmation -> write flow, and maintaining a unified top-level interaction pattern across scenes.
- **D-03:** Deep business reasoning, scene-specific rules, and low-level Feishu object handling should not stay in the main skill.

### Scene skill model
- **D-04:** Scene skills must be defined by AM workflows and user-facing scenarios rather than by raw Feishu tables.
- **D-05:** The first formal scene-skill wave should center on `post-meeting-synthesis`, `customer-recent-status`, `archive-refresh`, and `todo-capture-and-update`.
- **D-06:** Priority order for the first wave should be: first `post-meeting-synthesis` and `customer-recent-status`, then `archive-refresh` and `todo-capture-and-update`.
- **D-07:** `meeting-prep`, `weekly-or-monthly-account-review`, `public-update-synthesis`, and `phase-goal-review` remain valid future scene candidates, but they are not part of the first locked wave.

### Expert agent collaboration
- **D-08:** Expert agents should be invoked by scene skills on demand, not by a fixed global pipeline and not by the main skill as a universal dispatcher.
- **D-09:** Expert agents should return structured intermediate artifacts back to the scene skill, such as hydrated context, risk or opportunity lists, write-safety reports, or action candidates.
- **D-10:** Final user-facing synthesis remains the responsibility of the scene skill, which decides which expert outputs are needed and how to merge them.

### Admin and bootstrap path
- **D-11:** Bootstrap, install, compatibility, and environment-diagnosis capabilities should live in a separate admin/bootstrap skill, not in the daily main-skill path.
- **D-12:** The minimum bootstrap deliverables should include: workspace compatibility reporting, local config generation or update guidance, cache initialization or refresh output, drift and risk reporting, and explicit `lark-cli` version dependency checks.
- **D-13:** The bootstrap path may support automatic repair on the local side and, with strong confirmation, controlled creation or initialization of remote Feishu resources.
- **D-14:** Even when bootstrap supports controlled remote initialization, it remains an admin/setup path only. It must not weaken the recommendation-first and guarded-write rules of daily operating scenes.

### Cache contract
- **D-15:** Phase 7 should formally define three cache classes: workspace schema cache, workspace manifest/index cache, and semantic/ontology cache.
- **D-16:** Schema cache exists to reduce repeated schema and option discovery, but it remains a compatibility or acceleration layer rather than runtime truth.
- **D-17:** Manifest/index cache exists to accelerate archive lookup, meeting-note lookup, folder or tasklist resolution, and other repeated resource routing tasks.
- **D-18:** Semantic or ontology cache is a reasoning layer for entities, relations, events, operating state, and write-target mapping; it is a future extension surface and must not become a default runtime truth source.
- **D-19:** Cache may be used for routing and early reasoning, but critical reads should confirm live state when needed and every write path must use live confirmation before mutation.
- **D-20:** Cache refresh should be treated as an explicit artifact lifecycle, especially for bootstrap/setup and drift handling, rather than an implicit always-rebuild behavior.

### Foundation boundary
- **D-21:** Shared runtime foundation capabilities should continue to own resource probing, customer resolution, targeted read primitives, schema preflight, write guard, diagnostics, and normalized writer surfaces.
- **D-22:** The foundation must stay thin and reusable; it should not silently assemble a full business-context bundle for every scene.
- **D-23:** Scene skills remain responsible for deciding what context to hydrate, which expert agents to call, and which candidate outputs or writes to propose.

### the agent's Discretion
- Exact folder layout for scene skills, expert agent descriptors, and admin/bootstrap skill resources is discretionary as long as the four-layer contract stays explicit.
- Exact artifact format for schema cache, manifest/index cache, and semantic cache is discretionary during planning, but the three cache classes and their trust hierarchy are locked.
- Exact first-wave implementation order inside the two priority groups is discretionary if planning still preserves `post-meeting-synthesis` and `customer-recent-status` as the first group.

</decisions>

<specifics>
## Specific Ideas

- The desired target shape is: main skill as thin orchestrator, scene skills as self-contained workflow units, expert agents as internal collaborators, and runtime as the shared Feishu foundation.
- The architecture should stay aligned with progressive disclosure rather than growing the current root `SKILL.md` into a larger monolith.
- Bootstrap should be separated from daily usage because setup, compatibility, and drift repair are low-frequency but high-impact flows.
- Controlled remote initialization is acceptable only under the admin/bootstrap path and only behind strong confirmation.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and prior seed decisions
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria, dependency position, and architecture outcome expected from this discussion
- `.planning/STATE.md` — confirms Phase 7 is pending and records the quick-task seed that introduced this phase
- `.planning/quick/260415-nz8-feishu-am-workbench-skill-skill/260415-nz8-SUMMARY.md` — seed architecture recommendation for main skill, scene skills, expert agents, bootstrap skill, and cache classes
- `.planning/quick/260415-nz8-feishu-am-workbench-skill-skill/260415-nz8-VERIFICATION.md` — confirms which architecture questions were already covered and which gaps remained

### Current skill and architecture surfaces
- `SKILL.md` — current single-skill contract, progressive disclosure structure, and runtime prerequisites that the new architecture must evolve from
- `ARCHITECTURE.md` — current split between input, scene orchestration, extraction/judgment, runtime foundation, and progressive disclosure design
- `docs/loading-strategy.md` — current progressive disclosure strategy that should inform future scene-skill packaging and loader behavior

### Config and stable-boundary rules
- `CONFIG-MODEL.md` — workspace config boundary, private-vs-shared split, and safe runtime guardrail model that bootstrap/admin must preserve
- `references/minimal-stable-core.md` — stable core vs extension-surface boundary for future architecture work
- `references/workbench-information-architecture.md` — customer master/detail/archive/todo loop that scene boundaries must reflect

### Runtime and compatibility boundaries
- `references/feishu-runtime-sources.md` — runtime truth hierarchy that cache and bootstrap behavior must not violate
- `references/base-integration-model.md` — live schema vs semantic contract vs scenario routing split that should remain intact in the new architecture
- `references/live-schema-preflight.md` — write-time live validation contract that all future scene skills and bootstrap mutations must preserve
- `runtime/gateway.py` — current gateway boundary for resource resolution, customer resolution, preflight, and guard orchestration
- `runtime/live_adapter.py` — current thin live capability, targeted read, and resource probing substrate
- `runtime/schema_preflight.py` — current live-confirm contract for safe writes

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SKILL.md` already implements a three-tier progressive disclosure model; Phase 7 should extend this into multiple self-contained scene skills rather than inflate one root skill.
- `ARCHITECTURE.md` already separates scene orchestration from runtime foundation, which matches the desired main-skill vs scene-skill split.
- `runtime/gateway.py`, `runtime/live_adapter.py`, and `runtime/schema_preflight.py` already form the thin shared foundation that future scene skills can reuse.
- `CONFIG-MODEL.md` already defines workspace config as the environment boundary, giving the bootstrap/admin path a natural contract surface.

### Established Patterns
- The repo consistently prefers thin foundation layers, explicit scene decisions, live-first validation, and recommendation-first mutation.
- Cache-like artifacts already exist as compatibility aids, but current docs consistently state that live truth stays authoritative.
- Existing quick-task research already recommends scene-skill boundaries by workflow rather than by table, so planning should build on that rather than reopen it.

### Integration Points
- Future scene-skill packaging will need to stay compatible with the current root skill while progressively moving scene-specific logic and references into self-contained folders.
- Admin/bootstrap work should connect to `config/`, runtime capability checks, and cache-generation paths without becoming part of the normal scene invocation path.
- Expert-agent contracts should connect to scene-level orchestration and return structured artifacts that can feed existing audit, recommendation, and write-planning flows.

</code_context>

<deferred>
## Deferred Ideas

- `meeting-prep` is a valid near-future scene skill, but it is intentionally outside the first locked wave.
- `weekly-or-monthly-account-review`, `public-update-synthesis`, and `phase-goal-review` remain future scene candidates rather than first-wave commitments.
- Exact cache artifact file formats, refresh commands, and loader mechanics are deferred to planning and implementation.
- Exact remote bootstrap mutation surface, such as which table or folder creation flows are allowed, is deferred to planning under the strong-confirmation rule.

</deferred>

---
*Phase: 07-skill-architecture-scene-expansion*
*Context gathered: 2026-04-16*