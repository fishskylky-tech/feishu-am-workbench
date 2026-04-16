---
phase: 04
slug: unified-safe-writes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python unittest |
| **Config file** | none — unittest module discovery under repo venv |
| **Quick run command** | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` |
| **Full suite command** | `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` or `./.venv/bin/python -m unittest tests.test_runtime_smoke -q` depending on the touched surface
- **After every plan wave:** Run `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | MEET-03 | T-04-01 / T-04-02 | Meeting scenes emit normalized candidates with explicit routing fields | unit | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` | ✅ | ⬜ pending |
| 04-01-02 | 01 | 1 | WRITE-01, WRITE-02 | T-04-03 / T-04-04 | Todo confirmed-write path always passes preflight+guard and returns normalized result envelope | unit/integration | `./.venv/bin/python -m unittest tests.test_runtime_smoke tests.test_meeting_output_bridge -q` | ✅ | ⬜ pending |
| 04-02-01 | 02 | 2 | WRITE-03 | T-04-05 / T-04-06 | High-risk customer-master updates remain recommendation-only; only explicit low-risk fact fields may advance | unit | `./.venv/bin/python -m unittest tests.test_runtime_smoke -q` | ✅ | ⬜ pending |
| 04-02-02 | 02 | 2 | WRITE-02, WRITE-03 | T-04-07 / — | Concise default output preserves underlying structured evidence for validation/debug | unit/integration | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge tests.test_eval_runner -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Existing infrastructure covers all phase requirements.
- [ ] Add any missing regression cases in `tests/test_meeting_output_bridge.py` before implementation tasks that change candidate normalization or output behavior.
- [ ] Add any missing gateway/guard regressions in `tests/test_runtime_smoke.py` before implementation tasks that change write safety contracts.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Todo duplicate -> update / create / blocked behavior still matches real Feishu tasklist behavior | WRITE-02 | Real dedupe and live remote metadata depend on private tasklist state | Re-run the Phase 4 live validation flow against the configured tasklist and compare outcomes with `archive/validation-reports/2026-04-12-unified-todo-writer-live-validation.md` |
| Any narrowed customer-master direct-write path only touches the intended low-risk fields | WRITE-03 | Requires a real workspace schema and real protected-field surface | Validate against a live workspace with explicit sample candidates and confirm that non-allowlisted or high-risk fields stay blocked/recommendation-only |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
