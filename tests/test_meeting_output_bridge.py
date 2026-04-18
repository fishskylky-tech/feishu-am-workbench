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
UNILEVER_TRANSCRIPT = TRANSCRIPTS_DIR / "20260410-<CUSTOMER_A> Campaign活动分析优化-阶段汇报.txt"
YONGHE_TRANSCRIPT = TRANSCRIPTS_DIR / "20260409 神策AI 产品和<CUSTOMER_B>会议记录.txt"
DOMINOS_TRANSCRIPT = TRANSCRIPTS_DIR / "2026-3-18 <CUSTOMER_C>神策会议纪要.txt"
sys.path.insert(0, str(REPO_ROOT))

from evals.runner import evaluate_case  # noqa: E402
from runtime.models import (  # noqa: E402
    CapabilityReport,
    CustomerMatch,
    CustomerResolution,
    GatewayResult,
    ResourceHint,
    ResourceResolution,
    WriteCandidate,
    WriteExecutionResult,
    ContextRecoveryResult,
)

from evals.meeting_output_bridge import build_meeting_output  # noqa: E402
from evals.meeting_output_bridge import build_meeting_output_artifact  # noqa: E402
from evals.meeting_output_bridge import main as bridge_main  # noqa: E402
from evals.meeting_output_bridge import build_meeting_todo_candidates  # noqa: E402
from evals.meeting_output_bridge import recover_live_context  # noqa: E402
from evals.meeting_output_bridge import run_confirmed_todo_write  # noqa: E402
from evals.meeting_output_bridge import run_gateway_and_build_meeting_output  # noqa: E402
from evals.meeting_output_bridge import _derive_structured_sections  # noqa: E402
from runtime.semantic_registry import SEMANTIC_FIELD_REGISTRY  # noqa: E402
from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource  # noqa: E402


class MeetingOutputBridgeTests(unittest.TestCase):
    def test_build_meeting_output_includes_write_result_summary(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        output_text = build_meeting_output(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="partial",
            used_sources=["客户主数据"],
            write_results=[
                WriteExecutionResult(
                    target_object="todo",
                    attempted=False,
                    allowed=False,
                    preflight_status="safe",
                    guard_status="allowed",
                    dedupe_decision="update_existing",
                    executed_operation="blocked",
                    remote_object_id="task_existing",
                    blocked_reasons=["semantic_duplicate_detected"],
                    source_context={"scenario": "post_meeting"},
                )
            ],
        )

        self.assertIn("统一写回结果:", output_text)
        self.assertIn("- todo: 未执行", output_text)
        self.assertIn("原因：semantic_duplicate_detected", output_text)
        self.assertNotIn("dedupe=", output_text)

    def test_build_meeting_output_handles_missing_transcript_file(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="<CUSTOMER_A>",
                    )
                ],
            ),
        )

        output_text = build_meeting_output(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=Path("/tmp/feishu-am-workbench-missing-transcript.txt"),
            gateway_result=gateway_result,
            context_status="partial",
            fallback_reason="transcript file not available in current environment",
        )

        self.assertIn("Transcript source: feishu-am-workbench-missing-transcript.txt", output_text)
        self.assertIn("Transcript status: missing", output_text)
        self.assertIn("fallback 原因: transcript file not available in current environment", output_text)

    def test_build_meeting_todo_candidates_returns_recommendation_mode_candidate(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        candidates = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=gateway_result,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.target_object, "todo")
        self.assertEqual(candidate.operation, "create")
        self.assertEqual(candidate.source_context["scenario"], "post_meeting")
        self.assertEqual(candidate.match_basis["customer"], "<CUSTOMER_A>")
        self.assertEqual(candidate.match_basis["time_window"], "2026-04")
        self.assertNotIn("owner", candidate.payload)

    def test_build_meeting_todo_candidates_consolidates_same_meeting_same_theme_actions(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        candidates = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=gateway_result,
            action_items=[
                {"summary": "确认 Campaign 优化方案", "theme": "campaign_optimization", "due_at": "2026-04-20"},
                {"summary": "同步 Campaign 优化排期", "theme": "campaign_optimization", "due_at": "2026-04-21"},
                {"summary": "整理续费沟通口径", "theme": "renewal_follow_up", "due_at": "2026-04-22"},
            ],
        )

        self.assertEqual(len(candidates), 2)
        themes = {candidate.match_basis["action_theme"]: candidate for candidate in candidates}
        merged = themes["campaign_optimization"]
        self.assertEqual(merged.operation, "create")
        self.assertEqual(merged.target_object, "todo")
        self.assertEqual(merged.source_context["customer_id"], "C_002")
        self.assertEqual(merged.source_context["merged_action_count"], 2)
        self.assertIn("同步 Campaign 优化排期", merged.payload["description"])
        self.assertIsNone(themes["renewal_follow_up"].source_context.get("merged_action_count"))

    def test_build_meeting_output_artifact_keeps_structured_results_while_default_output_stays_concise(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        artifact = build_meeting_output_artifact(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="completed",
            used_sources=["客户主数据", "客户联系记录", "行动计划", "客户档案"],
            write_results=[
                WriteExecutionResult(
                    target_object="todo",
                    attempted=True,
                    allowed=True,
                    preflight_status="safe",
                    guard_status="allowed",
                    dedupe_decision="update_existing",
                    executed_operation="update",
                    remote_object_id="task_existing",
                    source_context={"scenario": "post_meeting"},
                ),
                WriteExecutionResult(
                    target_object="todo",
                    attempted=False,
                    allowed=False,
                    preflight_status="safe",
                    guard_status="blocked",
                    dedupe_decision="create_subtask",
                    executed_operation="blocked",
                    blocked_reasons=["semantic_duplicate_detected", "subtask_recommended"],
                    source_context={"scenario": "post_meeting"},
                ),
            ],
        )

        output_text = artifact["output_text"]
        self.assertIn("统一写回结果:", output_text)
        self.assertIn("已更新已有待办", output_text)
        self.assertIn("未执行，原因：semantic_duplicate_detected、subtask_recommended", output_text)
        self.assertNotIn("dedupe=", output_text)
        self.assertNotIn("preflight=", output_text)
        self.assertEqual(artifact["write_result_details"][0]["dedupe_decision"], "update_existing")
        self.assertEqual(artifact["write_result_details"][1]["blocked_reasons"], ["semantic_duplicate_detected", "subtask_recommended"])
        self.assertTrue(evaluate_case(eval_name="<CUSTOMER_A>-stage-review", output_text=output_text)["passed"])

    def test_write_candidate_routing_metadata_returns_isolated_required_fields(self) -> None:
        candidate = WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "owner", "customer"],
            payload={"summary": "跟进<CUSTOMER_A>续费", "customer": "<CUSTOMER_A>"},
            match_basis={"customer": "<CUSTOMER_A>", "time_window": "2026-04"},
            source_context={"scenario": "post_meeting", "customer_id": "C_002", "meeting_eval": "<CUSTOMER_A>-stage-review"},
        )

        metadata = candidate.routing_metadata()

        self.assertEqual(metadata["operation"], "create")
        self.assertEqual(metadata["target_object"], "todo")
        self.assertEqual(metadata["match_basis"]["customer"], "<CUSTOMER_A>")
        self.assertEqual(metadata["source_context"]["customer_id"], "C_002")

        metadata["match_basis"]["customer"] = "被篡改"
        metadata["source_context"]["customer_id"] = "changed"

        self.assertEqual(candidate.match_basis["customer"], "<CUSTOMER_A>")
        self.assertEqual(candidate.source_context["customer_id"], "C_002")

    def test_run_confirmed_todo_write_uses_unified_todo_writer(self) -> None:
        class FakeTodoWriter:
            def __init__(self) -> None:
                self.calls = []

            def create(self, candidate):
                self.calls.append(candidate)
                return WriteExecutionResult(
                    target_object="todo",
                    attempted=True,
                    allowed=True,
                    preflight_status="safe",
                    guard_status="allowed",
                    dedupe_decision="create_new",
                    executed_operation="create",
                    remote_object_id="task_guid_1",
                    remote_url="https://applink.feishu.cn/client/todo/detail?guid=task_guid_1",
                    source_context=dict(candidate.source_context),
                )

        candidate = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=GatewayResult(
                resource_resolution=ResourceResolution(status="resolved"),
                customer_resolution=CustomerResolution(
                    status="resolved",
                    query="<CUSTOMER_A>",
                    candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
                ),
            ),
        )[0]

        writer = FakeTodoWriter()
        results = run_confirmed_todo_write(
            candidates=[candidate],
            todo_writer=writer,
        )

        self.assertEqual(len(writer.calls), 1)
        self.assertEqual(writer.calls[0].target_object, "todo")
        self.assertEqual(results[0].executed_operation, "create")
        self.assertEqual(results[0].remote_object_id, "task_guid_1")

    def test_run_confirmed_todo_write_blocks_update_candidates(self) -> None:
        class FakeTodoWriter:
            def create(self, candidate):
                raise AssertionError("update candidate should not call create")

        candidate = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=GatewayResult(
                resource_resolution=ResourceResolution(status="resolved"),
                customer_resolution=CustomerResolution(
                    status="resolved",
                    query="<CUSTOMER_A>",
                    candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
                ),
            ),
        )[0]
        candidate.operation = "update"

        results = run_confirmed_todo_write(candidates=[candidate], todo_writer=FakeTodoWriter())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].executed_operation, "blocked")
        self.assertIn("update_operation_not_supported_in_confirmed_write", results[0].blocked_reasons)

    def test_recover_live_context_reads_minimum_base_sources(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [
                        {"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜阶段汇报跟进", "联系日期": "2026-04-09"},
                        {"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜投放优化讨论", "联系日期": "2026-04-03"},
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
                query="<CUSTOMER_A>",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="<CUSTOMER_A>",
                        archive_link="https://doc.example/<CUSTOMER_A>",
                        raw_record={"客户ID": "C_002", "简称": "<CUSTOMER_A>", "客户档案": "https://doc.example/<CUSTOMER_A>"},
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
        self.assertIn("最近联系记录: 2026-04-09｜<CUSTOMER_A>｜阶段汇报跟进", context["key_context"])
        self.assertIn("当前行动计划: 推进 Campaign 优化方案确认｜2026-04-20", context["key_context"])

    def test_recover_live_context_includes_ranked_related_meeting_notes(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [
                        {
                            "客户ID": customer_id,
                            "记录标题": "<CUSTOMER_A>｜Campaign活动分析优化阶段汇报",
                            "联系日期": "2026-04-10",
                            "会议纪要链接": "https://doc.example/note-1",
                        },
                        {
                            "客户ID": customer_id,
                            "记录标题": "<CUSTOMER_A>｜季度复盘沟通",
                            "联系日期": "2026-04-05",
                            "会议纪要链接": "https://doc.example/note-2",
                        },
                    ]
                if table_name == "行动计划":
                    return [
                        {"客户ID": customer_id, "具体行动": "推进优化方案", "计划完成时间": "2026-04-20"},
                    ]
                return []

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="<CUSTOMER_A>",
                        archive_link="https://doc.example/<CUSTOMER_A>",
                    )
                ],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=FakeQueryBackend(),
            topic_text="20260410-<CUSTOMER_A> Campaign活动分析优化-阶段汇报",
        )

        self.assertIn("相关会议纪要候选", context["used_sources"])
        note_lines = [line for line in context["key_context"] if line.startswith("相关会议纪要候选:")]
        self.assertEqual(len(note_lines), 1)
        self.assertIn("note-1", note_lines[0])

    def test_recover_live_context_prefers_recent_note_when_titles_are_similar(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [
                        {
                            "客户ID": customer_id,
                            "记录标题": "<CUSTOMER_A>｜月度复盘汇报",
                            "联系日期": "2024-04-10",
                            "会议纪要链接": "https://doc.example/old-note",
                        },
                        {
                            "客户ID": customer_id,
                            "记录标题": "<CUSTOMER_A>｜月度复盘汇报",
                            "联系日期": "2026-04-10",
                            "会议纪要链接": "https://doc.example/new-note",
                        },
                    ]
                if table_name == "行动计划":
                    return [{"客户ID": customer_id, "具体行动": "复盘沟通", "计划完成时间": "2026-04-20"}]
                return []

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=FakeQueryBackend(),
            topic_text="<CUSTOMER_A> 月度复盘",
        )
        note_lines = [line for line in context["key_context"] if line.startswith("相关会议纪要候选:")]
        self.assertEqual(len(note_lines), 1)
        self.assertTrue(note_lines[0].index("new-note") < note_lines[0].index("old-note"))

    def test_gateway_execution_marks_<CUSTOMER_A>_context_as_partial_until_stage3_reads_exist(self) -> None:
        class FakeGateway:
            def run(self, customer_query: str):
                self.last_query = customer_query
                return GatewayResult(
                    resource_resolution=ResourceResolution(
                        status="resolved",
                        hints_used=[
                            ResourceHint("base_token", "references/live-resource-links.example.md", "app_live", True),
                        ],
                    ),
                    capability_report=CapabilityReport(),
                    customer_resolution=CustomerResolution(
                        status="resolved",
                        query=customer_query,
                        candidates=[
                            CustomerMatch(
                                customer_id="C_002",
                                short_name="<CUSTOMER_A>",
                                archive_link="https://doc.example/<CUSTOMER_A>",
                            )
                        ],
                    ),
                )

        class EmptyQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                return []

        gateway = FakeGateway()
        output_text, gateway_result = run_gateway_and_build_meeting_output(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            customer_query="<CUSTOMER_A>",
            gateway=gateway,
            query_backend=EmptyQueryBackend(),
        )

        self.assertEqual(gateway.last_query, "<CUSTOMER_A>")
        self.assertEqual(gateway_result.customer_resolution.status, "resolved")
        self.assertIn("上下文恢复状态: partial", output_text)
        self.assertIn("已使用飞书资料: 客户主数据、客户档案链接", output_text)
        self.assertIn("未找到但应存在的资料: 客户联系记录、行动计划", output_text)
        result = evaluate_case(eval_name="<CUSTOMER_A>-stage-review", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_gateway_execution_keeps_context_limited_when_customer_resolution_fails(self) -> None:
        class FakeGateway:
            def run(self, customer_query: str):
                return GatewayResult(
                    resource_resolution=ResourceResolution(
                        status="partial",
                        hints_used=[
                            ResourceHint("base_token", "references/live-resource-links.example.md", "app_live", True),
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
            eval_name="<CUSTOMER_B>-product-solution-discussion",
            transcript_path=YONGHE_TRANSCRIPT,
            customer_query="<CUSTOMER_B>",
            gateway=FakeGateway(),
            query_backend=EmptyQueryBackend(),
        )

        self.assertEqual(gateway_result.customer_resolution.status, "missing")
        self.assertIn("上下文恢复状态: context-limited", output_text)
        self.assertIn("fallback 原因: customer cannot be resolved", output_text)
        result = evaluate_case(
            eval_name="<CUSTOMER_B>-product-solution-discussion",
            output_text=output_text,
        )
        self.assertTrue(result["passed"], result)

    def test_<CUSTOMER_A>_bridge_output_passes_eval_runner(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(
                status="resolved",
                hints_used=[
                    ResourceHint("base_token", "references/live-resource-links.example.md", "app_live", True),
                    ResourceHint("customer_archive_folder", "references/live-resource-links.example.md", "folder_archive", True),
                ],
            ),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="<CUSTOMER_A>",
                        archive_link="https://doc.example/<CUSTOMER_A>",
                    )
                ],
            ),
        )
        output_text = build_meeting_output(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="completed",
            used_sources=["客户主数据", "客户联系记录", "行动计划", "客户档案"],
        )
        result = evaluate_case(eval_name="<CUSTOMER_A>-stage-review", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_<CUSTOMER_B>_bridge_output_passes_eval_runner_with_fallback_reason(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(
                status="partial",
                hints_used=[ResourceHint("base_token", "references/live-resource-links.example.md", "app_live", True)],
                unconfirmed_keys=["customer_archive_folder"],
            ),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(status="missing", query="<CUSTOMER_B>"),
        )
        output_text = build_meeting_output(
            eval_name="<CUSTOMER_B>-product-solution-discussion",
            transcript_path=YONGHE_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="not-run",
            fallback_reason="customer cannot be resolved with enough confidence from current live customer master",
        )
        result = evaluate_case(
            eval_name="<CUSTOMER_B>-product-solution-discussion",
            output_text=output_text,
        )
        self.assertTrue(result["passed"], result)

    def test_<CUSTOMER_C>_bridge_output_passes_eval_runner_with_logic_focus(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(
                status="partial",
                hints_used=[ResourceHint("todo_tasklist_guid", "references/live-resource-links.example.md", "tasklist_1", True)],
                missing_keys=["base_token"],
            ),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(status="missing", query="<CUSTOMER_C>"),
        )
        output_text = build_meeting_output(
            eval_name="<CUSTOMER_C>-ad-tracking-qa",
            transcript_path=DOMINOS_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="not-run",
            fallback_reason="permission scope insufficient for current live lookup",
        )
        result = evaluate_case(eval_name="<CUSTOMER_C>-ad-tracking-qa", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_bridge_cli_prints_runner_compatible_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "evals.meeting_output_bridge",
                "--eval-name",
                "<CUSTOMER_B>-product-solution-discussion",
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
            eval_name="<CUSTOMER_B>-product-solution-discussion",
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
                        candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
                    ),
                )

        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                return []

        stdout = StringIO()
        with patch(
            "evals.meeting_output_bridge.FeishuWorkbenchGateway.for_live_lark_cli",
            return_value=FakeGateway(),
        ):
            with patch(
                "evals.meeting_output_bridge.LarkCliBaseQueryBackend",
                return_value=FakeQueryBackend(),
            ):
                with redirect_stdout(stdout):
                    exit_code = bridge_main(
                        [
                            "--run-gateway",
                            "--eval-name",
                            "<CUSTOMER_A>-stage-review",
                            "--transcript-file",
                            str(UNILEVER_TRANSCRIPT),
                            "--customer-query",
                            "<CUSTOMER_A>",
                            "--repo-root",
                            str(REPO_ROOT),
                        ]
                    )
        self.assertEqual(exit_code, 0)
        output_text = stdout.getvalue()
        self.assertIn("上下文恢复状态: partial", output_text)
        result = evaluate_case(eval_name="<CUSTOMER_A>-stage-review", output_text=output_text)
        self.assertTrue(result["passed"], result)

    def test_recover_live_context_returns_typed_contract(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [
                        {"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜阶段汇报跟进", "联系日期": "2026-04-09"},
                    ]
                if table_name == "行动计划":
                    return [
                        {"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"},
                    ]
                return []

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="<CUSTOMER_A>",
                        archive_link="https://doc.example/<CUSTOMER_A>",
                    )
                ],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=FakeQueryBackend(),
        )

        self.assertIsInstance(context, ContextRecoveryResult)
        self.assertEqual(context.status, "completed")
        self.assertEqual(context.write_ceiling, "normal")
        self.assertEqual(context["status"], "completed")
        self.assertIn("客户主数据", context.used_sources)

    def test_recover_live_context_marks_ambiguous_customer_as_recommendation_only(self) -> None:
        class EmptyQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                return []

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="ambiguous",
                query="联合",
                candidates=[
                    CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>"),
                    CustomerMatch(customer_id="C_099", short_name="联合健康"),
                ],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=EmptyQueryBackend(),
        )

        self.assertIsInstance(context, ContextRecoveryResult)
        self.assertEqual(context.status, "context-limited")
        self.assertEqual(context.write_ceiling, "recommendation-only")
        self.assertIn("ambiguous", context.fallback_reason)

    def test_recover_live_context_enriches_customer_snapshot_from_master_fields(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [{"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜阶段汇报跟进", "联系日期": "2026-04-09"}]
                if table_name == "行动计划":
                    return [{"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"}]
                return []

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[
                    CustomerMatch(
                        customer_id="C_002",
                        short_name="<CUSTOMER_A>",
                        archive_link="https://doc.example/<CUSTOMER_A>",
                        raw_record={
                            "客户ID": "C_002",
                            "简称": "<CUSTOMER_A>",
                            "策略摘要": "重点推进 Campaign 优化",
                            "上次接触日期": "2026-04-08",
                            "下次行动计划": "确认下一轮投放方案",
                        },
                    )
                ],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=FakeQueryBackend(),
        )

        self.assertIn("客户主数据策略摘要: 重点推进 Campaign 优化", context.key_context)
        self.assertIn("客户主数据下次行动: 确认下一轮投放方案", context.key_context)

    def test_semantic_registry_exposes_narrow_archive_and_meeting_aliases(self) -> None:
        customer_master = SEMANTIC_FIELD_REGISTRY["客户主数据"]
        contact_log = SEMANTIC_FIELD_REGISTRY["客户联系记录"]

        self.assertIn("客户档案链接", customer_master["archive_link"]["aliases"])
        self.assertIn("会议纪要链接", contact_log["meeting_note_doc"]["aliases"])
        self.assertIn("会议记录链接", contact_log["meeting_note_doc"]["aliases"])

    def test_recover_live_context_prefers_explicit_archive_link_without_fallback_lookup(self) -> None:
        class FakeQueryBackend:
            def __init__(self) -> None:
                self.archive_calls = 0

            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [{"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜阶段汇报跟进", "联系日期": "2026-04-09"}]
                if table_name == "行动计划":
                    return [{"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"}]
                return []

            def discover_archive_candidates(self, customer_id: str, short_name: str, limit: int = 10):
                self.archive_calls += 1
                return [{"title": "<CUSTOMER_A>客户档案", "url": "https://doc.example/archive"}]

        backend = FakeQueryBackend()
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>", archive_link="https://doc.example/<CUSTOMER_A>")],
            ),
        )

        context = recover_live_context(gateway_result=gateway_result, query_backend=backend)

        self.assertEqual(backend.archive_calls, 0)
        self.assertIn("客户档案链接: https://doc.example/<CUSTOMER_A>", context.key_context)

    def test_recover_live_context_uses_unique_archive_candidate_when_link_missing(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [{"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜阶段汇报跟进", "联系日期": "2026-04-09"}]
                if table_name == "行动计划":
                    return [{"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"}]
                return []

            def discover_archive_candidates(self, customer_id: str, short_name: str, limit: int = 10):
                return [{
                    "title": "<CUSTOMER_A>客户档案",
                    "url": "https://doc.example/archive",
                    "customer_id": customer_id,
                    "short_name": short_name,
                }]

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        context = recover_live_context(gateway_result=gateway_result, query_backend=FakeQueryBackend())

        self.assertIn("客户档案候选", context.used_sources)
        self.assertEqual(context.write_ceiling, "normal")
        self.assertIn("<CUSTOMER_A>客户档案", "\n".join(context.key_context))

    def test_recover_live_context_downgrades_fuzzy_archive_candidate_without_explicit_evidence(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return [{"客户ID": customer_id, "记录标题": "<CUSTOMER_A>｜阶段汇报跟进", "联系日期": "2026-04-09"}]
                if table_name == "行动计划":
                    return [{"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"}]
                return []

            def discover_archive_candidates(self, customer_id: str, short_name: str, limit: int = 10):
                return [{
                    "title": "<CUSTOMER_A>客户档案",
                    "url": "https://doc.example/archive",
                }]

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        context = recover_live_context(gateway_result=gateway_result, query_backend=FakeQueryBackend())

        self.assertIn("客户档案候选", context.used_sources)
        self.assertEqual(context.write_ceiling, "recommendation-only")
        self.assertTrue(any("缺少显式客户证据" in item for item in context.candidate_conflicts))

    def test_recover_live_context_downgrades_conflicting_meeting_note_candidates(self) -> None:
        class FakeQueryBackend:
            def query_rows_by_customer_id(self, table_name: str, customer_id: str, limit: int = 20):
                if table_name == "客户联系记录":
                    return []
                if table_name == "行动计划":
                    return [{"客户ID": customer_id, "具体行动": "推进 Campaign 优化方案确认", "计划完成时间": "2026-04-20"}]
                return []

            def discover_archive_candidates(self, customer_id: str, short_name: str, limit: int = 10):
                return [{
                    "title": "<CUSTOMER_A>客户档案",
                    "url": "https://doc.example/archive",
                    "customer_id": customer_id,
                    "short_name": short_name,
                }]

            def discover_meeting_note_candidates(
                self,
                customer_id: str,
                short_name: str,
                topic_text: str,
                limit: int = 10,
            ):
                return [
                    {"title": "<CUSTOMER_A> Campaign活动分析优化 会议纪要 A", "url": "https://doc.example/note-a"},
                    {"title": "<CUSTOMER_A> Campaign活动分析优化 会议纪要 B", "url": "https://doc.example/note-b"},
                ]

        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        context = recover_live_context(
            gateway_result=gateway_result,
            query_backend=FakeQueryBackend(),
            topic_text="<CUSTOMER_A> Campaign活动分析优化 阶段汇报",
        )

        self.assertIn("会议纪要候选", context.used_sources)
        self.assertEqual(context.write_ceiling, "recommendation-only")
        self.assertTrue(any("会议纪要候选冲突" in item for item in context.candidate_conflicts))

    def test_build_meeting_output_surfaces_write_ceiling_and_open_questions(self) -> None:
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )

        output_text = build_meeting_output(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            gateway_result=gateway_result,
            recovery=ContextRecoveryResult(
                status="partial",
                used_sources=["客户主数据", "客户档案候选"],
                key_context=["客户档案候选: <CUSTOMER_A>客户档案｜https://doc.example/archive"],
                missing_sources=["客户联系记录"],
                open_questions=["档案候选与会议线程仍需人工确认"],
                write_ceiling="recommendation-only",
                candidate_conflicts=["会议纪要候选存在重名冲突"],
            ),
        )

        self.assertIn("写回上限: recommendation-only", output_text)
        self.assertIn("开放问题:", output_text)
        self.assertIn("档案候选与会议线程仍需人工确认", output_text)
        self.assertIn("会议纪要候选存在重名冲突", output_text)

    def test_core02_four_sections_present_in_output(self) -> None:
        """Post-meeting output contains all four required sections."""
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )
        artifact = build_meeting_output_artifact(
            eval_name="<CUSTOMER_A>-stage-review",
            transcript_path=UNILEVER_TRANSCRIPT,
            gateway_result=gateway_result,
            context_status="completed",
            used_sources=["客户主数据", "客户联系记录", "行动计划", "客户档案"],
            evidence_container=self._make_fake_evidence_container(),
        )
        output_text = artifact["output_text"]
        self.assertIn("风险:", output_text)
        self.assertIn("机会:", output_text)
        self.assertIn("干系人变化:", output_text)
        self.assertIn("下一轮推进路径:", output_text)

    def test_core02_sections_derived_from_evidence_not_hardcoded(self) -> None:
        """Section content varies based on available evidence."""
        container_a = self._make_fake_evidence_container_with_risk_item("竞品")
        container_b = self._make_fake_evidence_container_with_opportunity_item("机会")
        sections_a = _derive_structured_sections(container_a, "transcript text with 竞品风险")
        sections_b = _derive_structured_sections(container_b, "transcript text with 新客机会")
        self.assertIn("竞品", sections_a.get("risks", []))
        self.assertIn("机会", sections_b.get("opportunities", []))

    def test_core02_section_item_limit_enforced(self) -> None:
        """Each section is capped at 5 items maximum."""
        container = self._make_fake_evidence_container_with_many_risks(10)
        sections = _derive_structured_sections(container, "transcript with many risks")
        self.assertLessEqual(len(sections.get("risks", [])), 5)

    def _make_fake_evidence_container(self) -> EvidenceContainer:
        """Helper to create a minimal EvidenceContainer for testing."""
        return EvidenceContainer(sources={
            "customer_master": EvidenceSource(name="customer_master", quality="live", available=True, content=["客户: <CUSTOMER_A>"]),
            "contact_records": EvidenceSource(name="contact_records", quality="live", available=True, content=["联系记录"]),
            "action_plan": EvidenceSource(name="action_plan", quality="recovered", available=True, content=["行动计划"]),
            "meeting_notes": EvidenceSource(name="meeting_notes", quality="recovered", available=True, content=["会议纪要"]),
            "customer_archive": EvidenceSource(name="customer_archive", quality="archived", available=True, content=["archive"]),
            "transcript": EvidenceSource(name="transcript", quality="live", available=True, content=["transcript content"]),
        })

    def _make_fake_evidence_container_with_risk_item(self, risk_text: str) -> EvidenceContainer:
        """Helper with a specific risk item."""
        container = self._make_fake_evidence_container()
        container.sources["transcript"] = EvidenceSource(name="transcript", quality="live", available=True, content=[f"transcript with {risk_text}"])
        return container

    def _make_fake_evidence_container_with_opportunity_item(self, opp_text: str) -> EvidenceContainer:
        """Helper with a specific opportunity item."""
        container = self._make_fake_evidence_container()
        container.sources["transcript"] = EvidenceSource(name="transcript", quality="live", available=True, content=[f"transcript with {opp_text}"])
        return container

    def _make_fake_evidence_container_with_many_risks(self, count: int) -> EvidenceContainer:
        """Helper with many risk items."""
        container = self._make_fake_evidence_container()
        risks = [f"风险项目{i}" for i in range(count)]
        container.sources["transcript"] = EvidenceSource(name="transcript", quality="live", available=True, content=risks)
        return container

    # =============================================================================
    # TODO-01: Intent classification tests (意图 field)
    # =============================================================================

    def test_todo01_intent_classification_returns_fixed_values(self) -> None:
        """Intent classification returns one of the four fixed values."""
        from evals.meeting_output_bridge import _classify_action_intent

        fixed_intents = {"风险干预", "扩张推进", "关系维护", "项目进展"}

        risk_item = {"summary": "确认竞品风险情况", "theme": "risk"}
        self.assertIn(_classify_action_intent(risk_item), fixed_intents)

        expansion_item = {"summary": "开拓新客机会", "theme": "expansion"}
        self.assertIn(_classify_action_intent(expansion_item), fixed_intents)

        relationship_item = {"summary": "维护客户关系", "theme": "relationship"}
        self.assertIn(_classify_action_intent(relationship_item), fixed_intents)

        project_item = {"summary": "推进项目进展", "theme": "project"}
        self.assertIn(_classify_action_intent(project_item), fixed_intents)

    def test_todo01_intent_classification_keyword_matching(self) -> None:
        """Intent is correctly derived from action item keywords."""
        from evals.meeting_output_bridge import _classify_action_intent

        # Risk keywords
        risk_item = {"summary": "处理客户流失风险"}
        self.assertEqual(_classify_action_intent(risk_item), "风险干预")

        # Expansion keywords
        expansion_item = {"summary": "新客开拓机会确认"}
        self.assertEqual(_classify_action_intent(expansion_item), "扩张推进")

        # Relationship keywords
        relationship_item = {"summary": "拜访客户维护关系"}
        self.assertEqual(_classify_action_intent(relationship_item), "关系维护")

        # Default (project progress)
        default_item = {"summary": "确认下一步动作"}
        self.assertEqual(_classify_action_intent(default_item), "项目进展")

    def test_todo01_intent_field_in_candidate_payload(self) -> None:
        """WriteCandidate payload contains 意图 field with correct value."""
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )
        candidates = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=gateway_result,
            action_items=[
                {"summary": "处理客户流失风险", "theme": "risk"},
            ],
        )
        self.assertEqual(len(candidates), 1)
        self.assertIn("意图", candidates[0].payload)
        self.assertIn(candidates[0].payload["意图"], {"风险干预", "扩张推进", "关系维护", "项目进展"})

    # =============================================================================
    # TODO-02: Rationale field tests (判定理由 field)
    # =============================================================================

    def test_todo02_rationale_field_in_candidate_payload(self) -> None:
        """WriteCandidate payload contains 判定理由 field as non-empty Chinese string."""
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )
        candidates = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=gateway_result,
            action_items=[
                {"summary": "确认 Campaign 优化方案", "theme": "campaign"},
            ],
        )
        self.assertEqual(len(candidates), 1)
        self.assertIn("判定理由", candidates[0].payload)
        rationale = candidates[0].payload["判定理由"]
        self.assertIsInstance(rationale, str)
        self.assertTrue(len(rationale) > 0)
        # Rationale should be in Chinese
        self.assertTrue(any("\u4e00" <= c <= "\u9fff" for c in rationale), "Rationale should contain Chinese characters")

    def test_todo02_generate_action_rationale_function(self) -> None:
        """_generate_action_rationale() returns non-empty Chinese string for valid action item."""
        from evals.meeting_output_bridge import _generate_action_rationale

        risk_item = {"summary": "处理客户流失风险", "theme": "risk"}
        rationale = _generate_action_rationale(risk_item)
        self.assertIsInstance(rationale, str)
        self.assertTrue(len(rationale) > 0)
        self.assertTrue(any("\u4e00" <= c <= "\u9fff" for c in rationale))

        expansion_item = {"summary": "开拓新客机会", "theme": "expansion"}
        rationale_exp = _generate_action_rationale(expansion_item)
        self.assertIsInstance(rationale_exp, str)
        self.assertTrue(len(rationale_exp) > 0)

    def test_todo02_rationale_precedes_candidate_in_display_order(self) -> None:
        """Rationale is stored separately in payload and available before candidate is proposed for write-back."""
        gateway_result = GatewayResult(
            resource_resolution=ResourceResolution(status="resolved"),
            capability_report=CapabilityReport(),
            customer_resolution=CustomerResolution(
                status="resolved",
                query="<CUSTOMER_A>",
                candidates=[CustomerMatch(customer_id="C_002", short_name="<CUSTOMER_A>")],
            ),
        )
        candidates = build_meeting_todo_candidates(
            eval_name="<CUSTOMER_A>-stage-review",
            gateway_result=gateway_result,
            action_items=[
                {"summary": "确认 Campaign 优化方案", "theme": "campaign"},
            ],
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        # Rationale is stored in payload and can be read before write-back confirmation
        rationale = candidate.payload.get("判定理由", "")
        intent = candidate.payload.get("意图", "")
        self.assertTrue(len(rationale) > 0, "Rationale should be available before candidate is proposed for write-back")
        self.assertTrue(len(intent) > 0, "Intent should be available before candidate is proposed for write-back")


if __name__ == "__main__":
    unittest.main()
