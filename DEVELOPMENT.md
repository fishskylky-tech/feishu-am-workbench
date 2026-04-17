# Development

本文档定义 `feishu-am-workbench` 的日常开发方式。

目标不是追求重型工程流程，而是保证这个仓库在持续演进时仍然：

- 改动边界清楚
- 验证足够快
- 文档与代码一致
- live-first / recommendation-first 原则不被偷偷破坏

## 1. 当前开发原则

- 优先解决真实 AM 高价值场景
- 优先保住 live-first、schema preflight 和 write guard 边界
- 不为了“以后也许会用到”先做平台化抽象
- 新场景先补验证，再谈放大能力面

## 2. 分支与节奏

当前仓库建议的开发节奏与 [WORKFLOW.md](WORKFLOW.md) 保持一致：

1. 先明确一个小目标
2. 在开发分支实现
3. 跑自动化或真实样本验证
4. 同步必要文档
5. 再发 PR

如果改动里混入大量 `.planning/` 产物，先走 `/gsd-pr-branch` 清理评审面，再发 PR。

## 3. 常见改动落点

### 业务与场景逻辑

- `evals/meeting_output_bridge.py`
  - 当前会议场景的主集成面

### runtime 底座

- `runtime/gateway.py`
- `runtime/live_adapter.py`
- `runtime/schema_preflight.py`
- `runtime/write_guard.py`
- `runtime/todo_writer.py`

### 语义与边界

- `runtime/models.py`
- `runtime/semantic_registry.py`
- `references/*.md`

### 验证

- `tests/test_runtime_smoke.py`
- `tests/test_meeting_output_bridge.py`
- `tests/test_validation_assets.py`
- `evals/evals.json`

## 4. 什么时候要补文档

以下变化默认应该同步文档：

- 用户可见流程变了
- 环境变量、配置方式或运行前提变了
- 验证口径变了
- 架构边界或 phase 状态变了

最常见需要一起同步的文件是：

- `README.md`
- `STATUS.md`
- `VALIDATION.md`
- `CHANGELOG.md`
- `VERSION`

## 5. 不该做的事

- 不把真实 token、folder token、tasklist guid 写进仓库
- 不让 foundation 层自动拼完整业务上下文
- 不把 fallback 搜索结果包装成高置信 grounded fact
- 不在没有验证的情况下扩大写回面
- 不顺手大改无关文档和无关模块

## 6. 推荐开发循环

一个典型的小循环如下：

```bash
source .venv/bin/activate
python3 -m unittest tests.test_meeting_output_bridge -q
# 修改代码
python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge -q
```

如果改动涉及版本或文档一致性，再补：

```bash
python3 -m unittest tests.test_validation_assets -q
```

## 7. 与 GSD 的关系

当前仓库已经接入 GSD 规划产物，所以建议：

- 小型文档/代码收尾：`/gsd-quick`
- bug 调试：`/gsd-debug`
- phase 执行：`/gsd-execute-phase`
- PR 评审面清理：`/gsd-pr-branch`
- 正式发 PR：`/gsd-ship`

如果你只是单次修一两个文件，也要尽量保持 phase、验证和文档三者一致，而不是只改代码。

## Local Setup

这个仓库当前没有顶层 `package.json`、`pyproject.toml`、`requirements.txt` 或 `Makefile` 来统一安装与开发脚本；日常开发以仓库内虚拟环境、本地 `.env` 和宿主机上的 `lark-cli` 为基础。

建议的本地开发准备顺序如下：

1. 准备仓库副本，并在仓库根目录创建本地虚拟环境：

   ```bash
   python3 -m venv .venv
   ```

2. 激活虚拟环境：

   ```bash
   source .venv/bin/activate
   ```

3. 基于 [.env.example](.env.example) 创建本地 `.env`，填入实际 `FEISHU_AM_*` 变量。当前样例里可见的核心变量包括：
   - `FEISHU_AM_BASE_TOKEN`
   - `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID`
   - `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`
   - `FEISHU_AM_MEETING_NOTES_FOLDER`
   - `FEISHU_AM_TODO_TASKLIST_GUID`

4. 确认 `lark-cli` 已在当前 shell 的 `PATH` 中可用，并且已经完成飞书认证授权。

5. 先跑一条最小诊断，确认 runtime 能读到本地配置和 live 能力：

   ```bash
   python3 -m runtime .
   ```

如果这一步无法返回 capability 结果，先排查 `.env`、资源权限或 `lark-cli`，不要直接继续业务场景开发。

## Build Commands

当前仓库没有单独的 build 产物装配步骤，开发命令以直接运行 Python 模块和 `unittest` 切片为主。

| Command | Description |
| --- | --- |
| `source .venv/bin/activate` | 激活仓库本地虚拟环境。 |
| `python3 -m runtime .` | 走默认诊断入口，检查当前仓库的 live capability。 |
| `python3 -m runtime diagnose . --json` | 以 JSON 输出 capability 诊断，适合脚本或 agent 链接。 |
| `python3 -m runtime scene post-meeting-synthesis --eval-name unilever-stage-review --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt --customer-query 联合利华` | 走 canonical scene runtime 的会后整理主路径。 |
| `python3 -m evals.meeting_output_bridge --eval-name unilever-stage-review --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt --run-gateway --customer-query 联合利华` | 跑当前最稳定的会议 eval 桥接链路。 |
| `python3 -m unittest tests.test_meeting_output_bridge -q` | 会议场景的快速回归切片。 |
| `python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q` | 发 PR 前最常用的核心回归切片。 |
| `python3 -m unittest tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner tests.test_validation_assets -q` | 更完整的回归，覆盖 eval runner 和验证资产一致性。 |

## Code Style

仓库根目录当前没有检测到 `ESLint`、`Prettier`、`Biome`、`.editorconfig`、`ruff.toml`、`mypy.ini` 这类统一代码风格配置；因此现阶段的代码风格约束主要来自现有源码风格和最小化自动化钩子。

- 当前唯一已配置的提交前自动检查是 [.pre-commit-config.yaml](.pre-commit-config.yaml) 中的 `detect-secrets`，用于避免把敏感信息提交进仓库。
- Python 代码风格以现有 `runtime/` 和 `tests/` 目录中的写法为准：优先标准库、显式类型标注、`unittest` 作为测试框架、避免不必要抽象。
- 因为没有单独的 lint/format 脚本，提交前至少应跑与改动对应的 `python3 -m unittest ...` 切片，把回归验证当成当前最硬的风格和质量闸门。
- 涉及 `.env`、字段映射或 live 资源说明的改动时，额外确认没有把真实 token、folder token 或 guid 写入仓库。

## Branch Conventions

当前已文档化的分支约定在 [WORKFLOW.md](WORKFLOW.md) 中：

- 稳定分支是 `main`，目标是保持“可回退、可对照”；未验证改动不应直接堆到 `main`。
- 推荐开发分支前缀是 `codex/*`。
- 已给出的命名样式示例包括 `codex/m1-validation-*`、`codex/m2-account-loop-*`、`codex/m3-deep-interpretation-*`。
- 除上述前缀约定外，仓库里没有额外文档化的分支命名规则。

## PR Process

提交 PR 时，当前仓库至少应满足以下要求：

- 按 [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) 说明本次变更、变更原因、影响范围、验证情况和剩余风险。
- 在影响范围里明确勾选这次改动触及的是主规则、字段快照、路由/幂等、客户档案、Todo 行为、schema 兼容，还是仅文档说明。
- 如果改动涉及 live 行为或写回边界，PR 前应确认 live Base schema、相关单选/自定义字段选项、保护字段约束、客户档案唯一性规则和绝对时间规则没有被放松。
- 至少跑过与改动范围匹配的 `unittest` 切片；如果同时改了版本、文档或验证口径，再补跑 `tests.test_validation_assets`。
- 对仍未完全验证的部分在“剩余风险”里写清楚，不要把未验证假设包装成已确认事实。
