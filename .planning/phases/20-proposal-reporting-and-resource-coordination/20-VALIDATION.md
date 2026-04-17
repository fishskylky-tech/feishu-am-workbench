---
phase: 20
slug: proposal-reporting-and-resource-coordination
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | tests/conftest.py (existing) |
| **Quick run command** | `pytest tests/test_proposal_scene.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_proposal_scene.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 20-01 | 1 | PROP-01 | T-20-01 | N/A (infrastructure) | unit | `pytest tests/test_proposal_scene.py::test_build_proposal_checklist -v` | ✅ | ⬜ pending |
| 20-01-02 | 20-01 | 1 | PROP-01 | T-20-02 | N/A (output format) | unit | `grep -c "def render_proposal_" runtime/scene_runtime.py` | ✅ | ⬜ pending |
| 20-01-03 | 20-01 | 1 | PROP-01 | T-20-03 | N/A (scene registration) | unit | `grep "run_proposal_scene" runtime/scene_registry.py` | ✅ | ⬜ pending |
| 20-02-01 | 20-02 | 2 | WRITE-01 | T-20-04 | Routing targets Feishu native destinations | unit | `grep "_infer_proposal_output_destination" runtime/live_adapter.py` | ✅ | ⬜ pending |
| 20-03-01 | 20-03 | 3 | PROP-01 | T-20-05 | Five-dimension output verified | unit | `pytest tests/test_proposal_scene.py::test_five_dimension_output -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_proposal_scene.py` — stubs for proposal scene tests
- [ ] `tests/conftest.py` — shared fixtures (existing)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Feishu Drive folder creation | WRITE-01 | Requires live Feishu API access | Verify doc created in customer archive folder via Feishu app |
| Base 行动计划 table write | WRITE-01 | Requires live Base API access | Verify resource-coordination item written to Base table |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
