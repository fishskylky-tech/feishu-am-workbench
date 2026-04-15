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