---
phase: 03
slug: core-context-recovery
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-15
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python unittest |
| **Config file** | none — stdlib test discovery |
| **Quick run command** | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` |
| **Full suite command** | `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q`
- **After every plan wave:** Run `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | LIVE-04, WORK-01, MEET-01 | T-03-01 / T-03-02 | Recovery only starts after gateway result is known and keeps customer scope tied to deterministic resolution | unit | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | LIVE-04, MEET-01 | T-03-03 | Three-core-table recovery stays scene-level and auditable instead of expanding gateway side effects | unit | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` | ✅ | ⬜ pending |
| 03-02-01 | 02 | 2 | WORK-03, LIVE-04 | T-03-04 / T-03-05 | Archive / meeting-note fallback search is constrained, evidence-backed, and conflict-aware | unit | `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` | ✅ | ⬜ pending |
| 03-02-02 | 02 | 2 | MEET-02 | T-03-06 | Final meeting output exposes fixed audit fields and downgrades write ceiling when fallback confidence is unsafe | unit | `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live archive / meeting-note fallback discovery on a real Feishu workspace | WORK-03, MEET-02 | Requires current user scopes, real Drive folder contents, and live customer archives that fixtures cannot safely embed | In a configured shell, run the Phase 3 scene flow against one customer with a valid archive link, one with only fallback-search evidence, and one with conflicting candidates; confirm the output changes `写回上限` and `开放问题` accordingly |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 2s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
