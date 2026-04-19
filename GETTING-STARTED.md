# Getting Started

## 这个 Skill 能帮你做什么

feishu-am-workbench 是一个面向 AM（客户运营）的 Agent Skill，帮助你在飞书工作台上完成客户信息收集、会议总结、任务跟踪等工作。

你可以把它理解为一个"客户运营助手"——它能帮你读取飞书上的客户资料、会议记录，生成结构化的客户分析，并且在写入前会先让你确认，避免误操作。

**Skill 支持的四大场景：**

| 场景 | 作用 | 帮你解决 |
|------|------|----------|
| 会后总结 | 分析会议内容，生成客户档案更新建议 | 手动整理会议要点容易遗漏 |
| 客户动态 | 汇总客户近期变化，发现风险和机会 | 客户多时难以及时跟进 |
| 归档刷新 | 从多个资料来源自动更新客户档案 | 资料分散在多个飞书文档里 |
| 任务跟踪 | 统一管理客户相关任务，避免重复 | 任务散落在不同地方 |

## 1. 前置条件

开始前，确认本机满足以下条件：

1. **Python 3.10+**（建议 3.11 或 3.12，性能更好）
2. **lark-cli 最新稳定版**（通过 `lark-cli --version` 确认版本）
3. 已完成飞书登录授权，具备目标 Base、Drive 和 Task 的访问权限
4. 仓库根目录有可用的 Python 环境（推荐使用 `.venv`）

## 2. 环境准备

### 激活 Python 环境

推荐使用仓库自带的虚拟环境：

```bash
source .venv/bin/activate
```

### 配置飞书访问凭证

1. 在仓库根目录创建 `.env` 文件
2. 参考 [config/example.yaml](config/example.yaml) 了解需要配置哪些资源
3. 填入以下核心环境变量：

```bash
FEISHU_AM_WORKBENCH_BASE_URL=https://open.feishu.cn
FEISHU_AM_BASE_TOKEN=<你的 Base Token>
FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER=<客户归档文件夹 ID>
FEISHU_AM_MEETING_NOTES_FOLDER=<会议记录文件夹 ID>
FEISHU_AM_TODO_TASKLIST_GUID=<待办清单 ID>
```

> **注意：** `.env` 文件不会提交到仓库，仅本地使用。

## 3. 第一次使用：诊断环境

建议第一步先确认 Skill 能正常访问你的飞书资源，而不是直接跑业务场景。

```bash
python3 -m runtime .
```

如果一切正常，你会看到三个核心能力的状态：

- `base_access: available` — 能读取飞书 Base
- `docs_access: available` — 能读取飞书云文档
- `task_access: available` — 能读写飞书任务

只要这三项都是 `available`，就可以开始使用了。

如果看到 `blocked`，先检查：
- `.env` 是否配置了对应资源 ID
- 当前飞书账号是否有这些资源的访问权限

## 4. 快速体验：一个真实场景

确认环境可用后，可以跑一条真实会议记录试试：

```bash
python3 -m evals.meeting_output_bridge \
  --eval-name <CUSTOMER_A>-stage-review \
  --transcript-file tests/fixtures/transcripts/20260410-<CUSTOMER_A> Campaign活动分析优化-阶段汇报.txt \
  --run-gateway \
  --customer-query <CUSTOMER_A>
```

运行后会看到类似这样的结构化输出：

1. **资源状态** — 客户资料是否完整
2. **客户结果** — 会议识别到的关键信息
3. **上下文恢复状态** — 从哪些资料补充了背景
4. **已使用资料** — 引用了哪些飞书文档
5. **写回上限** — 本次可以写入的范围
6. **开放问题** — 需要你进一步确认的内容

重点看最后两项：**写回上限**和**开放问题**——这是 Skill 在写入前给你的保护性提示。

## 5. 四大场景快速概览

### 会后总结（post-meeting-synthesis）

输入一段会议记录，自动分析：
- 客户当前处于什么状态
- 有哪些需要跟进的问题
- 可以从哪些资料补充背景

输出结构化的会后总结，并给出写回客户档案的建议。

### 客户动态（customer-recent-status）

输入一个客户名，自动扫描：
- 近期会议记录
- 任务更新
- 文档变更

输出客户近期变化摘要，发现潜在风险和机会。

### 归档刷新（archive-refresh）

从多个飞书文档来源，自动提取：
- 客户状态更新
- 合同进展
- 联系人变动

生成整合的归档更新建议。

### 任务跟踪（todo-capture-and-update）

帮你统一管理客户相关的任务：
- 自动从会议和文档中提取待办
- 写入飞书任务清单
- 写入前会先让你确认每一条

## 6. 下一步

- 想详细了解每个场景的用法和输入输出：查看 [SKILL.md](SKILL.md)
- 想了解如何配置飞书资源和环境变量：查看 [CONFIGURATION.md](CONFIGURATION.md)
- 想了解 Skill 的整体设计思路：查看 [ARCHITECTURE.md](ARCHITECTURE.md)
