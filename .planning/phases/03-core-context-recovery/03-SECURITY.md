---
phase: 03
slug: core-context-recovery
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-15
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| transcript -> scene recovery | Untrusted meeting text must not be treated as grounded customer context before gateway/customer resolution completes | Transcript text, customer query hints |
| scene recovery -> Base query backend | Customer-scoped reads must remain tied to the resolved customer and minimal semantic contract | Customer ID, core-table row reads |
| drive/doc candidate discovery -> scene ranking | Raw folder metadata is insufficient to become grounded context without explicit evidence and conflict checks | Drive folder listings, candidate titles/links |
| scene output -> downstream write planning | Recovery confidence and audit fields influence later write decisions and must not overstate certainty | Write ceiling, open questions, candidate conflicts |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-01 | I | evals/meeting_output_bridge.py | mitigate | Unresolved or ambiguous customers are forced to `context-limited` with explicit fallback reasons before any grounded recovery is emitted; see `recover_live_context()` unresolved branches and corresponding tests | closed |
| T-03-02 | T | runtime/models.py | mitigate | Typed `ContextRecoveryResult` and `WriteCeiling` contracts replace free-form dict/text conventions so later code cannot silently reinterpret recovery evidence | closed |
| T-03-03 | E | evals/meeting_output_bridge.py | mitigate | Scene orchestration remains limited to 客户主数据, 客户联系记录, and 行动计划 after customer resolution; gateway is not widened into business context assembly | closed |
| T-03-04 | I | runtime/live_adapter.py | mitigate | Drive fallback discovery is constrained to configured folders and title-based query terms, and no longer fabricates customer evidence onto candidates | closed |
| T-03-05 | T | evals/meeting_output_bridge.py | mitigate | Archive and meeting-note fallback now surface duplicate/conflicting/weak-evidence candidates via `candidate_conflicts` and `open_questions` instead of silently accepting them | closed |
| T-03-06 | E | evals/meeting_output_bridge.py | mitigate | `写回上限` is computed from recovery completeness plus fallback conflicts, forcing `recommendation-only` whenever fallback confidence is incomplete or conflicting | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-15 | 6 | 6 | 0 | GitHub Copilot |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-15
