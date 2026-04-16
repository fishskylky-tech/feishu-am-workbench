# Codebase Map: Integrations

## External Systems

### Feishu Base

- Live Base token is resolved from private runtime sources.
- Verified live base currently contains 8 tables:
  - 客户主数据
  - 合同清单
  - 行动计划
  - 客户关键人地图
  - 竞品基础信息表
  - 竞品交锋记录
  - 客户联系记录
  - 潜在客户池
- Runtime treats Base as the source of truth for customer resolution and business context.

### Feishu Drive / Docs

- Customer archive folder is live and readable.
- Current top-level archive directory mixes:
  - customer archive docs
  - a 会议记录 folder
  - a 资讯周报 folder
  - a 客户档案模板 doc
- Meeting notes are stored as separate docs under the 会议记录 folder.

### Feishu Task

- Current user-visible task module exposes one primary tasklist: 神策.
- Runtime already uses tasklist discovery, owner checks, and custom field metadata for Todo writes.
- Todo writer is the first normalized writer surface in the runtime.

### GitHub

- Remote repo: fishskylky-tech/feishu-am-workbench
- Visibility: private
- Collaboration signals already exist in:
  - Issues
  - PRs
  - Discussions
  - Projects v2

## Integration Boundaries

- The runtime is intentionally local and personal-workflow oriented.
- Secrets and live resource identifiers must stay in env/private runtime sources.
- Write execution is guarded and should remain recommendation-first unless explicitly confirmed.
- No external CRM or data warehouse integration exists yet.

## Integration Risks

- Feishu schema drift and custom field changes can break writes.
- Personal drive folder layout and tasklist configuration are not yet generalized for other AMs.
- Duplicate archive docs already exist for at least one customer and can confuse archive routing.