---
title: Meeting Note Doc Standard
load_triggers:
  - skill_stage: [doc-write, meeting-doc-creation]
  - task_type: [post-meeting]
load_priority: medium
estimated_tokens: 332
dependencies: [meeting-output-standard]
tier: L3-scenario-meeting
---

# Meeting Note Doc Standard

Use this file when the skill proposes or creates a meeting-note cold-memory doc.

The default principle is:

- do not store a raw transcript as the formal meeting note doc

The formal doc should be a structured note derived from the source material.
The source transcript remains a source, not the final artifact.

## Recommended doc structure

1. Meeting background
2. Participants
3. Confirmed facts
4. Discussion and analysis
5. Open questions
6. Recommended next actions
7. Source records

## Writing rules

- Clearly separate confirmed facts from interpretation.
- Do not rewrite speculative discussion as if it were a decision.
- Do not omit important uncertainty just to make the note sound cleaner.
- Preserve exact dates where known.
- When precision is partial, preserve that partial absolute form explicitly.

## Source record section

The doc should include the origin of the note, for example:

- original transcript file path
- related meeting record link
- related archive or contact-log references used during synthesis

Do not rely on memory without citing the source record basis.

## AI disclosure

The note should carry a short disclosure such as:

`本纪要由 AI 基于会议逐字稿及相关资料整理生成，用于经营沉淀与协作参考。已确认事实、分析判断与待确认项已分开展示；如与原始记录冲突，以原始记录及业务负责人确认结果为准。`

## Raw transcript handling

If the user wants the raw transcript preserved:

- keep it as source material
- do not present it as the formal meeting note by default

If no structured note can be safely produced:

- do not create the formal meeting-note doc yet
- return recommendation mode with the reason
