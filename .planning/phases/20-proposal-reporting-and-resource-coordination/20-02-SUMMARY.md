# Phase 20 Plan 02: Proposal Routing Integration Summary

## One-liner
Added Feishu-native output routing per WRITE-01 and type-based dispatch for proposal/report/resource-coordination routing to Drive, Base, or Task.

## Plan Details
- **Phase:** 20-proposal-reporting-and-resource-coordination
- **Plan:** 02
- **Type:** execute
- **Wave:** 2
- **Requirements:** PROP-01, WRITE-01
- **Status:** COMPLETED

## Tasks Completed

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Add proposal routing helper functions to scene_runtime.py | DONE | - |
| 2 | Update run_proposal_scene() with routing integration | DONE | - |
| 3 | Update build_proposal_checklist() with proposal_type parameter | DONE | - |

## Files Modified

| File | Changes |
|------|--------|
| runtime/scene_runtime.py | Added _infer_proposal_output_destination(), _extract_action_items_from_proposal(), _build_proposal_routing_payload() after _render_proposal_output(); updated run_proposal_scene() to pass proposal_type to checklist, build routing_payload, and include routing recommendation in output |
| runtime/confirmation_checklist.py | Added optional proposal_type parameter to build_proposal_checklist() and updated proposal_type ChecklistItem to use the passed parameter as system_suggestion |

## Key Implementation Details

### Type-Based Routing per D-12
- **proposal/report** -> routes to Drive (customer archive folder or existing archive doc)
- **resource-coordination** -> routes to Base 行动计划 table or Task module

### Three New Helper Functions
1. **_infer_proposal_output_destination()**: Returns human-readable destination string based on proposal_type
2. **_extract_action_items_from_proposal()**: Extracts action items from resource_asks and open_questions for resource-coordination type only
3. **_build_proposal_routing_payload()**: Builds routing payload with destination_type (drive_doc/base_table/task), target, content, customer, and action_items

### Updated run_proposal_scene() per D-11
- Passes proposal_type to build_proposal_checklist() for type-specific suggestion
- Builds confirmed_destination from checklist.confirmed_answers() or falls back to _infer_proposal_output_destination()
- Builds routing_payload via _build_proposal_routing_payload()
- Adds routing recommendation "建议输出至: {confirmed_destination}" to recommendations list
- Includes routing_payload in scene_result payload

### Updated build_proposal_checklist() per D-14
- Added optional proposal_type parameter (default "proposal")
- proposal_type ChecklistItem now uses the passed parameter as system_suggestion

## Verification
```bash
python -c "
from runtime.scene_runtime import _infer_proposal_output_destination, _build_proposal_routing_payload

# Test proposal type destination
dest = _infer_proposal_output_destination(None, 'proposal')
assert 'Drive' in dest

# Test report type destination
dest = _infer_proposal_output_destination(None, 'report')
assert 'Drive' in dest

# Test resource-coordination destination
dest = _infer_proposal_output_destination(None, 'resource-coordination')
assert 'Base' in dest or 'Task' in dest

# Test routing payload for proposal
payload = _build_proposal_routing_payload('proposal', 'Drive 客户档案文件夹', {'objective': ['目标1'], 'core_judgment': [], 'main_narrative': [], 'resource_asks': [], 'open_questions': []}, {'customer_id': 'test', 'short_name': 'Test'})
assert payload['destination_type'] == 'drive_doc'

# Test routing payload for resource-coordination
payload = _build_proposal_routing_payload('resource-coordination', 'Base 行动计划表', {'objective': [], 'core_judgment': [], 'main_narrative': [], 'resource_asks': ['资源1'], 'open_questions': []}, {'customer_id': 'test', 'short_name': 'Test'})
assert payload['destination_type'] in ('base_table', 'task')

print('All routing tests passed')
"
```

## Deviations from Plan
None - plan executed exactly as written.

## Auth Gates
None.
