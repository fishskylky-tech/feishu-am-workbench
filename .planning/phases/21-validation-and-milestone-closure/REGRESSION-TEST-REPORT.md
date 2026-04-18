---
title: VAL-05 Regression Test Report
date: 2026-04-18
scope: 6 scenes, 4 case types each = 24 paths
---

# VAL-05 Regression Test Report

## Regression Test Run

**Run date:** 2026-04-18
**Command:**
```bash
python3 -m unittest \
  tests.test_scene_runtime.TestPostMeetingRegression \
  tests.test_scene_runtime.TestCustomerRecentStatusRegression \
  tests.test_archive_refresh_scene.TestArchiveRefreshRegression \
  tests.test_cohort_scan.TestCohortScanRegression \
  tests.test_meeting_prep_scene.TestMeetingPrepRegression \
  tests.test_proposal_scene.TestProposalRegression \
  -v
```
**Result:** 24 passed, 0 failed, 0 errors
**Duration:** ~242 seconds

## Coverage Summary

All 24 VAL-05 coverage paths verified:

| Scene | Happy-Path | Limited-Context | Unresolved-Customer | Blocked-Write | Test Class |
|-------|------------|-----------------|---------------------|---------------|------------|
| post-meeting-synthesis | ok | ok | ok | ok | TestPostMeetingRegression |
| customer-recent-status | ok | ok | ok | ok | TestCustomerRecentStatusRegression |
| archive-refresh | ok | ok | ok | ok | TestArchiveRefreshRegression |
| cohort-scan | ok | ok | ok | ok | TestCohortScanRegression |
| meeting-prep | ok | ok | ok | ok | TestMeetingPrepRegression |
| proposal | ok | ok | ok | ok | TestProposalRegression |

Total: 6 scenes x 4 case types = 24 coverage paths

## Scope Note

`todo-capture-and-update` is EXCLUDED from VAL-05 regression (shipped in v1.1, not part of v1.2 scope).
