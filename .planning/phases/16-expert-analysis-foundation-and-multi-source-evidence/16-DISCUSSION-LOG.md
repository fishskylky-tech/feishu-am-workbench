# Phase 16: Expert Analysis Foundation And Multi-Source Evidence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 16-expert-analysis-foundation-and-multi-source-evidence
**Areas discussed:** Evidence Assembly Strategy, Expert-analysis Orchestration Location, Fallback Preservation Rules

---

## Evidence Assembly Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| A: Loose拼接 | Each scene receives raw materials and decides how to use them. Flexible but scenes repeat work. | |
| B: Unified Container | All evidence collected into a structured EvidenceContainer with source labels, quality indicators, and missing-source flags before passing to any scene. | ✓ |

**User's choice:** B — 统一容器方案
**Notes:** 收纳盒保证材料格式一致，场景用起来更省心。每个场景不用重复操心材料整理。

---

## Expert-analysis Orchestration Location

| Option | Description | Selected |
|--------|-------------|----------|
| A: Per-scene | Each scene implements its own analysis logic. Fully autonomous but code duplication. | |
| B: Shared Helper | Common patterns (multi-source weighting, judgment priority, conflict detection) extracted into a shared ExpertAnalysisHelper utility. Scenes decide when and how to use it. | ✓ |

**User's choice:** B — 共享工具箱方案
**Notes:** 专家判断逻辑有很多是相通的，工具箱避免重复代码，但工具箱要克制——只提供拼装指南，具体判断由场景自己做。场景代码必须保持可读性。

---

## Fallback Preservation Rules

| Option | Description | Selected |
|--------|-------------|----------|
| A: Hard stop on missing | Any key source missing → scene stops with "cannot proceed". | |
| B: Continue with honest annotation | Scene continues with explicit fallback visibility; results show which sources were used, which missing, and how that affects confidence. Safety boundary unchanged. | ✓ |

**User's choice:** B — 底线继续模式
**Notes:** AM 工作中完美材料组合很少见，缺一个就停不现实。但结果必须诚实标注缺了什么，让用户决定是否补全。安全边界不变——即使材料不全，写操作仍然被 guard 拦住。

---

## Claude's Discretion

- Exact naming of the EvidenceContainer class and its fields
- Exact threshold for "critical source missing" (hard stop vs soft warning)
- Exact internal structure of the ExpertAnalysisHelper, as long as scene code remains readable

## Deferred Ideas

- None — discussion stayed within Phase 16 scope.
