# Phase 2: Live Runtime Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-15
**Phase:** 2-Live Runtime Hardening
**Areas discussed:** 资源来源边界, 诊断输出口径, 客户解析策略, 加固目标范围

---

## 资源来源边界

| Option | Description | Selected |
|--------|-------------|----------|
| 只认私有运行时源 | 运行时正式 source of truth 只来自私有运行时输入，不允许 repo 文档参与 live 资源判定 | ✓ |
| 保留仓库文档兜底 | 当私有输入不全时，仍允许 repo 文档或示例文件参与 live 推断 | |
| 双层模式 | 私有输入优先，但 repo 文档仍可作为弱兜底层 | |

**User's choice:** 只认私有运行时源
**Notes:** Repo 文档可以保留为说明或示例，但不能再成为 live 解析链路中的 truth source。

## 正式入口

| Option | Description | Selected |
|--------|-------------|----------|
| shell env | 把进程环境中的私有变量定义为当前正式入口 | ✓ |
| 本地 .env | 把本地 `.env` 也定义成正式私有入口 | |
| 私有配置文件 | 额外引入新的私有配置文件入口 | |
| 先不扩新入口 | 不新增其它正式入口 | |

**User's choice:** shell env
**Notes:** 当前 contract 收敛到进程环境，不在本次讨论里扩展新的正式输入面。

## .env 地位

| Option | Description | Selected |
|--------|-------------|----------|
| 仍算正式入口 | `.env` 继续作为正式私有运行时源之一 | |
| 只作便利层 | `.env` 可以把值灌进环境变量，但不再作为独立 source contract | ✓ |
| 完全移除 | Phase 2 后不再支持 `.env` | |

**User's choice:** 只作便利层
**Notes:** 这保留本地开发便利性，同时避免 runtime 语义上出现两套 source of truth。

## 缺失行为

| Option | Description | Selected |
|--------|-------------|----------|
| 硬失败并给诊断 | 缺失必需私有输入时，直接阻断 live 路径并输出明确缺失项/修复建议 | ✓ |
| 允许部分运行 | 只阻断依赖缺失资源的动作，其他链路继续 | |
| 静默兜底到仓库文档 | 缺失时继续从 repo 文档猜测资源 | |

**User's choice:** 硬失败并给诊断
**Notes:** 失败应该显式、可修复，不能再用 repo 文档把状态伪装成“还能跑”。

## the agent's Discretion

- 若现有实现或文档仍把 `.env` 写成并列真源，可在 Phase 2 计划中收紧表述，但不需要在本讨论里直接改 requirement 编号或 phase 范围。

## 诊断输出口径

| Option | Description | Selected |
|--------|-------------|----------|
| 三档+行动建议 | 用 available / degraded / blocked 三档表达状态，并默认给出结论、原因、下一步建议 | ✓ |
| 只给简短结论 | 只告诉用户当前能不能继续，不展开原因和建议 | |
| 更细技术分层 | 输出更多技术状态层级，偏向调试视角 | |

**User's choice:** 三档+行动建议
**Notes:** 输出优先服务日常使用判断，不把诊断做成偏工程调试的内部台账。

## 客户解析策略

| Option | Description | Selected |
|--------|-------------|----------|
| 精确优先，唯一候选可过，歧义停下确认 | 完全匹配优先；若只剩一个明显候选可自动通过；只要歧义就不猜 | ✓ |
| 更激进自动匹配 | 允许更宽松的名称近似匹配并自动选中 | |
| 全部人工确认 | 除完全精确命中外，其余情况一律要求人工确认 | |

**User's choice:** 精确优先，唯一候选可过，歧义停下确认
**Notes:** 用户接受保守自动化，但不接受在多候选场景下替他猜。

## 加固目标范围

| Option | Description | Selected |
|--------|-------------|----------|
| 只打地基 | Phase 2 只收敛在 runtime 真源、启动诊断、客户识别，不顺手扩业务能力 | ✓ |
| 顺手并进更多 live 能力 | 在加固同时推进更多读取能力或业务判断 | |
| 尽量一次做宽 | 借 Phase 2 一次性把基础和部分业务增强一起做掉 | |

**User's choice:** 只打地基
**Notes:** 目标是减少后续返工，不让基础 phase 因 scope 扩张失焦。

## Deferred Ideas

None.