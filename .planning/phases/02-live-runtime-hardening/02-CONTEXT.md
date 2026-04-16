# Phase 2: Live Runtime Hardening - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 hardens the live runtime startup surface: private configuration loading, resource source resolution, capability diagnostics, and customer resolution. The goal is to make live execution start from explicit private runtime truth instead of repo-derived guesses, while preserving the existing safety-first operating model.

</domain>

<decisions>
## Implementation Decisions

### Resource source boundary
- **D-01:** Runtime source of truth must be limited to private runtime sources. Repository documents, examples, and checked-in references must not act as live resource fallbacks.
- **D-02:** For the current Phase 2 contract, the formal authoritative input is the process environment carrying private `FEISHU_AM_*` values.
- **D-03:** Local `.env` may remain only as a convenience layer that loads values into the process environment. It must not be treated as an independent runtime source contract or a separate truth layer.
- **D-04:** When required private inputs are missing, the runtime should fail the live path hard and return explicit diagnostics listing missing inputs and remediation guidance. It should not silently fall back to repo hints.

### Diagnostic output policy
- **D-05:** Runtime capability and startup diagnostics should use three plain-language states: available, degraded, and blocked.
- **D-06:** Default diagnostic output should include a clear conclusion, the concrete reason, and the next recommended action, rather than only exposing raw status details.

### Customer resolution policy
- **D-07:** Customer resolution should prioritize exact match first, including exact customer short name and customer ID.
- **D-08:** If exact match is absent but only one obvious candidate remains, runtime may resolve it directly.
- **D-09:** Any ambiguous customer result should stop and ask for confirmation instead of guessing.

### Hardening scope boundary
- **D-10:** Phase 2 should stay narrowly focused on runtime ground truth, startup diagnostics, and deterministic customer lookup.
- **D-11:** Phase 2 should not expand business-facing scene behavior or broader live-read features beyond what is needed to harden this foundation.

### the agent's Discretion
- If existing code still reads repo docs for hints, that behavior should be removed or downgraded so it cannot influence live resolution decisions.
- If requirement wording or docs still describe `.env` as a first-class source, downstream planning may tighten that wording as long as the implementation still allows `.env` as a local env-loading convenience.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition
- `.planning/ROADMAP.md` — Phase 2 goal, requirement mapping, and success criteria for Live Runtime Hardening
- `.planning/REQUIREMENTS.md` — `FOUND-02`, `LIVE-01`, `LIVE-02`, and `LIVE-03` define the required outcomes this phase must satisfy
- `.planning/PROJECT.md` — project constraints around private identifiers, safety-first writes, and brownfield execution

### Runtime surfaces in scope
- `runtime/env_loader.py` — current `.env` loader behavior and precedence baseline
- `runtime/runtime_sources.py` — current runtime source derivation logic, including repo fallback behavior that Phase 2 should tighten
- `runtime/resource_resolver.py` — required live resource keys and status model (`resolved`, `partial`, `unresolved`)
- `runtime/diagnostics.py` — structured and human-readable diagnostic surfaces for blocked/degraded states
- `runtime/customer_resolver.py` — current customer matching path that Phase 2 must keep deterministic while runtime sources harden

### Supporting context
- `STATUS.md` — current implemented runtime status and live-read claims
- `references/feishu-runtime-sources.md` — intended private runtime source model
- `references/live-resource-links.example.md` — example-only reference that should not be treated as live truth

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `runtime/env_loader.py` already preserves explicit shell env over `.env`, which fits the chosen authority model.
- `runtime/resource_resolver.py` and `runtime/diagnostics.py` already expose enough structure to support hard-blocked live startup with explicit missing-resource diagnostics.

### Established Patterns
- The repo already separates facts, diagnostics, and guarded writes; Phase 2 should preserve that pattern for startup/resource status.
- Runtime is intentionally thin. Hardening should stay focused on startup truth and diagnostics, not widen business behavior.

### Risks To Address
- `runtime/runtime_sources.py` currently allows repo-derived hints to influence runtime source resolution, which conflicts with the selected boundary.
- `FOUND-02` currently describes shell env or local `.env` as source inputs; planning may need to clarify that `.env` is convenience-only rather than a separate authoritative layer.
- Current diagnostic surfaces are structured enough, but their wording may need tightening so blocked startup is obvious to an operator.
- Customer resolution behavior must stay deterministic without widening into a broader fuzzy-matching feature project.

</code_context>

<specifics>
## Specific Ideas

- Treat process environment as the only authoritative runtime contract surface in Phase 2.
- Keep `.env` support only if it behaves as a private local bootstrap into environment variables, not as a separate fallback path.
- Missing required runtime inputs should block the live path immediately, with diagnostics that tell the operator exactly what to set.
- Use a simple operator-facing status vocabulary: available, degraded, blocked.
- Keep customer lookup conservative: exact match first, unique obvious candidate allowed, ambiguity always stops for confirmation.
- Resist adding broader business capabilities in this phase; keep it as foundation hardening only.

</specifics>

<deferred>
## Deferred Ideas

None — the initially open gray areas discussed in this pass are now closed.

</deferred>

---
*Phase: 02-live-runtime-hardening*
*Context gathered: 2026-04-15*