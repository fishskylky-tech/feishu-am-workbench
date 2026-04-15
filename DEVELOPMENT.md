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