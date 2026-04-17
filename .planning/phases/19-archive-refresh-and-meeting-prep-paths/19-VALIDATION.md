---
phase: 19
slug: archive-refresh-and-meeting-prep-paths
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pytest.ini (if exists) or pyproject.toml |
| **Quick run command** | `pytest tests/test_scene_runtime.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_scene_runtime.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-01-01 | ARCH-01 | 1 | ARCH-01 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestArchRefreshFiveDimension -x` | needs new | ⬜ pending |
| 19-01-02 | ARCH-01 | 1 | ARCH-01 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestArchRefreshDistinctFormat -x` | needs new | ⬜ pending |
| 19-02-01 | PREP-01 | 1 | PREP-01 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestMeetingPrepSevenDimension -x` | needs new | ⬜ pending |
| 19-02-02 | PREP-01 | 1 | PREP-01 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestMeetingPrepStat01Reuse -x` | needs new | ⬜ pending |
| 19-03-01 | WRITE-02 | 1 | WRITE-02 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestWrite02Checklist -x` | needs new | ⬜ pending |
| 19-03-02 | WRITE-02 | 1 | WRITE-02 | — | N/A | unit | `pytest tests/test_scene_runtime.py::TestMinimalQuestions -x` | needs new | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scene_runtime.py` — existing, covers STAT-01 (Phase 18)
- [ ] `tests/test_archive_refresh_scene.py` — needed for ARCH-01 (Phase 19)
- [ ] `tests/test_meeting_prep_scene.py` — needed for PREP-01 (Phase 19)
- [ ] `tests/test_confirmation_checklist.py` — needed for WRITE-02 (Phase 19)
- [ ] Framework install: already detected (pytest in project)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Archive refresh distinct from Phase 17 post-meeting format | ARCH-01 D-03 | Format comparison requires human judgment of output distinctiveness | Run scene, visually compare with Phase 17 output |
| Meeting prep brief renders correctly in Lark card | PREP-01 | Lark card rendering requires visual verification | Manual render check in Lark message |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending / approved YYYY-MM-DD
