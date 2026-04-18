# Phase 21: Validation And Milestone Closure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 21-validation-and-milestone-closure
**Areas discussed:** Regression coverage strategy, Test organization, Documentation alignment scope, Milestone closeout structure

---

## Area: Regression Coverage Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Full matrix | 6 scenes × 4 case types = 24 coverage paths | ✓ |
| Critical path priority | 3高频场景 × 4 case + 3低频场景 happy-path + 1 fallback | |
| Scene-contract only | 只测 dispatch 契约，不区分 case type | |

**User's choice:** Full matrix
**Notes:** User confirmed full matrix coverage for all 6 scenes × 4 case types

---

## Area: Test Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Per-scene files | 每个 scene 独立测试文件，4 case types 在文件内覆盖 | ✓ |
| Unified validation file | 单一大文件集中覆盖全部场景 | |
| Expand existing files | 扩展现有 tests/ 文件 | |

**User's choice:** Per-scene files
**Notes:** User initially asked for tradeoffs; after explanation chose per-scene as recommended option

---

## Area: Documentation Alignment Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All docs listed | scene-runtime-contract, scene-skill-architecture, SKILL.md, README.md, CHANGELOG.md, VERSION, VALIDATION.md | ✓ |
| Critical docs only | SKILL.md, VERSION, CHANGELOG.md only | |
| SKILL + runtime contract only | Only SKILL.md and scene-runtime-contract | |

**User's choice:** All docs + two additional requirements:
1. README and CHANGELOG written from business scenario and value perspective (minimize non-technical barriers)
2. ROADMAP phases need completion status so roadmap progress is visible at a glance
**Notes:** Version number must also be aligned

---

## Area: Milestone Closeout Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror v1.1 structure | v1.2-MILESTONE-AUDIT + v1.2-ROADMAP + v1.2-REQUIREMENTS + milestone index | |
| Extended v1.1 structure | Standard structure + VAL-05 traceability matrix + regression test report | ✓ |
| Minimal closeout | Only靠各 phase VERIFICATION.md 自证明，不写 milestone audit | |

**User's choice:** Extended v1.1 structure
**Notes:** User initially asked for clarification; after explanation deferred to my recommendation which was Extended v1.1 (larger scope of v1.2 + VAL-05 explicit requirement for regression coverage evidence justifies extended structure)

---

## Claude's Discretion

None — all decisions made by user explicitly.

## Deferred Ideas

None — discussion stayed within Phase 21 scope.

