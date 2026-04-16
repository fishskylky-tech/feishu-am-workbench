---
phase: 02
slug: live-runtime-hardening
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-15
---

# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Private runtime env -> runtime source loader | Private FEISHU_AM_* values enter the local runtime and become live resource hints. | Base token, table IDs, folder tokens, tasklist GUIDs |
| Runtime -> lark-cli / Feishu APIs | The runtime probes and reads live Base, Drive, and Task capabilities through local lark-cli commands. | Live customer metadata, docs folder reachability, tasklist reachability |
| Customer resolver -> live workflow selection | A user-supplied customer query determines which live customer context can be accessed next. | Customer short name, customer ID, resolved customer identity |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-02-01 | Information Disclosure | runtime/runtime_sources.py | mitigate | Live resource truth is env-backed only; checked-in repo docs cannot supply Base, Docs, or Task hints. Verified by runtime source loader code and regression tests covering repo-file non-participation. | closed |
| T-02-02 | Elevation of Privilege | runtime/resource_resolver.py + runtime/diagnostics.py | mitigate | Missing required private inputs fail closed and render blocked diagnostics with explicit next action instead of allowing guessed live startup. Verified by diagnostic renderer and missing-env smoke coverage. | closed |
| T-02-03 | Spoofing | runtime/customer_resolver.py | mitigate | Customer resolution is exact-first, allows only a single remaining candidate, and returns ambiguous instead of auto-selecting a wrong customer. Verified by regression tests and human live validation on 联合利华（UFS） / C_002. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-15 | 3 | 3 | 0 | GitHub Copilot |

---

## Security Audit 2026-04-15

| Metric | Count |
|--------|-------|
| Threats found | 3 |
| Closed | 3 |
| Open | 0 |

Evidence reviewed:
- runtime/runtime_sources.py env-only source loader
- runtime/diagnostics.py blocked/degraded/available operator-facing diagnostics
- runtime/customer_resolver.py deterministic resolution rules
- tests/test_runtime_smoke.py env-only, fail-closed, and ambiguity regression coverage
- 02-VERIFICATION.md and 02-HUMAN-UAT.md live verification results

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] threats_open: 0 confirmed
- [x] status: verified set in frontmatter

**Approval:** verified 2026-04-15
