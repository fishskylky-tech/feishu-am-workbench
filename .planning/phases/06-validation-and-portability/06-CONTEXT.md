# Phase 6: Validation And Portability - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning and execution
**Mode:** Autonomous

<domain>
## Phase Boundary

Phase 6 closes the milestone by turning trust and portability expectations into executable checks. The repository already has multi-case evals and host-portability guidance spread across docs. This phase makes that contract harder to regress by adding tests that verify the live-first/recommendation-first rules remain visible in project guidance and that runtime/account-operating code stays host-agnostic.

</domain>

<decisions>
## Decisions

- **D-01:** Prefer executable validation over additional prose. New guarantees should land as tests first.
- **D-02:** Treat runtime and eval core as host-agnostic code. Host names may appear in project guidance, but not in the account-operating core.
- **D-03:** Accept both `recommendation-first` and `recommendation mode` as valid wording when checking repo guidance, as long as the safety rule is explicit.

### Claude's Discretion

- Add the smallest test surface needed to prove portability and rule consistency.
- Reuse existing docs as the source of truth instead of rewriting them.

</decisions>

<code_context>
## Existing Code Insights

- `tests/test_validation_assets.py` already checks multi-case validation assets and version consistency.
- `runtime/` and `evals/` currently avoid host-specific markers; this should be pinned in tests.
- `AGENTS.md`, `README.md`, `SKILL.md`, and `.planning/PROJECT.md` already express the live-first and recommendation-first safety model, though wording differs slightly.

</code_context>

<specifics>
## Specific Ideas

- Add a portability-contract test that checks host coverage in project docs.
- Add a rule-consistency test that accepts current repo wording while still enforcing the safety model.
- Assert that runtime and eval core modules do not mention Hermes/OpenClaw/Codex directly.

</specifics>

<deferred>
## Deferred Ideas

- Full host adapter implementation work
- Packaging or bootstrap refactors beyond executable contract checks

</deferred>
