# feishu-am-workbench

Feishu AM Workbench 是一个面向客户经营（AM）工作的飞书技能。

它不是单纯的“会议总结器”，而是一套帮助 AM 把日常工作做稳、做深、做成闭环的工作方法：

- 先恢复上下文，再给判断
- 先出建议，再确认写回
- 先做校验，再触发变更

目标是把 AM 的日常动作从“零散信息处理”，升级成“可追踪、可复盘、可持续优化”的经营闭环。

## 产品定位

这个技能的核心价值，不是“多写一份总结”，而是帮助 AM 把每天最耗精力的工作变得更稳、更快、更可持续。

它重点辅助 AM 做好四类日常工作：

1. 会前准备：快速恢复客户上下文，知道这次会要解决什么，不再临时拼信息。
2. 会后沉淀：把会议结论、待确认问题、后续动作拆清楚，减少“开完会就断线”。
3. 客户经营跟进：把分散在聊天、纪要、表格里的信号串成连续线程，避免遗漏关键动作。
4. 团队协同执行：把待办责任人、优先级和重复任务管住，让推进动作真正落地。

对应的业务结果是：

- 降低上下文切换成本，提升每次沟通的准备质量。
- 减少遗漏、误写和重复任务，提升执行确定性。
- 让客户经营从“靠记忆”变成“可追踪、可复盘、可优化”的工作流。

它背后的运行原则可以概括为三句：

- 先恢复上下文，再做判断。
- 先给执行建议，再确认落盘。
- 先保证写入安全，再追求自动化。

## 核心能力

### 1. 会前会后助手

- 支持会议纪要、逐字稿、会后整理输入
- 先恢复客户背景，不把单份纪要当成全部事实
- 输出中明确区分：事实、判断、开放问题、写回边界

### 2. 客户经营资产管理

- 将客户概况与过程记录分层管理
- 长文本沉淀在文档，表格保持结构化字段
- 在需要时关联客户档案和历史线程，避免脱离背景的结论

### 3. 统一 Todo 闭环

- 支持创建、更新、暂不写入、建议拆分子任务等决策
- 支持语义去重，减少重复任务与并行冲突

## 运行原则

### 上下文优先

- 会议类任务先恢复最小必要背景，再做结论
- 输出明确标注依据来源，方便复核和追踪

### 写入前防护

- 写入前先检查字段与选项是否匹配当前环境
- 写入前检查负责人与关键约束是否满足
- 不满足安全条件时保持建议模式

### 漂移兼容

- 优先使用当前环境中的真实字段与选项
- 同义词只用于辅助匹配，不作为盲写依据
- 兼容失败时宁可阻断写入，也不做不可解释变更

## 快速开始

### 前置条件

1. 已安装并可用 lark-cli
2. 已完成飞书认证并具备目标资源访问权限
3. 本地 Python 3.10+

### 安全配置指南

1. 使用 `.env.example` 作为模板，在本地创建 `.env` 并填入真实资源。
2. 真实 token、folder token、tasklist guid 只放环境变量，不提交到仓库。
3. `references/live-resource-links.example.md` 只保留示例值，用于说明格式。
4. 可选安装 pre-commit 并启用 `detect-secrets`：

```bash
pip install pre-commit
pre-commit install
```

`.env` 内容是什么：

- 这是本地运行时环境变量文件，保存你个人环境的 `FEISHU_AM_*` 配置。
- 典型键包括：`FEISHU_AM_BASE_TOKEN`、`FEISHU_AM_CUSTOMER_MASTER_TABLE_ID`、`FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`、`FEISHU_AM_MEETING_NOTES_FOLDER`、`FEISHU_AM_TODO_TASKLIST_GUID`。

`.env` 作用是什么：

- runtime 入口会显式读取仓库根目录 `.env`，把其中的 `FEISHU_AM_*` 注入进程环境，避免每次手动 export。
- 加载策略是“显式环境变量优先，`.env` 补充”。如果你已在 shell 中 export 同名变量，runtime 不会覆盖它。

### 1) 先跑环境诊断

```bash
python3 -m runtime .
```

如果三个核心能力都显示为 `available`，就可以进入真实验证。

### 2) 再跑会议场景验证

```bash
python3 -m evals.meeting_output_bridge \
  --eval-name unilever-stage-review \
  --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt \
  --run-gateway \
  --customer-query 联合利华
```

重点观察：资源解析状态、客户解析结果、上下文恢复状态、已使用资料。

### 3) 运行验证集

```bash
python3 -m unittest tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner tests.test_validation_assets
```

## 文档导航

如果你要继续在这个仓库里开发，而不是只做一次性试跑，建议配合以下文档一起看：

- [GETTING-STARTED.md](GETTING-STARTED.md)
  - 新环境首次上手、诊断和第一条会议验证路径
- [DEVELOPMENT.md](DEVELOPMENT.md)
  - 日常开发节奏、分支策略、改动边界和文档同步方式
- [TESTING.md](TESTING.md)
  - 自动化测试切片、人工验证项和发 PR 前检查清单
- [CONFIGURATION.md](CONFIGURATION.md)
  - `.env`、`FEISHU_AM_*`、模板配置和私有运行时边界
- [ARCHITECTURE.md](ARCHITECTURE.md)
  - 当前 runtime、场景层和写回层的分层边界

## 写回策略

### 默认行为

- 先建议，后确认
- 未确认不写入
- 责任人未解析时不创建待办

### 去重行为

- 同一核心任务优先“更新已有任务（update_existing）”
- 若是更细执行步骤，优先“建议拆分子任务（create_subtask）”
- 子任务默认是建议态，显式确认（source_context.confirm_create_subtask=true）后才会执行创建

## 路线图（抽象）

### M1 稳态执行内核

持续压实写回稳定性、回归样本和失败模式治理，降低误写/漏写/重复写风险。

### M2 经营闭环增强

从“完成落盘”升级到“主动提炼经营信号”，形成客户周报、风险提醒和动作缺口提示。

### M3 复杂输入深度解读

提升会议纪要与历史资料的分阶段解读能力，强化事实-判断-行动的专家级链路。

### M4 兼容性与通用化

增强跨工作区（workspace）的字段适配能力，降低硬编码依赖，沉淀可迁移的经营方法模型（operating model）。

## 当前版本

- 版本号：0.2.13（2026-04-15）
- 上一正式版本：0.2.12（2026-04-14）
