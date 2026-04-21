# 测试指南

<!-- generated-by: gsd-doc-writer -->

本指南介绍飞书 AM 工作台项目的测试基础设施、测试分类、运行方法及编写规范。

## 测试框架

项目使用 **pytest** 和 **unittest** 作为测试框架。

- `tests/` 目录包含所有测试用例
- `evals/` 目录包含评估测试（质量评估）
- `.pytest_cache/` 用于测试缓存

## 测试分类

### 1. 单元测试（Unit Tests）

单元测试验证单个函数或模块的行为。

**测试文件示例：**
- `tests/test_env_loader.py` - 环境变量加载器测试
- `tests/test_portability_contract.py` - 可移植性契约测试
- `tests/test_skill_tokens.py` - 技能令牌测试
- `tests/test_expert_card_loader.py` - 专家卡片加载器测试
- `tests/test_expert_agent_adapter.py` - 专家代理适配器测试
- `tests/test_expert_analysis_helper.py` - 专家分析辅助测试

**测试特点：**
- 使用 `unittest.TestCase` 类组织
- 独立的临时环境，不依赖外部服务
- 快速执行，无需网络连接

### 2. 集成测试（Integration Tests）

集成测试验证多个模块协同工作的行为，通常涉及场景执行。

**测试文件示例：**
- `tests/test_scene_runtime.py` - 场景运行时集成测试
- `tests/test_meeting_prep_scene.py` - 会议准备场景测试
- `tests/test_proposal_scene.py` - 提案场景测试
- `tests/test_archive_refresh_scene.py` - 归档刷新场景测试
- `tests/test_post_meeting_scene.py` - 会后综合场景测试
- `tests/test_meeting_output_bridge.py` - 会议输出桥接测试

**测试特点：**
- 测试完整的场景执行流程
- 涉及多个模块协作
- 可能需要 mock 外部依赖

### 3. E2E 测试（End-to-End Tests）

E2E 测试验证通过 lark-cli 的完整 Task 和 Doc 操作流程，测试真实的飞书 API 集成。

**测试文件：**
- `tests/test_lark_task.py` - Task 创建/更新/去重 E2E 测试
- `tests/test_lark_doc.py` - Doc 读取/创建 E2E 测试
- `tests/test_live_bitable_integration.py` - 实时 Bitable 集成测试（5 层覆盖，默认跳过）

**测试特点：**
- 使用真实的 lark-cli 调用（可通过 `FEISHU_LARK_CLI_SKIP=1` 跳过）
- 测试完整的 API 操作流程
- 覆盖错误处理和边界情况

### 4. 评估测试（Evaluation Tests）

评估测试验证输出质量是否符合预期标准，通过 `evals/evals.json` 定义断言规则。

**核心文件：**
- `evals/runner.py` - 评估运行器
- `evals/evals.json` - 评估用例和断言定义
- `tests/test_eval_runner.py` - 评估运行器测试

**断言类型：**
| 类型 | 说明 |
|------|------|
| `contains_all` | 输出必须包含所有指定关键词 |
| `contains_any` | 输出必须包含至少一个指定关键词 |
| `not_contains_any` | 输出不能包含任何指定关键词 |
| `live_first_gate` | 验证 live-first 模式是否正确执行 |
| `hallucination_guard` | 检测输出是否包含捏造的信号（幻觉检测） |

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_scene_runtime.py
```

### 运行特定测试类

```bash
pytest tests/test_eval_runner.py::EvalRunnerTests
```

### 运行特定测试用例

```bash
pytest tests/test_eval_runner.py::EvalRunnerTests::test_runner_passes_customer_a_output_with_live_first_evidence
```

### 带详细输出运行

```bash
pytest -v
```

### 带覆盖率运行

```bash
pytest --cov=runtime
```

### 运行评估测试

```bash
pytest evals/
pytest tests/test_eval_runner.py
```

### 通过 CLI 运行单个评估用例

```bash
python -m evals.runner --eval-name "<CUSTOMER_A>-stage-review" --output-text "输出内容"
```

## 编写新测试

### 单元测试示例

```python
"""Tests for runtime .env loading behavior."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from runtime.env_loader import load_dotenv


class EnvLoaderTests(unittest.TestCase):
    def test_load_dotenv_reads_key_value_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                "FEISHU_AM_BASE_TOKEN=from_dotenv\n",
                encoding="utf-8",
            )
            loaded = load_dotenv(root)

            self.assertIn("FEISHU_AM_BASE_TOKEN", loaded)
            self.assertEqual(os.environ.get("FEISHU_AM_BASE_TOKEN"), "from_dotenv")

            os.environ.pop("FEISHU_AM_BASE_TOKEN", None)
```

### 评估测试断言示例

评估测试使用 `evals/runner.evaluate_case()` 或 `evals.runner.evaluate_artifact()` 验证输出：

```python
from evals.runner import evaluate_case

def test_live_first_gate_pass(self) -> None:
    output_text = """
    资源解析状态: resolved
    客户解析结果: <CUSTOMER_A> / 客户ID C_002
    上下文恢复状态: completed
    已使用飞书资料: 客户主数据、客户联系记录
    """
    result = evaluate_case(eval_name="<CUSTOMER_A>-stage-review", output_text=output_text)
    self.assertTrue(result["passed"])
```

### 测试命名规范

- 测试文件：`test_<模块名>.py`
- 测试类：`XxxTests`（使用驼峰命名）
- 测试方法：`test_<描述性名称>`（使用下划线分隔）

### 测试fixtures

测试使用的 fixtures 位于 `tests/fixtures/` 目录：

```
tests/fixtures/
└── transcripts/    # 会议记录样本
```

## 评估用例管理

评估用例定义在 `evals/evals.json`，包含 **18 个评测用例**（3 个基础 + 15 个 LLM 专家审核 cases）。每个用例包含：

```json
{
  "skill_name": "feishu-am-workbench",
  "version": "1.1.0",
  "description": "...",
  "evals": [{
    "id": 1,
    "name": "<CUSTOMER_A>-stage-review",
    "scenario": "探索型阶段汇报",
    "assertions": [
      {
        "id": "u1-live-first-gate",
        "type": "live_first_gate",
        "description": "验证 live-first 模式执行"
      }
    ]
  }]
}
```

## 最佳实践

1. **测试隔离**：每个测试应独立运行，不依赖其他测试的状态
2. **清理环境**：测试后清理修改的环境变量和临时文件
3. **清晰的断言消息**：使用描述性的断言消息便于定位问题
4. **AAA 模式**：按 Arrange（准备）、Act（执行）、Assert（断言）组织测试代码
5. **覆盖率目标**：保持核心模块的高测试覆盖率
6. **快速执行**：单元测试应能在毫秒级完成，避免不必要的延迟

## 持续集成

CI 流程中会自动运行测试套件和 LLM 专家审核评测，确保代码变更不会破坏现有功能：

- `pytest` — 运行所有单元和集成测试
- `pytest evals/` — 运行评估测试
- 特定评测用例（101/106/111）在 CI 中作为回归检测
