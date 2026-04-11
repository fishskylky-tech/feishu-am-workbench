# Meeting Output Standard

Use this file when producing the final user-facing result for a meeting note, transcript, or post-meeting update.

The goals are:

- keep the structure stable across runs
- keep headings in Chinese
- separate facts, judgment, and recommendations
- make the output auditable when context recovery was used
- make `建议态更新` depend on actual extracted entities, not on a fixed template

## Recommended output sections

For a real post-meeting output, prefer this order:

1. `会议定性`
2. `上下文恢复说明`
3. `会议已确认事实`
4. `基于事实的经营判断`
5. `建议的推进方向`
6. `按 Workbench 口径的结构化摘要`
7. `建议态更新`
8. `待确认项 / Blocked 项`

If one section is truly empty, say so explicitly instead of silently skipping it.

## Heading language rule

Keep section headings and structured-summary labels in Chinese by default.

Avoid mixed labels such as:

- `resolved_customer`
- `meeting_type`
- `write_ceiling`
- `facts_vs_judgment`

Prefer:

- `客户解析`
- `会议类型`
- `写回上限`
- `事实与判断`

## Required distinctions

The output should clearly distinguish:

- `会议已确认事实`
- `基于事实的经营判断`
- `建议的推进方向`

Do not let a strong recommendation appear as if it were a confirmed meeting conclusion.

## Context recovery section

`上下文恢复说明` should include:

- `上下文恢复状态`
- `已使用资料`
- `关键补充背景`
- `未找到但应存在的资料`

If the run is only a single-file fallback, say so explicitly.

## Structured summary section

`按 Workbench 口径的结构化摘要` should use Chinese labels such as:

- `客户解析`
- `会议类型`
- `写回上限`
- `参会人`
- `风险`
- `机会`
- `待办建议`
- `时间节点`
- `事实与判断`

These labels are a stable interface for repeated use.

## Dynamic recommendation-mode updates

`建议态更新` must be driven by the actual extracted entities in this case.
It is not a fixed list of the same few objects every time.

If the meeting yields new items in any of these dimensions, consider them individually:

- `客户联系记录`
- `行动计划`
- `客户关键人地图`
- `竞品交锋记录`
- `合同清单`
- `客户档案`
- `客户主数据`
- `Feishu Todo`

For each relevant object, output:

- `对象`
- `建议动作`
  - create / update / no-write / blocked
- `依据`
- `关键信息`
- `当前限制`

Only include objects that are actually implicated by the extraction bundle.

## Time section rule

`时间节点` should contain only:

- confirmed dates from the meeting or supporting records, or
- explicitly partial-precision absolute dates

If a date is your suggested next step rather than a confirmed schedule item, move it to:

- `建议的推进方向`
or
- `建议态更新`

Do not mix recommendation with confirmed schedule.
