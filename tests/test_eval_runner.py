from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evals.runner import evaluate_case


REPO_ROOT = Path("/Users/liaoky/.codex/skills/feishu-am-workbench")


class EvalRunnerTests(unittest.TestCase):
    def test_runner_passes_unilever_output_with_live_first_evidence(self) -> None:
        output_text = """
资源解析状态: resolved
客户解析结果: 联合利华 / 客户ID C_002
上下文恢复状态: completed
已使用飞书资料: 客户主数据、客户联系记录、行动计划、客户档案
Meeting type: stage_review
write ceiling: 客户主数据: no-write; Todo: no-write
Open questions:
- 招募来源口径
- 激活来源口径
- 画像如何落地到投放
Schedule:
- 2026-08 或 2026-09 高峰
- precision gap: 2026年下半年
"""
        result = evaluate_case(eval_name="unilever-stage-review", output_text=output_text)
        self.assertTrue(result["passed"])

    def test_runner_fails_unilever_without_live_first_evidence(self) -> None:
        output_text = """
这是一次阶段汇报。
客户主数据: no-write
Todo: no-write
Open questions:
- 招募来源口径
"""
        result = evaluate_case(eval_name="unilever-stage-review", output_text=output_text)
        self.assertFalse(result["passed"])
        failing = {item["id"] for item in result["assertions"] if not item["passed"]}
        self.assertIn("u1-live-first-gate", failing)

    def test_runner_accepts_not_run_with_explicit_reason(self) -> None:
        output_text = """
资源解析状态: unresolved
客户解析结果: missing
上下文恢复状态: not-run
fallback 原因: permission scope insufficient for current live lookup
输出重点:
- 归因逻辑解释
- dashboard 取数口径
- 后续支持动作
客户主数据: no-write
"""
        result = evaluate_case(eval_name="dominos-ad-tracking-qa", output_text=output_text)
        self.assertTrue(result["passed"])

    def test_runner_rejects_generic_reason_words_without_explicit_fallback_field(self) -> None:
        output_text = """
资源解析状态: unresolved
客户解析结果: missing
上下文恢复状态: not-run
This output mentions reason and scope in ordinary prose only.
输出重点:
- 归因逻辑解释
"""
        result = evaluate_case(eval_name="dominos-ad-tracking-qa", output_text=output_text)
        self.assertFalse(result["passed"])
        live_first_assertion = next(item for item in result["assertions"] if item["id"] == "d1-live-first-gate")
        self.assertFalse(live_first_assertion["details"]["has_fallback_reason"])

    def test_cli_returns_json_and_exit_code(self) -> None:
        output_text = """
资源解析状态: unresolved
客户解析结果: missing
上下文恢复状态: not-run
fallback 原因: permission scope insufficient for current live lookup
输出重点:
- 知识库
- 记忆
- 归因能力边界
- 后续跟进
客户主数据: no-write
"""
        with tempfile.NamedTemporaryFile("w+", delete=False) as handle:
            handle.write(output_text)
            handle.flush()
            path = handle.name
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "evals.runner",
                "--eval-name",
                "yonghe-product-solution-discussion",
                "--output-file",
                path,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["passed"])


if __name__ == "__main__":
    unittest.main()
