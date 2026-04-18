# Phase 18: Account Posture And Cohort Scanning - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 18-account-posture-and-cohort-scanning
**Areas discussed:** Account posture lenses, Cohort definition input, Cohort output format, Cohort recommendations

---

## Account Posture Lenses

| Option | Description | Selected |
|--------|-------------|----------|
| 标签子项式（推荐） | 判断里每个结论带风险/机会/关系/进展标签，分开可读 | ✓ |
| 结构化字段式 | payload 里单独放 account_posture 字典，精确但可读性降低 | |
| 固定四 section | 和会后四个 section 一样，每个角度一个固定区块 | |

**User's choice:** 标签子项式（推荐）
**Notes:** 带标签的子项方式，每个角度 1-3 条，精炼可读

---

## STAT-01 Scene Form

| Option | Description | Selected |
|--------|-------------|----------|
| 升级现有场景（推荐） | 复用 customer-recent-status，增加四角度 lens 输出 | ✓ |
| 新建独立场景 | 新建 account-posture scene，保留原有 recent-status 独立存在 | |

**User's choice:** 升级现有场景（推荐）
**Notes:** STAT-01 作为 customer-recent-status 场景升级实现

---

## Cohort Definition Input

| Option | Description | Selected |
|--------|-------------|----------|
| 标签/分类为主（推荐） | 用客户主数据的标签/分类筛选，手动列表补充 | |
| 动态条件查询 | 用户描述条件，如「最近三月有动态的所有客户」 | ✓ |
| 手动勾选列表 | 每次从客户列表里勾选，精确但不可复用 | |

**User's choice:** 动态条件查询
**Notes:** 用户通过动态条件描述客户群（如「最近三月有动态的客户」）

---

## Cohort Scan Limit

| Option | Description | Selected |
|--------|-------------|----------|
| 上限10个（推荐） | 超出提示收窄范围，保证输出质量 | |
| 上限20个 | 稍大，但输出可能膨胀 | |
| 无硬性上限 | 按条件全部扫描，用户自己控制量 | |
| 可配置项，默认 10 个 | 做成可配置项，默认 10 个 | ✓ |

**User's choice:** 做成可配置项，默认 10 个
**Notes:** 扫描上限可配置，默认 10 个；超出时提示用户收窄

---

## Cohort Output Structure

| Option | Description | Selected |
|--------|-------------|----------|
| 聚合摘要+重点客户（推荐） | 先给这类客户的整体信号和问题，再列需重点关注的客户 | ✓ |
| 全部逐一分列 | 每个客户一条结论，按风险/机会排序 | |
| 纯聚合，不分列 | 只给整体信号和共性问题，不逐个分析 | |

**User's choice:** 聚合摘要+重点客户（推荐）
**Notes:** 聚合摘要 + 重点客户，2-3 条共通信号/问题 + 3-5 个重点客户

---

## Cohort Recommendation Format

| Option | Description | Selected |
|--------|-------------|----------|
| 群体+重点个人（推荐） | 群体共性建议 + 风险最高/机会最大客户的个别跟进建议 | ✓ |
| 仅群体建议 | 只给这类客户的整体建议，不落到具体客户 | |
| 全部给个别建议 | 每个客户都给出建议，标注优先级 | |

**User's choice:** 群体+重点个人（推荐）
**Notes:** 建议形态为「群体共性建议 + 重点客户的个别跟进建议」

---

## Deferred Ideas

- SCAN-02 (scheduled or semi-automatic customer scanning) — future requirement, out of scope for Phase 18

