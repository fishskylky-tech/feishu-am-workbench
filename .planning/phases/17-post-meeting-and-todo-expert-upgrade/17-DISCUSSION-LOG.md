# Phase 17: Post-Meeting And Todo Expert Upgrade - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 17-post-meeting-and-todo-expert-upgrade
**Areas discussed:** Post-meeting output format, Todo intent classification structure, Expert rationale storage

---

## Post-Meeting Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| 结构化列表 | 2-5 bullet points per section, concise and scannable | ✓ |
| 段落式分析 | One paragraph per section with full context and logic | |
| 混合格式 | Lists for risk/opportunity, paragraphs for next-round path | |

**User's choice:** 结构化列表为主
**Notes:** AM workflow is fast-paced — need scannable output for quick review and copy into reporting materials. Next-round section may use short sentences.

---

## Todo Intent Classification Structure

| Option | Description | Selected |
|--------|-------------|----------|
| 固定四类 | Always use 风险干预/扩张推进/关系维护/项目进展, no exceptions | |
| 推荐四类+可扩展 | Default to four, but scene can add new categories when cases don't fit | ✓ |
| 不做预设 | Let expert decide category count based on actual situation | |

**User's choice:** 推荐四类 + 可扩展
**Notes:** Four categories cover ~80% of AM work. Extension via user tag or system auto-inference — both acceptable.

---

## Expert Rationale Storage Location

| Option | Description | Selected |
|--------|-------------|----------|
| 仅给用户看 | Display as human-readable text, not stored in structured field | |
| 结构化存储 | Stored in structured field for traceability and reuse | ✓ |
| 两者都要 | Both human-readable display and structured storage | |

**User's choice:** 结构化存储
**Notes:** Rationale needs to be traceable across sessions and reusable in archiving/reporting workflows.

---

## Follow-up Questions

**Q: Four category names — keep as-is or change?**
**User's choice:** Keep as-is (风险干预, 扩张推进, 关系维护, 项目进展)

**Q: Rationale field naming — English or Chinese?**
**User's choice:** 中文 (Chinese naming)

**Q: Who decides when to extend categories — user or system?**
**User's choice:** 都可以 (both acceptable)

---

## Deferred Ideas

None — discussion stayed within Phase 17 scope.

