# Getting Started

本文档面向第一次在本地跑起 `feishu-am-workbench` 的使用者。

目标不是把所有能力一次性讲完，而是带你走通一条最小、可验证、不会误写的路径。

## 1. 前置条件

开始前，确认本机满足以下条件：

1. Python 3.10+
2. 已安装 `lark-cli`
3. 已完成飞书登录授权，并具备目标 Base、Drive 和 Task 资源访问权限
4. 仓库根目录存在本地 `.venv`，或者你有可用的 Python 环境

如果只是阅读 skill 文档，不需要 live runtime；如果要走真实验证，以上 4 项缺一不可。

## 2. 本地环境准备

推荐先激活仓库自己的虚拟环境：

```bash
source .venv/bin/activate
```

然后准备本地 `.env`：

1. 复制 [config/template.yaml](config/template.yaml) 和 [config/example.yaml](config/example.yaml) 了解所需资源范围
2. 在仓库根目录创建 `.env`
3. 填入本地 `FEISHU_AM_*` 环境变量

最常见的运行时输入包括：

- `FEISHU_AM_WORKBENCH_BASE_URL`
- `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`
- `FEISHU_AM_MEETING_NOTES_FOLDER`
- `FEISHU_AM_TODO_TASKLIST_GUID`
- `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID`
- `FEISHU_AM_TODO_PRIORITY_FIELD_GUID`

`.env` 只作为本地便利层，不应该提交到仓库。

## 3. 第一步：跑环境诊断

先确认 runtime 能看到你的 live 资源，而不是一上来跑业务场景：

```bash
python3 -m runtime .
```

理想结果是三个核心能力都可用：

- `base_access: available`
- `docs_access: available`
- `task_access: available`

如果不是 `available`，先不要继续跑会议场景。优先修资源、scope 或 `.env`。

## 4. 第二步：跑一条真实会议链路

推荐先跑联合利华案例，因为它已经在当前仓库里形成稳定验证基线：

```bash
python3 -m evals.meeting_output_bridge \
  --eval-name unilever-stage-review \
  --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt \
  --run-gateway \
  --customer-query 联合利华
```

重点看 6 个字段：

1. `资源状态`
2. `客户结果`
3. `上下文恢复状态`
4. `已使用资料`
5. `写回上限`
6. `开放问题`

这 6 个字段是当前 meeting 场景最核心的审计框架。

## 5. 第三步：跑自动化测试切片

当前最值得优先跑的切片是：

```bash
python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q
```

它覆盖了：

- 本地环境加载
- runtime capability smoke
- meeting context recovery
- 版本和验证资产一致性

## 6. 成功标准

你可以认为本地“已上手”的最低标准是：

1. `python3 -m runtime .` 能正常返回 capability 结果
2. 一条真实会议样本能跑出完整审计框架
3. 上面的 unittest 切片通过

做到这三点，才适合继续往写回、扩表、Phase 4/5 演进。

## 7. 下一步看什么

- 想做开发：看 [DEVELOPMENT.md](DEVELOPMENT.md)
- 想理解测试和 PR 前检查：看 [TESTING.md](TESTING.md)
- 想理解配置边界：看 [CONFIGURATION.md](CONFIGURATION.md)
- 想理解当前架构：看 [ARCHITECTURE.md](ARCHITECTURE.md)
## Prerequisites

- Python 版本至少为 `3.10`。仓库说明和 [SKILL.md](SKILL.md) 都将本地 runtime 前提固定为 Python 3.10+。
- 当前 shell 里必须能直接调用 `lark-cli`，并且已完成飞书授权。runtime 的 live 能力全部通过本机 `lark-cli` 调用。
- 建议使用仓库根目录下的 `.venv`；如果没有，也可以自行创建一个本地 Python 虚拟环境。
- 如果要跑 live 诊断，至少需要准备 `.env.example` 中示例过的 `FEISHU_AM_BASE_TOKEN`、`FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`、`FEISHU_AM_MEETING_NOTES_FOLDER` 和 `FEISHU_AM_TODO_TASKLIST_GUID`。

## Installation Steps

1. 克隆仓库并进入目录：

```bash
git clone git@github.com:fishskylky-tech/feishu-am-workbench.git
cd feishu-am-workbench
```

2. 准备本地 Python 环境。如果仓库内已有 `.venv`，直接激活；否则新建一个：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. 复制环境变量样例并补齐本地值：

```bash
cp .env.example .env
```

4. 确认 `lark-cli` 已在 `PATH` 中，并且已经完成登录授权。这个仓库没有单独的 Python 依赖清单，live 集成主要依赖本机 `lark-cli` 和仓库内源码。

## First Run

第一次启动建议显式走诊断子命令，而不是直接进入业务场景：

```bash
python3 -m runtime diagnose .
```

如果这个命令返回 `base_access`、`docs_access`、`task_access` 三项能力状态，你就已经走通了本地 runtime 的最短路径。当前 `python3 -m runtime .` 也会落到同一个诊断流程，但 `diagnose` 子命令更直白，适合作为首跑入口。

## Common Setup Issues

- `base_access: blocked`
  最常见原因是缺少 `FEISHU_AM_BASE_TOKEN`。runtime 在 capability 检查里会把这个变量视为 Base 访问前提。
- `docs_access: blocked` 或 `task_access: blocked`
  通常表示 `.env` 里缺少 `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`、`FEISHU_AM_MEETING_NOTES_FOLDER` 或 `FEISHU_AM_TODO_TASKLIST_GUID`，或者这些资源在当前账号下不可确认。
- `lark-cli` 命令失败、无输出或返回非 JSON
  runtime 的 CLI 包装层要求 `lark-cli` 返回可解析 JSON；如果本机没有安装、没有登录，或者当前 shell 找不到该命令，诊断会直接失败。
- `.env` 改了但运行结果没变
  这是预期行为之一。`runtime.env_loader` 默认不会覆盖已经存在的 shell 环境变量，所以如果你在当前终端里先导出了同名 `FEISHU_AM_*` 变量，`.env` 中的值不会生效，需先清掉旧环境变量再重试。
- 会议场景提示缺少 `--eval-name` 或 `--transcript-file`
  `post-meeting-synthesis` 是强约束 scene，缺少这两个参数会直接退出。先用诊断命令确认环境，再进入场景命令。

## Next Steps

- 想继续做本地开发，查看 [DEVELOPMENT.md](DEVELOPMENT.md)。
- 想了解测试切片、覆盖范围和 CI 入口，查看 [TESTING.md](TESTING.md)。
- 想核对环境变量和 workspace config 边界，查看 [CONFIGURATION.md](CONFIGURATION.md)。
- 想理解 runtime、gateway 和 scene contract 的关系，查看 [ARCHITECTURE.md](ARCHITECTURE.md)。
