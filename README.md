# feishu-am-workbench

Feishu AM Workbench 是一个面向客户经营工作的飞书技能仓库。它的目标不是做一个更长的 prompt，而是把 AM 高频工作沉淀成一套 live-first、recommendation-first、可验证的工作流。

当前仓库已经形成一条可运行的最小闭环：

- 先恢复客户上下文，再给经营判断
- 先给推荐方案，再确认写回
- 先做 schema preflight 和 write guard，再触发变更

它优先服务的不是抽象平台化，而是你每天真的会用到的会前准备、会后整理、客户状态跟进和 Todo 执行闭环。

## 当前能力边界

当前最成熟、验证最完整的是 scene runtime 主路径：

1. 通过 runtime 做资源探测、客户解析和 capability diagnostics
2. 在 `post-meeting-synthesis`、`customer-recent-status`、`archive-refresh`、`todo-capture-and-update` 里按共享 contract 恢复最小必要 live context
3. 输出审计化结果，包括资源状态、客户结果、上下文恢复状态、已使用资料、写回上限和开放问题
4. 在确认后让需要写回的场景继续走统一 Todo writer 的 preflight、guard、dedupe 和执行结果归一

这意味着当前仓库已经不是“会议总结器”，而是一个带飞书工作台底座的 AM operating workflow。

## 核心原则

### Live-first

- 会议类场景优先尝试 live runtime，而不是把单份材料当成全部事实
- live schema 和 live options 是写前真相，缓存只能做兼容或加速

### Recommendation-first

- 默认先给建议，不直接写回
- 高风险主数据更新必须保持受控
- 缺 owner、schema 不匹配、证据冲突时，宁可阻断也不盲写

### Thin foundation

- runtime 负责资源解析、客户解析、targeted read、schema preflight、write guard 和 normalized writer surface
- scene 层负责决定读什么、如何判断、给什么建议
- foundation 不默认拼装完整业务上下文

## 工作台信息层次

当前 workbench 仍然遵循稳定的层次分工：

- `客户主数据`: 客户索引与快照层
- detail tables: `客户联系记录`、`行动计划`、`合同清单`、`客户关键人地图`、`竞品交锋记录`
- `客户档案`: 长周期叙事和经营解释层
- Feishu Todo: 执行与提醒载体

这套分层决定了 skill 的路由方式，也决定了后续 scene skill 不应按表拆，而应按经营场景拆。

## 目标架构方向

当前仓库仍以一个根级 skill 为入口，但已经明确了后续演进方向：

- 主 skill 保持薄入口和编排层
- 新能力按 scene skill 方式扩展，而不是继续向根级 SKILL.md 堆规则
- scene skill 在需要时按需调用专家 agent
- 所有 scene 复用同一个 runtime foundation
- 初始化安装、兼容性检查、config 生成、cache 刷新等能力走独立 admin/bootstrap path

当前与目标的边界需要同时成立：

- current state: 根级 skill 仍然是唯一正式入口，scene skill 目录化还没有作为运行时事实落地
- target state: 根级入口只保留路由与顶层交互，scene skills 承载工作流规则，expert agents 作为场景内协作者按需拉起

Phase 7 的 canonical architecture references：

- [references/scene-skill-architecture.md](references/scene-skill-architecture.md)
- [references/workspace-bootstrap.md](references/workspace-bootstrap.md)
- [references/cache-governance.md](references/cache-governance.md)

当前已经锁定的第一波 scene 方向是：

- `post-meeting-synthesis`
- `customer-recent-status`
- `archive-refresh`
- `todo-capture-and-update`

其中第一组 `post-meeting-synthesis` 和 `customer-recent-status` 已完成可执行 runtime 落地；第二组 `archive-refresh` 和 `todo-capture-and-update` 已按同一 contract 定义并接入 runtime surface。

## 快速开始

### 前置条件

1. Python 3.10+
2. 已安装并可用 `lark-cli`
3. 已完成飞书认证并具备 Base、Drive、Task 的目标访问权限
4. 本地有可用 Python 环境，推荐直接使用仓库内 `.venv`

### 1. 激活环境

```bash
source .venv/bin/activate
```

### 2. 准备本地运行时输入

在仓库根目录准备本地 `.env`，填入你的 `FEISHU_AM_*` 变量。真实 token、folder token、tasklist guid 不应提交到仓库。

常见项包括：

- `FEISHU_AM_WORKBENCH_BASE_URL`
- `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`
- `FEISHU_AM_MEETING_NOTES_FOLDER`
- `FEISHU_AM_TODO_TASKLIST_GUID`
- `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID`
- `FEISHU_AM_TODO_PRIORITY_FIELD_GUID`

### 3. 先跑 capability 诊断

```bash
python3 -m runtime .
```

理想状态是：

- `base_access: available`
- `docs_access: available`
- `task_access: available`

### 4. 再跑会议主路径验证

```bash
python3 -m evals.meeting_output_bridge \
  --eval-name unilever-stage-review \
  --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt \
  --run-gateway \
  --customer-query 联合利华
```

重点观察：

- `资源状态`
- `客户结果`
- `上下文恢复状态`
- `已使用资料`
- `写回上限`
- `开放问题`

### 4.5 优先走 canonical scene runtime 入口

最近完成并已归档的主线 milestone：v1.1 Executable Scene Runtimes。

Phase 12 开始，runtime 的长期主入口是稳定 `scene` 名称，而不是继续增加一串一次性 operator 命令。

先预览 canonical post-meeting scene：

```bash
python3 -m runtime scene post-meeting-synthesis   --eval-name unilever-stage-review   --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt   --customer-query 联合利华
```

如果你已经确认要执行当前建议态 Todo 写回，再显式加 `--confirm-write`。如果需要把结果接到脚本或别的 agent，再加 `--json`：

```bash
python3 -m runtime scene post-meeting-synthesis   --eval-name unilever-stage-review   --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt   --customer-query 联合利华   --confirm-write   --json
```

旧的 `meeting-write-loop` 仍保留，但现在只作为 `post-meeting-synthesis` 的 compatibility wrapper，而不是长期 contract 本体：

```bash
python3 -m runtime meeting-write-loop   --eval-name unilever-stage-review   --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt   --customer-query 联合利华
```

再看客户近期状态：

```bash
python3 -m runtime scene customer-recent-status \
  --customer-query 联合利华 \
  --repo-root . \
  --json
```

如果你要先整理 archive refresh 的建议态输入：

```bash
python3 -m runtime scene archive-refresh \
  --customer-query 联合利华 \
  --topic-text 客户档案 \
  --repo-root . \
  --json
```

如果你已经有 follow-on 项，想先走统一 Todo contract 的候选整理：

```bash
python3 -m runtime scene todo-capture-and-update \
  --customer-query 联合利华 \
  --todo-item-json '{"summary":"确认联合利华复盘结论","owner":"ou_owner","priority":"高","due_at":"2026-04-20"}' \
  --repo-root . \
  --json
```

### 5. 跑自动化切片

```bash
python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q
```

## 仓库导航

- [ARCHITECTURE.md](ARCHITECTURE.md)
  - 当前实现边界与 phase 7 锁定的目标架构口径
- [references/scene-skill-architecture.md](references/scene-skill-architecture.md)
  - scene skills、expert agents 与 first-wave boundary 的 canonical contract
- [references/scene-runtime-contract.md](references/scene-runtime-contract.md)
  - shared scene contract、fallback visibility、write ceiling 与 non-bypass runtime boundary
- [references/workspace-bootstrap.md](references/workspace-bootstrap.md)
  - admin/bootstrap path 的最小交付物、compatibility 与强确认边界
- [references/cache-governance.md](references/cache-governance.md)
  - schema、manifest/index、semantic cache 的 trust hierarchy 与 refresh lifecycle
- [CONFIGURATION.md](CONFIGURATION.md)
  - 本地环境、workspace config 边界、bootstrap 与 cache 关系
- [GETTING-STARTED.md](GETTING-STARTED.md)
  - 首次跑通诊断与会议样例的最短路径
- [DEVELOPMENT.md](DEVELOPMENT.md)
  - 日常开发节奏、文档同步点和 phase/GSD 协作方式
- [TESTING.md](TESTING.md)
  - 自动化切片、人工 live 验证和文档一致性检查
- [STATUS.md](STATUS.md)
  - 当前实际实现状态与下一步主线
- [ROADMAP.md](ROADMAP.md)
  - 产品与经营能力演进方向

## 当前版本

- 版本：0.2.14
- 当前状态：v1.0 phases 1-11 与 v1.1 phases 12-15 都已完成并归档；v1.1 closeout artifacts 已补齐
- 当前主线：暂无新的 mainline milestone；下一步是定义新里程碑，或可选处理 backlog 999.1

## 后续建议

如果你现在要继续推进仓库：

1. 定义新的 mainline milestone，把 bootstrap/admin operator path 或下一轮 validation 收口目标正式写进 requirements / roadmap
2. 可选处理 backlog 999.1，但它只是 historical metadata cleanup，不阻塞主线推进
3. 在新 milestone 开始前，继续沿 canonical scene runtime 入口做日常验证与 live workspace 使用


## 安装

当前仓库没有 `pyproject.toml`、`requirements.txt` 或 `package.json` 这类声明式依赖清单；Python 侧实现以标准库为主，live 集成通过本机 `lark-cli` 可执行文件完成。因此安装路径是先准备本地仓库副本、Python 虚拟环境和 `.env`，再确认 `lark-cli` 已完成授权。

```bash
cd /path/to/feishu-am-workbench
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

完成后再补齐 `.env` 中对应的 `FEISHU_AM_*` 变量，并确保 `lark-cli` 已在当前 shell 的 `PATH` 中可用。

## 使用示例

### 1. 输出当前 live capability 诊断

```bash
python3 -m runtime diagnose . --json
```

适合先确认 Base、Drive/Docs、Task 三类资源是否可用。返回结果里重点看 `base_access`、`docs_access`、`task_access`。

### 2. 跑一条 post-meeting scene 主路径

```bash
python3 -m runtime scene post-meeting-synthesis   --eval-name unilever-stage-review   --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt   --customer-query 联合利华   --json
```

这个入口会走共享 scene runtime contract，输出结构化审计结果，包括资源状态、客户解析、上下文恢复、写回上限和开放问题。

### 3. 先生成 Todo 候选而不直接写回

```bash
python3 -m runtime scene todo-capture-and-update   --customer-query 联合利华   --todo-item-json '{"summary":"确认联合利华复盘结论","owner":"ou_owner","priority":"高","due_at":"2026-04-20"}'   --repo-root .   --json
```

默认行为是建议态候选整理，不会绕过 preflight 和 guard 直接落写；只有显式加 `--confirm-write` 时才会进入统一 Todo writer 执行路径。
