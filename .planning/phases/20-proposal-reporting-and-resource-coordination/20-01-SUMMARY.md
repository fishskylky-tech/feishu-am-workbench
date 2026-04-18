# Phase 20 Plan 01: Proposal Scene Core Infrastructure Summary

## One-liner
Implemented the `proposal` scene with five-dimension output structure (objective, core_judgment, main_narrative, resource_asks, open_questions) and type-based dispatch for proposal/report/resource-coordination.

## Plan Details
- **Phase:** 20-proposal-reporting-and-resource-coordination
- **Plan:** 01
- **Type:** execute
- **Wave:** 1
- **Requirements:** PROP-01, WRITE-01
- **Status:** COMPLETED

## Tasks Completed

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Add build_proposal_checklist() to confirmation_checklist.py | DONE | - |
| 2 | Add five-dimension keyword sets and lens derivation to scene_runtime.py | DONE | - |
| 3 | Add run_proposal_scene() to scene_runtime.py | DONE | - |
| 4 | Register proposal scene in scene_registry.py | DONE | - |

## Files Modified

| File | Changes |
|------|---------|
| runtime/confirmation_checklist.py | Added build_proposal_checklist() with scene_name="proposal", WRITE-02 universal items (audience, purpose, internal_external, resource_coordination), and scene-specific items (proposal_type, output_destination) |
| runtime/scene_runtime.py | Added five-dimension keyword sets (_PROPOSAL_OBJECTIVE_KEYWORDS, _PROPOSAL_JUDGMENT_KEYWORDS, _PROPOSAL_NARRATIVE_KEYWORDS, _PROPOSAL_RESOURCE_KEYWORDS, _PROPOSAL_QUESTION_KEYWORDS), _PROPOSAL_LENS_SOURCE_MAP, _derive_proposal_lenses(), _render_proposal_output(), run_proposal_scene(), and updated import to include build_proposal_checklist |
| runtime/scene_registry.py | Added import for run_proposal_scene and registry.register("proposal", run_proposal_scene) |

## Key Implementation Details

### Five-Dimension Keyword Sets
- **objective:** {"目标", "目的", "意图", "期望", "想要达成", "规划"}
- **judgment:** {"判断", "评估", "结论", "认为", "核心是", "关键点", "重点"}
- **narrative:** {"叙事", "说明", "阐述", "背景", "情况", "现状", "原因", "历程"}
- **resource:** {"资源", "支持", "协助", "需要", "请求", "投入", "预算", "人力", "时间", "资源需求"}
- **question:** {"待确认", "待定", "不确定", "需确认", "疑问", "问题", "待解决"}

### Type-Specific Emphasis (per D-07)
- **proposal:** Emphasizes core_judgment (up to 4 items) + main_narrative
- **report:** Emphasizes main_narrative (up to 3 items)
- **resource-coordination:** Emphasizes resource_asks (up to 4 items)

### Confirmation Checklist (per D-10)
- Pre-scene checklist shown BEFORE scene output
- WRITE-02 universal items: audience, purpose, internal_external, resource_coordination
- Scene-specific items: proposal_type, output_destination (inferred from EvidenceContainer)

## Verification
```bash
python -c "
from runtime.scene_registry import build_default_scene_registry
registry = build_default_scene_registry()
assert 'proposal' in registry.available_scenes()
print('proposal scene registered OK')
"
```

## Deviations from Plan
None - plan executed exactly as written.

## Auth Gates
None.
