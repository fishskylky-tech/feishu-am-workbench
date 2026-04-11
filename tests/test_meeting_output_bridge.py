from __future__ import annotations

import sys
import subprocess
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS_DIR = REPO_ROOT / "tests" / "fixtures" / "transcripts"
UNILEVER_TRANSCRIPT = TRANSCRIPTS_DIR / "20260410-联合利华 Campaign活动分析优化-阶段汇报.txt"
YONGHE_TRANSCRIPT = TRANSCRIPTS_DIR / "20260409 神策AI 产品和永和大王会议记录.txt"
DOMINOS_TRANSCRIPT = TRANSCRIPTS_DIR / "2026-3-18 达美乐神策会议纪要.txt"
sys.path.insert(0, str(REPO_ROOT))

from evals.runner import evaluate_case  # noqa: E402
from runtime.models import (  # noqa: E402
    CapabilityReport,
    CustomerMatch,
    CustomerResolution,
    GatewayResult,
    ResourceHint,
    ResourceResolution,
)

from evals.meeting_output_bridge import build_meeting_output  # noqa: E402
from evals.meeting_output_bridge import main as bridge_main  # noqa: E402
from evals.meeting_output_bridge import recover_live_context  # noqa: E402
from evals.meeting_output_bridge import run_gateway_and_build_meeting_output  # noqa: E402


class MeetingOutputBridgeTests(unittest.TestCase):
    def test_build_meeting_output_handles_missing_transcript_file(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="联合利华",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="联合利华",
                    )
                ],
            ),
        )

        output_text = build_meeting_output(
            eval_name="unilever-stage-review",
            transcript_path=Path("/tmp/feishu-am-workbench-missing-transcript.txt"),
            gateway_result=gateway_result,
            context_status="partial",
            fallback_reason="transcript file not available in current environment",
        )

        self.assertIn("Transcript source: feishu-am-workbench-missing-transcript.txt", output_text)
        self.assertIn("Transcript status: missing", output_text)
        self.assertIn("fallback 原因: transcript file not available in current environment", output_text)

    def test_recover_live_context_reads_minimum_base_sources(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [
                        {"客户ID": customer_id, "记录标题": "联合利华｜阶段汇报跟进", "联系日期": "2026-04-09"},
                        {"客户ID": customer_id, "记录标题": "联合利华｜投放优化讨论", "联系日期": "2026-04-03"},
                    ][:limit]
                if table_name == "行动计划":
                    return [
                        {"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"},
                    ][:limit]
                return []

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="联合利华",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="联合利华",
                        archive_link="https://doc.example/unilever",
                        raw_record={"客户ID": "C_002", "简称": "联合利华", "客户档案": "https://doc.example/unilever"},
                    )
                ],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=FakeQueryBackend(),
        )

        self.assertEqual(context["status"], "completed")
        self.assertEqual(
            context["used_sources"],
            ["客户主数据", "客户联系记录", "行动计划", "客户档案链接"],
        )
        self.assertIn("最近联系记录: 2026-04-09｜联合利华｜阶段汇报跟进", context["key_context"])
        self.assertIn("当前行动计划: 推进 Campaign 优化方案确认｜2026-04-20", context["key_context"])

    def test_gateway_execution_marks_unilever_context_as_partial_until_stage3_reads_exist(self) -> None:
        class FakeGateway:
            def run(self, customer_query: str):
                self.last_query = customer_query
                return GatewayResult(
                    resource_resolution=ResourceResolution(
                        status="resolved",
                        hints_used=[
                            ResourceHint("base_token", "references/live-resource-links.md", "app_live", True),
                        ],
                    ),
                    capability_report=CapabilityReport(),
                    customer_resolution=CustomerResolution(
                        status="resolved",
                        query=customer_query,
                        candidates=[
                            CustomerMatch(
                                customer_id="C_002",
                                short_name="联合利华",
                                archive_link="https://doc.example/unilever",
                            )
                        ],
                    ),
                )

        class EmptyQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                return []

        gateway = FakeGateway()
        output_text, gateway_result = run_gateway_and_build_meeting_output(
            eval_name="unilever-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            customer_query="联合利华",
            gateway=gateway,
            query_backend=EmptyQueryBackend(),
        )

        self.assertEqual(gateway.last_query, "联合利华")
        self.assertEqual(gateway_result.customer_resolution.status, "resolved")
        self.assertIn("上下文恢复状态: partial", output_text)
        self.assertIn("已使用飞书资料: 客户主数据、客户档案链接", output_text)
        self.assertIn("未找到但应存在的资料: 客户联系记录、行动计划", output_text)
        result = evaluate_case(eval_name="unilever-stage-review", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_gateway_execution_keeps_context_limited_when_customer_resolution_fails(self) -> None:
        class FakeGateway:
            def run(self, customer_query: str):
                return GatewayResult(
                    resource_resolution=ResourceResolution(
                        status="partial",
                        hints_used=[
                            ResourceHint("base_token", "references/live-resource-links.md", "app_live", True),
                        ],
                        unconfirmed_keys=["customer_archive_folder"],
                    ),
                    capability_report=CapabilityReport(),
                    customer_resolution=CustomerResolution(status="missing", query=customer_query),
                )

        class EmptyQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                return []

        output_text, gateway_result = run_gateway_and_build_meeting_output(
            eval_name="yonghe-product-solution-discussion",
            transcript_path=YONGHE_TRANSCRIPT,
            customer_query="永和大王",
            gateway=FakeGateway(),
            query_backend=EmptyQueryBackend(),
        )

        self.assertEqual(gateway_result.customer_resolution.status, "missing")
        self.assertIn("上下文恢复状态: context-limited", output_text)
        self.assertIn("fallback 原因: customer cannot be resolved", output_text)
        result = evaluate_case(
            eval_name="yonghe-product-solution-discussion",
            output_text=output_text,
        )
        self.assertTrue(result["passed"], result)

    def test_unilever_bridge_output_passes_eval_runner(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(
                status="resolved",
                hints_used=[
                    ResourceHint("base_token", "references/live-resource-links.md", "app_live", True),
                    ResourceHint("customer_archive_folder", "references/live-resource-links.md", "folder_archive", True),
                ],
            ),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="联合利华",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="联合利华",
                        archive_link="https://doc.example/unilever",
                    )
                ],
            ),
        )
        output_text = build_meeting_output(
            eval_name="unilever-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="completed",
            used_sources=["客户主数据", "客户联系记录", "行动计划", "客户档案"],
        )
        result = evaluate_case(eval_name="unilever-stage-review", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_yonghe_bridge_output_passes_eval_runner_with_fallback_reason(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(
                status="partial",
                hints_used=[ResourceHint("base_token", "references/live-resource-links.md", "app_live", True)],
                unconfirmed_keys=["customer_archive_folder"],
            ),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(status="missing", query="永和大王"),
        )
        output_text = build_meeting_output(
            eval_name="yonghe-product-solution-discussion",
            transcript_path=YONGHE_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="not-run",
            fallback_reason="customer cannot be resolved with enough confidence from current live customer master",
        )
        result = evaluate_case(
            eval_name="yonghe-product-solution-discussion",
            output_text=output_text,
        )
        self.assertTrue(result["passed"], result)

    def test_dominos_bridge_output_passes_eval_runner_with_logic_focus(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(
                status="partial",
                hints_used=[ResourceHint("todo_tasklist_guid", "references/live-resource-links.md", "tasklist_1", True)],
                missing_keys=["base_token"],
            ),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(status="missing", query="达美乐"),
        )
        output_text = build_meeting_output(
            eval_name="dominos-ad-tracking-qa",
            transcript_path=DOMINOS_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="not-run",
            fallback_reason="permission scope insufficient for current live lookup",
        )
        result = evaluate_case(eval_name="dominos-ad-tracking-qa", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_bridge_cli_prints_runner_compatible_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "evals.meeting_output_bridge",
                "--eval-name",
                "yonghe-product-solution-discussion",
                "--transcript-file",
                str(YONGHE_TRANSCRIPT),
                "--resource-status",
                "partial",
                "--customer-status",
                "missing",
                "--context-status",
                "not-run",
                "--fallback-reason",
                "customer cannot be resolved with enough confidence from current live customer master",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = evaluate_case(
            eval_name="yonghe-product-solution-discussion",
            output_text=completed.stdout,
        )
        self.assertTrue(result["passed"], result)

    def test_bridge_cli_can_run_gateway_mode_without_manual_status_args(self) -> None:
        class FakeGateway:
            def run(self, customer_query: str):
                return GatewayResult(
                    resource_resolution=ResourceResolution(status="resolved"),
                    capability_report=CapabilityReport(),
                    customer_resolution=CustomerResolution(
                        status="resolved",
                        query=customer_query,
                        candidates=[CustomerMatch(customer_id="C_002", short_name="联合利华")],
                    ),
                )

        stdout = StringIO()
        with patch(
            "evals.meeting_output_bridge.FeishuWorkbenchGateway.for_live_lark_cli",
            return_value=FakeGateway(),
        ):
            with redirect_stdout(stdout):
                exit_code = bridge_main(
                    [
                        "--run-gateway",
                        "--eval-name",
                        "unilever-stage-review",
                        "--transcript-file",
                        str(UNILEVER_TRANSCRIPT),
                        "--customer-query",
                        "联合利华",
                        "--repo-root",
                        str(REPO_ROOT),
                    ]
                )
        self.assertEqual(exit_code, 0)
        output_text = stdout.getvalue()
        self.assertIn("上下文恢复状态: partial", output_text)
        result = evaluate_case(eval_name="unilever-stage-review", output_text=output_text)
        self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
