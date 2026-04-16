# Phase 7: Skill Architecture For Scene Expansion - Research

**Date:** 2026-04-16
**Phase:** 7-Skill Architecture For Scene Expansion
**Question:** What do we need to know to plan this phase well?

## Scope Read

Phase 7 is an architecture-contract phase, not a full implementation phase for every future scene. The locked goal is to move the repository from one root skill toward a thin main skill plus scene skills plus on-demand expert agents plus a shared runtime foundation, while adding a separate admin/bootstrap path and a subordinate cache hierarchy that never outranks live truth.

## Current State

### The repo already has the right foundation boundary
- `runtime/gateway.py`, `runtime/live_adapter.py`, and `runtime/schema_preflight.py` already implement the thin live-access and write-safety substrate that future scene skills should reuse.
- `ARCHITECTURE.md` and `SKILL.md` already state that the foundation should not assemble default business context bundles, which matches the locked Phase 7 decisions.
- The current runtime is strongest on meeting and Todo flows, so the next architecture should extend those strengths rather than replace them.

### The current packaging is still root-skill heavy
- `SKILL.md` already documents progressive disclosure and scenario-triggered reference loading, but the packaging is still centered on one root skill plus shared references.
- `docs/loading-strategy.md` assumes a single root skill today and only sketches the future multi-skill direction.
- No concrete scene-skill contract, scene-to-expert handoff spec, or admin/bootstrap skill contract exists yet as first-class repo artifacts.

### The bootstrap and cache shape is conceptually seeded but not formalized
- `CONFIG-MODEL.md` already separates core skill logic from per-user workspace config and runtime guardrails.
- Quick task `260415-nz8` already settled the main architecture direction: thin main skill, workflow-defined scene skills, scene-internal expert agents, separate bootstrap/admin path, and three cache classes.
- The quick-task verification also confirms the remaining gap: the recommendations are not yet written back into canonical docs or executable phase plans.

## Risks

1. If Phase 7 only adds prose without a file-ownership and packaging contract, the repo will keep drifting toward a larger root `SKILL.md`.
2. If scene skills are defined by tables instead of AM workflows, the architecture will fragment the workbench loop and recreate table-driven prompt bloat.
3. If bootstrap/install behavior is mixed into the daily main skill path, low-frequency setup logic will dilute normal scene execution and weaken safety boundaries.
4. If cache artifacts are described as truth rather than acceleration or routing aids, future scenes may silently bypass live confirmation before critical reads or writes.
5. If host-specific packaging assumptions leak into the architecture contract, Phase 7 will hurt the portability goals already established in `REQUIREMENTS.md`.

## Recommended Implementation Shape

### 1. Split the work into three doc-focused plans
- Plan 01 should lock the four-layer execution contract: thin main skill, workflow-defined scene skills, on-demand expert agents, and shared runtime foundation.
- Plan 02 should define the admin/bootstrap contract and the three cache classes with explicit trust hierarchy and refresh lifecycle.
- Plan 03 should wire the packaging and loading guidance back into the root docs so the architecture becomes discoverable and executable for future phases.

### 2. Keep file ownership clean for parallel execution
- Plan 01 should own `SKILL.md`, `ARCHITECTURE.md`, and one new scene-architecture reference.
- Plan 02 should own `CONFIG-MODEL.md` plus new bootstrap/cache reference docs.
- Plan 03 should own `README.md`, `docs/loading-strategy.md`, and `references/INDEX.md` so it can integrate the earlier architecture decisions without merge conflicts.

### 3. Treat Phase 7 as architecture locking, not broad code generation
- Do not require all scene-skill folders, loaders, or cache commands to become fully operational in this phase.
- Do require explicit contracts for first-wave scene names, priority order, expert-agent return artifacts, bootstrap deliverables, cache classes, and live-confirm rules.
- Prefer reference docs and loading/index updates over speculative runtime abstractions.

### 4. Preserve existing trust boundaries explicitly
- Root skill remains entry and orchestration only.
- Scene skills decide what context to hydrate and which expert agents to call.
- Foundation stays thin and reusable.
- Bootstrap/admin remains separate from daily scenes.
- Cache remains subordinate to live truth, and every write path still requires live confirmation before mutation.

## Planning Guidance

- Use two parallel wave-1 plans and one integration wave-2 plan.
- Keep all tasks documentation- or contract-focused; no new external dependencies are required.
- Make the scene-skill definitions workflow-driven and lock the first wave to `post-meeting-synthesis`, `customer-recent-status`, `archive-refresh`, and `todo-capture-and-update`, in that priority grouping.
- Add explicit threat models around cache trust, bootstrap privilege, and root-skill scope creep.

## Validation Architecture

### Fast structural validation
- Validate each new `PLAN.md` with `gsd-tools.cjs frontmatter validate --schema plan`.
- Validate XML/task structure with `gsd-tools.cjs verify plan-structure`.

### Phase-level verification target
- Confirm `ROADMAP.md` no longer shows `TBD` requirements for Phase 7.
- Confirm `REQUIREMENTS.md` contains traceable requirement IDs for the architecture, bootstrap, and cache contract.
- Confirm every Phase 7 plan has non-empty `requirements`, `must_haves`, and a STRIDE threat register.

## Open But Non-Blocking

- Exact folder names for future scene-skill or expert-agent directories can remain implementation-discretionary as long as the packaging contract is explicit.
- Exact cache artifact file formats and refresh commands can be deferred to execution, but the cache classes, trust hierarchy, and refresh lifecycle must be locked now.
- Exact bootstrap remote-initialization surface can be deferred to execution as long as strong-confirmation gating is explicit.

---
*Research status: ready for planning*
