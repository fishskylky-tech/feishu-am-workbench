# Testing

本文档说明 `feishu-am-workbench` 当前如何验证“这次改动真的可信”。

这里不追求重型 benchmark，而是追求对当前 live-first 工作流真正有约束力的验证。

## 1. 测试分层

当前仓库可以分成 3 层验证：

### 自动化单元/集成切片

- `tests/test_env_loader.py`
- `tests/test_runtime_smoke.py`
- `tests/test_meeting_output_bridge.py`
- `tests/test_eval_runner.py`
- `tests/test_validation_assets.py`

### 结构化 eval 资产

- `evals/evals.json`
- `evals/runner.py`
- `evals/meeting_output_bridge.py`

### 人工 live 验证

- 真实飞书工作区的 capability 检查
- meeting 场景输出审计字段复核
- fallback evidence 质量复核
- human UAT

## 2. 最常用测试命令

### 快速切片

```bash
python3 -m unittest tests.test_meeting_output_bridge -q
```

适合修改会议场景、上下文恢复、fallback 路由、审计字段时快速回归。

### Phase 3 / 当前核心切片

```bash
python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q
```

适合在发 PR 前确认：

- 环境加载没坏
- runtime capability 逻辑没坏
- meeting recovery 没回退
- 文档/版本/验证资产仍然一致

### 更完整的回归

```bash
python3 -m unittest tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_eval_runner tests.test_validation_assets
```

## 3. 人工验证重点

自动化通过不等于 live 场景一定可信。以下项仍然需要人工确认：

1. archive / meeting-note fallback 在真实 Drive 中的候选质量
2. 写回前 preflight / guard 在真实任务和表结构上的行为
3. 高风险字段是否仍然保持 recommendation-only

## 4. 发 PR 前建议清单

至少确认：

1. 相关 unittest 切片通过
2. 如果改了文档或版本，`tests.test_validation_assets` 通过
3. 需要时补一条真实会议样本验证
4. 文档与实际行为一致
5. 未把 `.planning/` 噪音带进 PR 评审面

## 5. 当前可信口径

截至当前状态，最稳定的验证结论是：

- Phase 3 自动化切片已通过
- Phase 3 code review clean
- security audit `threats_open: 0`
- human UAT 4/4 passed

这说明当前 meeting 场景的核心上下文恢复闭环可信，但不代表所有写回路径都已完全成熟。