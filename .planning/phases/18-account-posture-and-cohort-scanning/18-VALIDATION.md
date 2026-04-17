---
phase: 18
slug: account-posture-and-cohort-scanning
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `pytest tests/test_scene_runtime.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_scene_runtime.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 18-01 | 1 | STAT-01 | T-18-01 | Lens attribution traceable to sources | unit | `pytest tests/test_scene_runtime.py::TestStat01FourLensOutput -x` | YES (extend) | ⬜ pending |
| 18-01-02 | 18-01 | 1 | STAT-01 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestStat01LensCount -x` | NO (new) | ⬜ pending |
| 18-01-03 | 18-01 | 1 | STAT-01 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestStat01LensAttribution -x` | NO (new) | ⬜ pending |
| 18-02-01 | 18-02 | 2 | SCAN-01 | T-18-02 | Condition query injection prevention | unit | `pytest tests/test_cohort_scan.py::TestConditionQueryParsing -x` | NO (new) | ⬜ pending |
| 18-02-02 | 18-02 | 2 | SCAN-01 | — | N/A | unit | `pytest tests/test_cohort_scan.py::TestCohortLimit -x` | NO (new) | ⬜ pending |
| 18-02-03 | 18-02 | 2 | SCAN-01 | — | N/A | unit | `pytest tests/test_cohort_scan.py::TestCohortAggregation -x` | NO (new) | ⬜ pending |
| 18-02-04 | 18-02 | 2 | SCAN-01 | — | N/A | unit | `pytest tests/test_cohort_scan.py::TestRecommendationCap -x` | NO (new) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scene_runtime.py` — extend with STAT-01 four-lens tests (TestStat01FourLensOutput, TestStat01LensCount, TestStat01LensAttribution)
- [ ] `tests/test_cohort_scan.py` — new file covering SCAN-01 behaviors (TestConditionQueryParsing, TestCohortLimit, TestCohortAggregation, TestRecommendationCap)
- [ ] `pytest.ini` or `pyproject.toml` — if not already present
- [ ] No framework install needed — pytest already present

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Four-lens output formatting in judgments field | STAT-01 | Requires visual inspection of scene output structure | Run scene manually, inspect judgments field for labeled sub-items |

*If none: "All phase behaviors have automated verification."*

---

## Security Controls

| Threat | STRIDE | Mitigation |
|--------|--------|------------|
| Condition query injection into customer filter | Tampering | Keyword-based extraction only; no raw SQL construction |
| Unbounded cohort enumeration | Information Disclosure | D-04 limit enforcement (default 10) prevents large result dumps |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** {pending / approved YYYY-MM-DD}