"""Smoke tests for the local runtime layer."""

from __future__ import annotations

import json
import sys
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runtime import (  # noqa: E402
    LarkCliBaseQueryBackend,
    CustomerResolver,
    FeishuWorkbenchGateway,
    LarkCliClient,
    LarkCliCommandError,
    LiveCapabilityReporter,
    LarkCliCustomerBackend,
    LarkCliResourceProbe,
    LarkCliSchemaBackend,
    LiveWorkbenchConfig,
    ResourceResolver,
    RuntimeSourceLoader,
    SchemaPreflightRunner,
    TodoWriter,
    WriteGuard,
    render_live_diagnostic,
    TABLE_PROFILES,
    get_required_base_tables,
)
from runtime.diagnostics import suggest_next_actions  # noqa: E402
from runtime.models import TodoWriteResult, WriteCandidate, WriteExecutionResult  # noqa: E402
from runtime.scene_registry import (  # noqa: E402
    UnknownSceneError,
    build_default_scene_registry,
    dispatch_scene,
)
from runtime.scene_runtime import SceneRequest, SceneResult  # noqa: E402
import runtime.scene_runtime as scene_runtime  # noqa: E402
import runtime.__main__ as runtime_main  # noqa: E402


class FakeCustomerBackend:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows

    def search_customer_master(self, query: str) -> list[dict[str, str]]:
        return [
            row
            for row in self.rows
            if query in row.get("简称", "")
            or query in row.get("客户名称", "")
            or query == row.get("客户ID")
        ]


class FakeSchemaBackend:
    def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
        if object_name == "行动计划":
            return {
                "action_type": {
                    "field_id": "fld_action_type",
                    "name": "行动类型_单选",
                    "type": "single_select",
                    "options": ["客户经营", "续费沟通"],
                    "synonyms": {"经营": "客户经营"},
                    "allowed_live_types": ["single_select"],
                    "write_policy": "safe_update",
                },
                "subject": {
                    "field_id": "fld_subject",
                    "name": "具体行动",
                    "type": "text",
                    "allowed_live_types": ["text"],
                    "write_policy": "required_create",
                },
                "owner": {
                    "field_id": "fld_owner",
                    "name": "负责人",
                    "type": "text",
                    "allowed_live_types": ["text"],
                    "write_policy": "safe_update",
                },
                "due_at": {
                    "field_id": "fld_due",
                    "name": "计划完成时间",
                    "type": "datetime",
                    "allowed_live_types": ["datetime", "text"],
                    "write_policy": "safe_update",
                },
            }
        if object_name == "客户主数据":
            return {
                "last_contact_at": {
                    "field_id": "fld_last_contact",
                    "name": "上次接触日期",
                    "type": "datetime",
                    "allowed_live_types": ["datetime", "text"],
                    "write_policy": "safe_update",
                },
                "next_action_summary": {
                    "field_id": "fld_next_action",
                    "name": "下次行动计划",
                    "type": "text",
                    "allowed_live_types": ["text"],
                    "write_policy": "safe_update",
                },
                "strategy_summary": {
                    "field_id": "fld_strategy_summary",
                    "name": "策略摘要",
                    "type": "text",
                    "allowed_live_types": ["text"],
                    "write_policy": "safe_update",
                },
                "renewal_risk": {
                    "field_id": "fld_risk",
                    "name": "续费风险",
                    "type": "single_select",
                    "options": ["🟢 低", "🟡 中"],
                    "allowed_live_types": ["single_select"],
                    "write_policy": "guarded_update",
                },
            }
        if object_name == "待办":
            return {
                "summary": {
                    "field_id": "todo_summary",
                    "name": "标题",
                    "type": "text",
                    "allowed_live_types": ["text"],
                    "write_policy": "required_create",
                },
                "description": {
                    "field_id": "todo_description",
                    "name": "描述",
                    "type": "text",
                    "allowed_live_types": ["text"],
                    "write_policy": "safe_update",
                },
                "due_at": {
                    "field_id": "todo_due",
                    "name": "截止时间",
                    "type": "datetime",
                    "allowed_live_types": ["datetime"],
                    "write_policy": "safe_update",
                },
                "owner": {
                    "field_id": "todo_owner",
                    "name": "负责人",
                    "type": "user",
                    "allowed_live_types": ["user"],
                    "write_policy": "required_create",
                    "valid_member_ids": ["ou_owner", "ou_editor"],
                },
                "priority": {
                    "field_id": "todo_priority",
                    "name": "优先级",
                    "type": "single_select",
                    "options": ["高", "中", "低"],
                    "synonyms": {"高优先级": "高"},
                    "allowed_live_types": ["single_select"],
                    "write_policy": "safe_update",
                },
            }
        return None


class FakeRunner:
    def __init__(self, responses: dict[str, subprocess.CompletedProcess[str]]) -> None:
        self.responses = responses

    def __call__(self, command, capture_output, text, check):
        key = " ".join(command[1:])
        return self.responses[key]


class RuntimeSmokeTests(unittest.TestCase):
    TEST_RUNTIME_ENV = {
        "FEISHU_AM_WORKBENCH_BASE_URL": "https://example.com/base/app_example_base_token?table=tbl_customer_master_example",
        "FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER": "fld_customer_archive_example",
        "FEISHU_AM_MEETING_NOTES_FOLDER": "fld_meeting_notes_example",
        "FEISHU_AM_TODO_TASKLIST_GUID": "00000000-0000-4000-8000-000000000001",
        "FEISHU_AM_TODO_CUSTOMER_FIELD_GUID": "a7009aff-7d85-4378-82c9-1584873f469d",
        "FEISHU_AM_TODO_PRIORITY_FIELD_GUID": "f7587037-8ad1-443c-b350-f6600e0ccadd",
    }
    CLEARED_RUNTIME_ENV = (
        "FEISHU_AM_BASE_TOKEN",
        "FEISHU_AM_CUSTOMER_MASTER_TABLE_ID",
    )

    def setUp(self) -> None:
        self._env_backup = {
            key: os.environ.get(key)
            for key in (*self.TEST_RUNTIME_ENV, *self.CLEARED_RUNTIME_ENV)
        }
        for key, value in self.TEST_RUNTIME_ENV.items():
            os.environ[key] = value
        for key in self.CLEARED_RUNTIME_ENV:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_runtime_source_loader_requires_env_for_live_resource_hints(self) -> None:
        env_backup = {key: os.environ.get(key) for key in RuntimeSourceLoader.ENV_VARS.values()}
        try:
            for key in RuntimeSourceLoader.ENV_VARS.values():
                os.environ.pop(key, None)

            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                (root / "references").mkdir()
                (root / "references" / "actual-field-mapping.md").write_text(
                    "tasklist_guid: 11111111-1111-1111-1111-111111111111\n",
                    encoding="utf-8",
                )
                (root / "references" / "workbench-information-architecture.md").write_text(
                    "Layer 4: Customer archive Location: Feishu docs folder `archive_from_repo`\n",
                    encoding="utf-8",
                )
                (root / "references" / "update-routing.md").write_text(
                    "Default meeting-note folder: `meeting_notes_from_repo`\n",
                    encoding="utf-8",
                )
                (root / "references" / "live-resource-links.example.md").write_text(
                    "Workbench Base: `https://example.com/base/app_token?table=tbl123`\n",
                    encoding="utf-8",
                )
                (root / "SKILL.md").write_text(
                    "dedicated Feishu folder `skill_meeting_notes`\n",
                    encoding="utf-8",
                )

                sources = RuntimeSourceLoader(root).load()

            self.assertIsNone(sources.base_token)
            self.assertIsNone(sources.customer_archive_folder)
            self.assertIsNone(sources.meeting_notes_folder)
            self.assertIsNone(sources.todo_tasklist_guid)
            self.assertEqual(sources.source_files, [])
        finally:
            for key, value in env_backup.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_runtime_source_loader_uses_env_backed_values_only(self) -> None:
        env_backup = {key: os.environ.get(key) for key in RuntimeSourceLoader.ENV_VARS.values()}
        try:
            os.environ["FEISHU_AM_WORKBENCH_BASE_URL"] = "https://example.com/base/app_token?table=tbl123"
            os.environ["FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER"] = "archive_folder"
            os.environ["FEISHU_AM_MEETING_NOTES_FOLDER"] = "meeting_folder"
            os.environ["FEISHU_AM_TODO_TASKLIST_GUID"] = "22222222-2222-2222-2222-222222222222"

            with tempfile.TemporaryDirectory() as temp_dir:
                sources = RuntimeSourceLoader(Path(temp_dir)).load()

            self.assertEqual(sources.base_token.value, "app_token")
            self.assertEqual(sources.base_token.source_file, "env:FEISHU_AM_WORKBENCH_BASE_URL")
            self.assertEqual(sources.customer_master_table_id.value, "tbl123")
            self.assertEqual(sources.customer_archive_folder.source_file, "env:FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER")
            self.assertEqual(sources.meeting_notes_folder.source_file, "env:FEISHU_AM_MEETING_NOTES_FOLDER")
            self.assertEqual(sources.todo_tasklist_guid.source_file, "env:FEISHU_AM_TODO_TASKLIST_GUID")
            self.assertIn("env:FEISHU_AM_WORKBENCH_BASE_URL", sources.source_files)
        finally:
            for key, value in env_backup.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_write_candidate_supports_shared_write_metadata(self) -> None:
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner"],
            payload={"summary": "跟进联合利华续费", "owner": "ou_owner"},
            operation="create",
            match_basis={"customer": "联合利华", "time_window": "2026-04"},
            source_context={"scenario": "post_meeting", "customer_id": "C_002"},
            target_object="todo",
        )
        self.assertEqual(candidate.operation, "create")
        self.assertEqual(candidate.target_object, "todo")
        self.assertEqual(candidate.match_basis["customer"], "联合利华")
        self.assertEqual(candidate.source_context["scenario"], "post_meeting")

    def test_write_execution_result_structured_result_preserves_blocked_evidence(self) -> None:
        result = WriteExecutionResult(
            target_object="todo",
            attempted=False,
            allowed=False,
            preflight_status="safe",
            guard_status="blocked",
            dedupe_decision="update_existing",
            executed_operation="blocked",
            remote_object_id="task_existing",
            blocked_reasons=["semantic_duplicate_detected"],
            source_context={"scenario": "post_meeting", "customer_id": "C_002"},
            remote_metadata={"dedupe_target": "task_existing"},
        )

        envelope = result.structured_result()

        self.assertEqual(envelope["preflight_status"], "safe")
        self.assertEqual(envelope["guard_status"], "blocked")
        self.assertEqual(envelope["dedupe_decision"], "update_existing")
        self.assertEqual(envelope["remote_metadata"]["object_id"], "task_existing")
        self.assertEqual(envelope["remote_metadata"]["dedupe_target"], "task_existing")

        envelope["blocked_reasons"].append("extra")
        envelope["source_context"]["customer_id"] = "changed"

        self.assertEqual(result.blocked_reasons, ["semantic_duplicate_detected"])
        self.assertEqual(result.source_context["customer_id"], "C_002")

    def test_todo_write_result_structured_result_keeps_remote_metadata_for_allowed_path(self) -> None:
        result = TodoWriteResult(
            target_object="todo",
            attempted=True,
            allowed=True,
            preflight_status="safe",
            guard_status="allowed",
            dedupe_decision="create_new",
            executed_operation="create",
            remote_object_id="task_guid_1",
            remote_url="https://applink.feishu.cn/client/todo/detail?guid=task_guid_1",
            remote_metadata={"object_type": "task"},
            source_context={"scenario": "post_meeting"},
        )

        envelope = result.structured_result()

        self.assertEqual(result.task_guid, "task_guid_1")
        self.assertEqual(result.task_url, "https://applink.feishu.cn/client/todo/detail?guid=task_guid_1")
        self.assertEqual(envelope["remote_metadata"]["object_id"], "task_guid_1")
        self.assertEqual(envelope["remote_metadata"]["url"], "https://applink.feishu.cn/client/todo/detail?guid=task_guid_1")
        self.assertEqual(envelope["remote_metadata"]["object_type"], "task")

    def test_todo_writer_returns_shared_execution_result_for_blocked_candidate(self) -> None:
        class RaisingRunner:
            def __call__(self, command, capture_output, text, check):
                raise AssertionError("task create should not be invoked when preflight is blocked")

        client = LarkCliClient(runner=RaisingRunner())
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(FakeSchemaBackend()),
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "priority", "customer"],
            payload={
                "summary": "跟进联合利华续费",
                "owner": "ou_owner",
                "priority": "高",
                "customer": "联合利华",
            },
            operation="create",
            target_object="todo",
        )
        result = writer.create(candidate)
        self.assertEqual(result.preflight_status, "blocked")
        self.assertEqual(result.guard_status, "blocked")
        self.assertEqual(result.executed_operation, "blocked")
        self.assertEqual(result.dedupe_decision, "no_write")
        self.assertIn("todo_custom_field_missing", result.blocked_reasons)

    def test_todo_writer_updates_semantic_duplicate_instead_of_creating(self) -> None:
        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "customer_guid",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "priority": {
                        "field_id": "priority_guid",
                        "name": "优先级",
                        "type": "single_select",
                        "options": ["高", "中", "低"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    },
                }

        responses = {
            (
                'task tasks get --params {"task_guid": "task_existing"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"task":{"guid":"task_existing","url":"https://applink.feishu.cn/client/todo/detail?guid=task_existing",'
                    '"members":[{"id":"ou_owner","role":"assignee","type":"user"}]}}}'
                ),
                stderr="",
            ),
            (
                'task tasks patch --params {"task_guid": "task_existing"} --data '
                '{"task": {"summary": "跟进联合利华续费方案", '
                '"due": {"timestamp": "1776643200000", "is_all_day": true}, '
                '"custom_fields": [{"guid": "a7009aff-7d85-4378-82c9-1584873f469d", "text_value": "联合利华"}]}, '
                '"update_fields": ["summary", "due", "custom_fields"]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"task":{"guid":"task_existing","url":"https://applink.feishu.cn/client/todo/detail?guid=task_existing"}}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "guid": "task_existing",
                    "summary": "推进联合利华续费方案确认",
                    "customer": "联合利华",
                    "due_at": "2026-04-18",
                }
            ],
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "customer", "priority"],
            payload={
                "summary": "跟进联合利华续费方案",
                "owner": "ou_owner",
                "customer": "联合利华",
                "priority": "高",
                "due_at": "2026-04-20",
            },
            operation="create",
            target_object="todo",
            match_basis={"customer": "联合利华", "time_window": "2026-04"},
        )
        result = writer.create(candidate)
        self.assertTrue(result.attempted)
        self.assertTrue(result.allowed)
        self.assertEqual(result.dedupe_decision, "update_existing")
        self.assertEqual(result.executed_operation, "update")
        self.assertEqual(result.remote_object_id, "task_existing")
        self.assertEqual(result.blocked_reasons, [])

    def test_todo_writer_handles_chinese_punctuation_variant_as_duplicate(self) -> None:
        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "customer_guid",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "priority": {
                        "field_id": "priority_guid",
                        "name": "优先级",
                        "type": "single_select",
                        "options": ["高", "中", "低"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    },
                }

        responses = {
            (
                'task tasks get --params {"task_guid": "task_existing"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"task":{"guid":"task_existing","url":"https://applink.feishu.cn/client/todo/detail?guid=task_existing",'
                    '"members":[{"id":"ou_owner","role":"assignee","type":"user"}]}}}'
                ),
                stderr="",
            ),
            (
                'task tasks patch --params {"task_guid": "task_existing"} --data '
                '{"task": {"summary": "跟进联合利华 AI 埋点产品介绍给触脉确认", '
                '"custom_fields": [{"guid": "a7009aff-7d85-4378-82c9-1584873f469d", "text_value": "联合利华"}]}, '
                '"update_fields": ["summary", "custom_fields"]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"task":{"guid":"task_existing","url":"https://applink.feishu.cn/client/todo/detail?guid=task_existing"}}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "guid": "task_existing",
                    "summary": "联合利华-AI埋点产品介绍给触脉（王奇）",
                    "customer": "联合利华",
                    "due_at": "2026-04-18",
                }
            ],
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "customer", "priority"],
            payload={
                "summary": "跟进联合利华 AI 埋点产品介绍给触脉确认",
                "owner": "ou_owner",
                "customer": "联合利华",
                "priority": "高",
            },
            operation="create",
            target_object="todo",
            match_basis={"customer": "联合利华", "time_window": "2026-04"},
        )
        result = writer.create(candidate)
        self.assertEqual(result.dedupe_decision, "update_existing")
        self.assertEqual(result.executed_operation, "update")
        self.assertEqual(result.remote_object_id, "task_existing")

    def test_todo_writer_recommends_create_subtask_for_step_level_duplicate(self) -> None:
        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "customer_guid",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                }

        class RaisingRunner:
            def __call__(self, command, capture_output, text, check):
                raise AssertionError("no write should be attempted when subtask is recommended")

        client = LarkCliClient(runner=RaisingRunner())
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "guid": "task_parent",
                    "summary": "联合利华 活动 优化 方案",
                    "customer": "联合利华",
                    "due_at": "2026-04-20",
                }
            ],
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "customer"],
            payload={
                "summary": "整理联合利华活动优化方案并发送会前资料",
                "owner": "ou_owner",
                "customer": "联合利华",
            },
            operation="create",
            target_object="todo",
            match_basis={"customer": "联合利华", "time_window": "2026-04"},
        )
        result = writer.create(candidate)
        self.assertFalse(result.attempted)
        self.assertEqual(result.dedupe_decision, "create_subtask")
        self.assertEqual(result.executed_operation, "blocked")
        self.assertIn("subtask_recommended", result.blocked_reasons)

    def test_todo_writer_creates_subtask_when_explicitly_confirmed(self) -> None:
        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "customer_guid",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                }

        responses = {
            (
                'task tasks create --data '
                '{"summary": "整理联合利华活动优化方案并发送会前资料", '
                '"tasklists": [{"tasklist_guid": "00000000-0000-4000-8000-000000000001"}], '
                '"members": [{"id": "ou_owner", "role": "assignee", "type": "user"}], '
                '"custom_fields": [{"guid": "a7009aff-7d85-4378-82c9-1584873f469d", "text_value": "联合利华"}], '
                '"parent_task_guid": "task_parent"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"task":{"guid":"task_sub_1",'
                    '"url":"https://applink.feishu.cn/client/todo/detail?guid=task_sub_1"}}}'
                ),
                stderr="",
            )
        }

        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "guid": "task_parent",
                    "summary": "联合利华 活动 优化 方案",
                    "customer": "联合利华",
                    "due_at": "2026-04-20",
                }
            ],
        )

        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "customer"],
            payload={
                "summary": "整理联合利华活动优化方案并发送会前资料",
                "owner": "ou_owner",
                "customer": "联合利华",
            },
            operation="create",
            target_object="todo",
            match_basis={"customer": "联合利华", "time_window": "2026-04"},
            source_context={"confirm_create_subtask": True},
        )
        result = writer.create(candidate)

        self.assertTrue(result.attempted)
        self.assertTrue(result.allowed)
        self.assertEqual(result.dedupe_decision, "create_subtask")
        self.assertEqual(result.executed_operation, "create")
        self.assertEqual(result.remote_object_id, "task_sub_1")

    def test_table_profiles_cover_runtime_and_expansion_tables(self) -> None:
        self.assertEqual(TABLE_PROFILES["客户主数据"].table_role, "snapshot")
        self.assertEqual(TABLE_PROFILES["客户联系记录"].table_role, "detail")
        self.assertEqual(TABLE_PROFILES["行动计划"].table_role, "detail")
        self.assertEqual(TABLE_PROFILES["客户关键人地图"].table_role, "detail")
        self.assertEqual(TABLE_PROFILES["合同清单"].table_role, "detail")
        self.assertEqual(TABLE_PROFILES["竞品基础信息表"].table_role, "dimension")
        self.assertEqual(TABLE_PROFILES["竞品交锋记录"].table_role, "bridge")
        self.assertEqual(
            get_required_base_tables(),
            ["客户主数据", "行动计划", "客户联系记录"],
        )
        self.assertFalse(TABLE_PROFILES["合同清单"].capability_required)

    def test_live_config_builds_table_targets_for_all_integrated_tables(self) -> None:
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        self.assertEqual(config.table_target("客户主数据"), "tbl_customer_master_example")
        self.assertEqual(config.table_target("客户联系记录"), "客户联系记录")
        self.assertEqual(config.table_target("行动计划"), "行动计划")
        self.assertEqual(config.table_target("客户关键人地图"), "客户关键人地图")
        self.assertEqual(config.table_target("合同清单"), "合同清单")
        self.assertEqual(config.table_target("竞品基础信息表"), "竞品基础信息表")
        self.assertEqual(config.table_target("竞品交锋记录"), "竞品交锋记录")

    def test_runtime_source_loader_reads_known_hints(self) -> None:
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        self.assertEqual(sources.base_token.value, "app_example_base_token")
        self.assertEqual(sources.customer_master_table_id.value, "tbl_customer_master_example")
        self.assertEqual(sources.meeting_notes_folder.value, "fld_meeting_notes_example")
        self.assertEqual(sources.todo_tasklist_guid.value, "00000000-0000-4000-8000-000000000001")
        self.assertEqual(sources.customer_archive_folder.value, "fld_customer_archive_example")
        self.assertEqual(
            sources.todo_customer_field_guid.value,
            "a7009aff-7d85-4378-82c9-1584873f469d",
        )
        self.assertEqual(
            sources.todo_priority_field_guid.value,
            "f7587037-8ad1-443c-b350-f6600e0ccadd",
        )
        self.assertEqual(sources.todo_priority_options, [])

    def test_customer_resolver_preserves_raw_row(self) -> None:
        backend = FakeCustomerBackend(
            [
                {
                    "客户ID": "C001",
                    "简称": "联合利华",
                    "客户名称": "联合利华中国",
                    "客户档案": "https://doc.example/u",
                }
            ]
        )
        resolution = CustomerResolver(backend).resolve("联合利华")
        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(resolution.candidates[0].raw_record["客户名称"], "联合利华中国")

    def test_customer_resolver_matches_customer_id_exactly(self) -> None:
        backend = FakeCustomerBackend(
            [
                {
                    "客户ID": "C_002",
                    "简称": "联合利华",
                    "客户名称": "联合利华中国",
                }
            ]
        )

        resolution = CustomerResolver(backend).resolve("C_002")

        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(resolution.candidates[0].customer_id, "C_002")

    def test_customer_resolver_resolves_single_remaining_candidate(self) -> None:
        backend = FakeCustomerBackend(
            [
                {
                    "客户ID": "C_002",
                    "简称": "联合利华华东",
                    "客户名称": "联合利华华东",
                }
            ]
        )

        resolution = CustomerResolver(backend).resolve("联合利华")

        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(resolution.candidates[0].short_name, "联合利华华东")

    def test_customer_resolver_returns_missing_when_no_candidate_exists(self) -> None:
        backend = FakeCustomerBackend([])

        resolution = CustomerResolver(backend).resolve("不存在客户")

        self.assertEqual(resolution.status, "missing")
        self.assertEqual(resolution.query, "不存在客户")
        self.assertEqual(resolution.candidates, [])

    def test_customer_resolver_returns_ambiguous_for_multiple_candidates(self) -> None:
        backend = FakeCustomerBackend(
            [
                {
                    "客户ID": "C_002",
                    "简称": "联合利华华东",
                    "客户名称": "联合利华华东",
                },
                {
                    "客户ID": "C_003",
                    "简称": "联合利华华北",
                    "客户名称": "联合利华华北",
                },
            ]
        )

        resolution = CustomerResolver(backend).resolve("联合利华")

        self.assertEqual(resolution.status, "ambiguous")
        self.assertEqual(len(resolution.candidates), 2)

    def test_customer_resolver_returns_ambiguous_for_multiple_exact_matches(self) -> None:
        backend = FakeCustomerBackend(
            [
                {
                    "客户ID": "C_002",
                    "简称": "联合利华",
                    "客户名称": "联合利华中国",
                },
                {
                    "客户ID": "C_003",
                    "简称": "联合利华",
                    "客户名称": "联合利华餐饮",
                },
            ]
        )

        resolution = CustomerResolver(backend).resolve("联合利华")

        self.assertEqual(resolution.status, "ambiguous")
        self.assertEqual(len(resolution.candidates), 2)

    def test_gateway_runs_full_smoke_flow(self) -> None:
        customer_backend = FakeCustomerBackend(
            [
                {
                    "客户ID": "C001",
                    "简称": "联合利华",
                    "客户名称": "联合利华中国",
                    "客户档案": "https://doc.example/u",
                }
            ]
        )
        gateway = FeishuWorkbenchGateway(
            repo_root=str(REPO_ROOT),
            customer_resolver=CustomerResolver(customer_backend),
            schema_preflight=SchemaPreflightRunner(FakeSchemaBackend()),
            write_guard=WriteGuard(protected_fields={"行动计划": {"forbidden_field"}}),
            live_config=LiveWorkbenchConfig.from_sources(RuntimeSourceLoader(REPO_ROOT).load()),
        )
        candidate = WriteCandidate(
            object_name="行动计划",
            layer="detail",
            semantic_fields=["subject", "action_type", "owner"],
            payload={
                "subject": "推进续费方案",
                "action_type": "经营",
                "owner": "liaoky",
            },
        )
        result = gateway.run(
            customer_query="联合利华",
            write_candidates=[candidate],
            owner_required_objects={"行动计划"},
        )
        self.assertEqual(result.resource_resolution.status, "resolved")
        self.assertEqual(result.customer_resolution.status, "resolved")
        self.assertEqual(result.preflight_reports[0].status, "safe_with_drift")
        self.assertIn(
            "option_synonym_resolved",
            result.preflight_reports[0].field_results[1].drift_items,
        )
        self.assertTrue(result.guard_results[0].allowed)

    def test_preflight_blocks_missing_option(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="行动计划",
            layer="detail",
            semantic_fields=["action_type"],
            payload={"action_type": "不存在的选项"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("option_missing_blocked", report.blocked_reasons)

    def test_preflight_blocks_type_incompatible_payload(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="行动计划",
            layer="detail",
            semantic_fields=["due_at"],
            payload={"due_at": {"unexpected": "shape"}},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("field_type_changed_blocked", report.blocked_reasons)

    def test_preflight_blocks_guarded_policy_field(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="客户主数据",
            layer="snapshot",
            semantic_fields=["renewal_risk"],
            payload={"renewal_risk": "🟡 中"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("protected_field_policy_changed", report.blocked_reasons)

    def test_preflight_marks_non_allowlisted_customer_master_field_for_guard_review(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="客户主数据",
            layer="snapshot",
            semantic_fields=["strategy_summary"],
            payload={"strategy_summary": "推进续费策略对齐"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "safe_with_drift")
        self.assertIn(
            "customer_master_direct_write_not_allowlisted",
            report.field_results[0].drift_items,
        )

    def test_write_guard_allows_only_low_risk_customer_master_fact_fields(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        allowed_candidate = WriteCandidate(
            object_name="客户主数据",
            layer="snapshot",
            semantic_fields=["last_contact_at", "next_action_summary"],
            payload={
                "last_contact_at": "2026-04-16",
                "next_action_summary": "下周确认续费节奏",
            },
        )
        allowed_report = runner.run(allowed_candidate)
        allowed_guard = WriteGuard().evaluate(allowed_candidate, allowed_report)
        self.assertEqual(allowed_report.status, "safe")
        self.assertTrue(allowed_guard.allowed)

        blocked_candidate = WriteCandidate(
            object_name="客户主数据",
            layer="snapshot",
            semantic_fields=["strategy_summary"],
            payload={"strategy_summary": "推进续费策略对齐"},
        )
        blocked_report = runner.run(blocked_candidate)
        blocked_guard = WriteGuard().evaluate(blocked_candidate, blocked_report)
        self.assertFalse(blocked_guard.allowed)
        self.assertIn(
            "customer_master_recommendation_only:strategy_summary",
            blocked_guard.reasons,
        )

    def test_preflight_marks_alias_resolution_as_drift(self) -> None:
        class AliasSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "行动计划":
                    return None
                return {
                    "行动类型_单选": {
                        "field_id": "fld_action_type",
                        "name": "行动类型_单选",
                        "type": "single_select",
                        "options": ["客户经营"],
                        "aliases": ["action_type"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    }
                }

        runner = SchemaPreflightRunner(AliasSchemaBackend())
        candidate = WriteCandidate(
            object_name="行动计划",
            layer="detail",
            semantic_fields=["action_type"],
            payload={"action_type": "客户经营"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "safe_with_drift")
        self.assertIn("field_renamed_alias_resolved", report.field_results[0].drift_items)

    def test_preflight_marks_option_synonym_resolution_as_drift(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["priority"],
            payload={"priority": "高优先级"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "safe_with_drift")
        self.assertIn("option_synonym_resolved", report.field_results[0].drift_items)
        self.assertEqual(report.field_results[0].option_result.resolved_option, "高")

    def test_preflight_blocks_missing_required_payload(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="行动计划",
            layer="detail",
            semantic_fields=["subject"],
            payload={},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("required_field_missing", report.blocked_reasons)

    def test_preflight_blocks_missing_todo_custom_field(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["customer"],
            payload={"customer": "联合利华"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("todo_custom_field_missing", report.blocked_reasons)

    def test_preflight_blocks_unresolved_todo_owner(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["owner"],
            payload={"owner": ""},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("owner_unresolved", report.blocked_reasons)

    def test_preflight_blocks_owner_not_in_live_tasklist_members(self) -> None:
        runner = SchemaPreflightRunner(FakeSchemaBackend())
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["owner"],
            payload={"owner": "ou_not_in_tasklist"},
        )
        report = runner.run(candidate)
        self.assertEqual(report.status, "blocked")
        self.assertIn("owner_unresolved", report.blocked_reasons)

    def test_resource_resolver_marks_unconfirmed_live_resources(self) -> None:
        responses = {
            "base +table-list --base-token app_example_base_token --limit 1": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"ok":true,"data":{"tables":[{"id":"tbl_customer_master_example","name":"客户主数据"}]}}',
                stderr="",
            ),
            "task tasklists list": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"items":[{"guid":"00000000-0000-4000-8000-000000000001"}]}}'
                ),
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_customer_archive_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=(
                    '{"ok":false,"error":{"type":"permission","message":"insufficient '
                    'permissions","hint":"need scope"}}'
                ),
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_meeting_notes_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=(
                    '{"ok":false,"error":{"type":"permission","message":"insufficient '
                    'permissions","hint":"need scope"}}'
                ),
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        probe = LarkCliResourceProbe(client, LiveWorkbenchConfig.from_sources(sources))
        resolution = ResourceResolver(probe=probe).resolve(sources)
        self.assertEqual(resolution.status, "partial")
        self.assertEqual(
            sorted(resolution.unconfirmed_keys),
            ["customer_archive_folder", "meeting_notes_folder"],
        )
        self.assertTrue(
            next(hint for hint in resolution.hints_used if hint.key == "base_token").confirmed_live
        )
        self.assertTrue(
            next(
                hint for hint in resolution.hints_used if hint.key == "todo_tasklist_guid"
            ).confirmed_live
        )

    def test_lark_cli_client_raises_structured_error(self) -> None:
        responses = {
            "docs +search --query 客户主数据": subprocess.CompletedProcess(
                args=[],
                returncode=3,
                stdout=(
                    '{"ok":false,"error":{"type":"missing_scope","message":"missing '
                    'required scope","hint":"auth login"}}'
                ),
                stderr="",
            )
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        with self.assertRaises(LarkCliCommandError) as ctx:
            client.invoke_json(["docs", "+search", "--query", "客户主数据"])
        self.assertEqual(ctx.exception.error_type, "missing_scope")
        self.assertIn("auth login", ctx.exception.hint)

    def test_live_schema_backend_maps_semantic_slots(self) -> None:
        responses = {
            "base +field-list --base-token app_live --table-id 行动计划 --limit 200": (
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=(
                        '{"code":0,"data":{"items":['
                        '{"field_id":"fld_subject","field_name":"具体行动","type":"text"},'
                        '{"field_id":"fld_action_type","field_name":"行动类型_单选","type":"single_select"},'
                        '{"field_id":"fld_status","field_name":"完成状态_单选","type":"single_select"}'
                        ']}}'
                    ),
                    stderr="",
                )
            ),
            "base +field-search-options --base-token app_live --table-id 行动计划 --field-id fld_action_type --limit 100": (
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout='{"ok":true,"data":{"options":[{"name":"客户经营"},{"name":"续费沟通"}]}}',
                    stderr="",
                )
            ),
            "base +field-search-options --base-token app_live --table-id 行动计划 --field-id fld_status --limit 100": (
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout='{"ok":true,"data":{"options":[{"name":"未开始"},{"name":"进行中"}]}}',
                    stderr="",
                )
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        backend = LarkCliSchemaBackend(
            client,
            LiveWorkbenchConfig(base_token="app_live"),
        )
        schema = backend.get_table_schema("行动计划")
        self.assertEqual(schema["subject"]["name"], "具体行动")
        self.assertEqual(schema["action_type"]["type"], "single_select")
        self.assertIn("客户经营", schema["action_type"]["options"])

    def test_live_schema_backend_builds_todo_schema_from_tasklist(self) -> None:
        responses = {
            (
                'task tasklists get --params '
                '{"tasklist_guid": "00000000-0000-4000-8000-000000000001"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"tasklist":{'
                    '"guid":"00000000-0000-4000-8000-000000000001",'
                    '"owner":{"id":"ou_owner","role":"owner","type":"user"},'
                    '"members":[{"id":"ou_editor","role":"editor","type":"user"}]'
                    '}}}'
                ),
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        backend = LarkCliSchemaBackend(client, config)
        schema = backend.get_table_schema("待办")
        self.assertEqual(schema["customer"]["field_id"], "a7009aff-7d85-4378-82c9-1584873f469d")
        self.assertEqual(schema["priority"]["options"], [])
        self.assertEqual(
            schema["owner"]["valid_member_ids"],
            ["ou_owner", "ou_editor"],
        )

    def test_capability_report_surfaces_base_and_docs_gaps(self) -> None:
        responses = {
            "base +table-list --base-token app_example_base_token --limit 200": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"tables":['
                    '{"id":"tbl_customer_master_example","name":"客户主数据"},'
                    '{"id":"tbla91dGjJsb0axd","name":"客户联系记录"},'
                    '{"id":"tblqbbS46bWilKd7","name":"行动计划"}'
                    ']}}'
                ),
                stderr="",
            ),
            "task tasklists list": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"items":[{"guid":"00000000-0000-4000-8000-000000000001"}]}}'
                ),
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_customer_archive_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout='{"ok":false,"error":{"type":"permission","message":"insufficient permissions"}}',
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_meeting_notes_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout='{"ok":false,"error":{"type":"permission","message":"insufficient permissions"}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        self.assertEqual(config.base_token, "app_example_base_token")
        self.assertEqual(config.customer_master_table, "tbl_customer_master_example")
        reporter = LiveCapabilityReporter(
            client,
            config,
            LarkCliResourceProbe(client, config),
        )
        report = reporter.build(sources)
        checks = {item.name: item for item in report.checks}
        self.assertEqual(checks["base_access"].status, "available")
        self.assertTrue(checks["base_access"].details["required_tables_verified"])
        self.assertEqual(
            checks["base_access"].details["required_tables"],
            {
                "客户主数据": "tbl_customer_master_example",
                "行动计划": "行动计划",
                "客户联系记录": "客户联系记录",
            },
        )
        self.assertIn("合同清单", checks["base_access"].details["table_targets"])
        self.assertEqual(checks["docs_access"].status, "degraded")
        self.assertEqual(checks["task_access"].status, "available")

    def test_capability_report_supports_current_lark_cli_base_table_shape(self) -> None:
        responses = {
            "base +table-list --base-token app_example_base_token --limit 200": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"tables":['
                    '{"id":"tbl_customer_master_example","name":"客户主数据"},'
                    '{"id":"tbla91dGjJsb0axd","name":"客户联系记录"},'
                    '{"id":"tblqbbS46bWilKd7","name":"行动计划"}'
                    ']}}'
                ),
                stderr="",
            ),
            "task tasklists list": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"items":[{"guid":"00000000-0000-4000-8000-000000000001"}]}}'
                ),
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_customer_archive_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"files":[]}}',
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_meeting_notes_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"files":[]}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        reporter = LiveCapabilityReporter(
            client,
            config,
            LarkCliResourceProbe(client, config),
        )
        report = reporter.build(sources)
        checks = {item.name: item for item in report.checks}
        self.assertEqual(checks["base_access"].status, "available")
        self.assertTrue(checks["base_access"].details["required_tables_verified"])

    def test_capability_report_accepts_legacy_table_list_response_shape(self) -> None:
        responses = {
            "base +table-list --base-token app_example_base_token --limit 200": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"items":['
                    '{"table_id":"tbl_customer_master_example","table_name":"客户主数据"},'
                    '{"table_id":"tbla91dGjJsb0axd","table_name":"客户联系记录"},'
                    '{"table_id":"tblqbbS46bWilKd7","table_name":"行动计划"}'
                    ']}}'
                ),
                stderr="",
            ),
            "task tasklists list": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"items":[{"guid":"00000000-0000-4000-8000-000000000001"}]}}'
                ),
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_customer_archive_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"files":[]}}',
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_meeting_notes_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"files":[]}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        reporter = LiveCapabilityReporter(
            client,
            config,
            LarkCliResourceProbe(client, config),
        )
        report = reporter.build(sources)
        checks = {item.name: item for item in report.checks}
        self.assertEqual(checks["base_access"].status, "available")
        self.assertTrue(checks["base_access"].details["required_tables_verified"])

    def test_todo_writer_blocks_before_live_create_when_preflight_fails(self) -> None:
        class RaisingRunner:
            def __call__(self, command, capture_output, text, check):
                raise AssertionError("task create should not be invoked when preflight is blocked")

        client = LarkCliClient(runner=RaisingRunner())
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(FakeSchemaBackend()),
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "priority", "customer"],
            payload={
                "summary": "跟进联合利华续费",
                "owner": "ou_owner",
                "priority": "高",
                "customer": "联合利华",
            },
        )
        result = writer.create(candidate)
        self.assertFalse(result.attempted)
        self.assertFalse(result.allowed)
        self.assertIn("todo_custom_field_missing", result.preflight_report.blocked_reasons)

    def test_todo_writer_creates_task_after_preflight_passes(self) -> None:
        responses = {
            (
                'task tasks create --data '
                '{"summary": "跟进联合利华续费", "tasklists": [{"tasklist_guid": "00000000-0000-4000-8000-000000000001"}], '
                '"members": [{"id": "ou_owner", "role": "assignee", "type": "user"}], '
                '"description": "带客户档案链接", '
                '"due": {"timestamp": "1776124800000", "is_all_day": true}, '
                '"custom_fields": [{"guid": "a7009aff-7d85-4378-82c9-1584873f469d", "text_value": "联合利华"}]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"task":{"guid":"task_guid_1",'
                    '"url":"https://applink.feishu.cn/client/todo/detail?guid=task_guid_1"}}}'
                ),
                stderr="",
            )
        }
        client = LarkCliClient(runner=FakeRunner(responses))

        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "description": {
                        "field_id": "description",
                        "name": "描述",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "due_at": {
                        "field_id": "due",
                        "name": "截止时间",
                        "type": "datetime",
                        "allowed_live_types": ["datetime"],
                        "write_policy": "safe_update",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "a7009aff-7d85-4378-82c9-1584873f469d",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "priority": {
                        "field_id": "f7587037-8ad1-443c-b350-f6600e0ccadd",
                        "name": "优先级",
                        "type": "single_select",
                        "options": ["高", "中", "低"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    },
                }

        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "owner", "customer", "priority"],
            payload={
                "summary": "跟进联合利华续费",
                "owner": "ou_owner",
                "customer": "联合利华",
                "priority": "高",
                "description": "带客户档案链接",
                "due_at": "2026-04-14",
            },
        )
        result = writer.create(candidate)
        self.assertTrue(result.attempted)
        self.assertTrue(result.allowed)
        self.assertEqual(result.task_guid, "task_guid_1")

    def test_todo_writer_updates_task_via_patch_and_owner_sync(self) -> None:
        responses = {
            (
                'task tasks get --params {"task_guid": "task_guid_1"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"task":{"guid":"task_guid_1","url":"https://applink.feishu.cn/client/todo/detail?guid=task_guid_1",'
                    '"members":[{"id":"ou_old","role":"assignee","type":"user"}]}}}'
                ),
                stderr="",
            ),
            (
                'task tasks patch --params {"task_guid": "task_guid_1"} --data '
                '{"task": {"summary": "更新后的标题", "description": "更新后的描述", '
                '"due": {"timestamp": "1776124800000", "is_all_day": true}, '
                '"custom_fields": [{"guid": "a7009aff-7d85-4378-82c9-1584873f469d", "text_value": "联合利华"}]}, '
                '"update_fields": ["summary", "description", "due", "custom_fields"]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"task":{"guid":"task_guid_1","url":"https://applink.feishu.cn/client/todo/detail?guid=task_guid_1"}}}',
                stderr="",
            ),
            (
                'task members remove --params {"task_guid": "task_guid_1"} --data '
                '{"members": [{"id": "ou_old", "role": "assignee", "type": "user"}]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"msg":"success"}',
                stderr="",
            ),
            (
                'task members add --params {"task_guid": "task_guid_1"} --data '
                '{"members": [{"id": "ou_new", "role": "assignee", "type": "user"}]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"msg":"success"}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))

        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "description": {
                        "field_id": "description",
                        "name": "描述",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "due_at": {
                        "field_id": "due",
                        "name": "截止时间",
                        "type": "datetime",
                        "allowed_live_types": ["datetime"],
                        "write_policy": "safe_update",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_old", "ou_new"],
                    },
                    "customer": {
                        "field_id": "a7009aff-7d85-4378-82c9-1584873f469d",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "priority": {
                        "field_id": "f7587037-8ad1-443c-b350-f6600e0ccadd",
                        "name": "优先级",
                        "type": "single_select",
                        "options": ["高", "中", "低"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    },
                }

        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
        )
        candidate = WriteCandidate(
            object_name="待办",
            layer="reminder",
            semantic_fields=["summary", "description", "due_at", "customer", "priority", "owner"],
            payload={
                "summary": "更新后的标题",
                "description": "更新后的描述",
                "due_at": "2026-04-14",
                "customer": "联合利华",
                "priority": "中",
                "owner": "ou_new",
            },
        )
        result = writer.update("task_guid_1", candidate)
        self.assertTrue(result.attempted)
        self.assertTrue(result.allowed)
        self.assertEqual(result.task_guid, "task_guid_1")
        self.assertIn("patch", result.request_payload)
        self.assertIn("member_add", result.request_payload)
        self.assertIn("member_remove", result.request_payload)

    def test_todo_writer_updates_existing_task_when_duplicate_detected(self) -> None:
        responses = {
            (
                'task tasks get --params {"task_guid": "task_existing"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"code":0,"data":{"task":{"guid":"task_existing","url":"https://applink.feishu.cn/client/todo/detail?guid=task_existing",'
                    '"members":[{"id":"ou_old","role":"assignee","type":"user"}]}}}'
                ),
                stderr="",
            ),
            (
                'task tasks patch --params {"task_guid": "task_existing"} --data '
                '{"task": {"summary": "跟进联合利华 AI 埋点产品介绍给触脉确认", "description": "补充新的会后上下文", '
                '"due": {"timestamp": "1776124800000", "is_all_day": true}, '
                '"custom_fields": [{"guid": "a7009aff-7d85-4378-82c9-1584873f469d", "text_value": "联合利华（UFS）"}]}, '
                '"update_fields": ["summary", "description", "due", "custom_fields"]}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"task":{"guid":"task_existing","url":"https://applink.feishu.cn/client/todo/detail?guid=task_existing"}}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))

        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "description": {
                        "field_id": "description",
                        "name": "描述",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "due_at": {
                        "field_id": "due",
                        "name": "截止时间",
                        "type": "datetime",
                        "allowed_live_types": ["datetime"],
                        "write_policy": "safe_update",
                    },
                    "customer": {
                        "field_id": "a7009aff-7d85-4378-82c9-1584873f469d",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "priority": {
                        "field_id": "f7587037-8ad1-443c-b350-f6600e0ccadd",
                        "name": "优先级",
                        "type": "single_select",
                        "options": ["高", "中", "低"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    },
                }

        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "guid": "task_existing",
                    "summary": "联合利华-AI埋点产品介绍给触脉（王奇）",
                    "customer": "联合利华（UFS）",
                    "due_at": "2026-04-14",
                }
            ],
        )
        candidate = WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "description", "due_at", "customer", "priority"],
            payload={
                "summary": "跟进联合利华 AI 埋点产品介绍给触脉确认",
                "description": "补充新的会后上下文",
                "due_at": "2026-04-14",
                "customer": "联合利华（UFS）",
                "priority": "高",
            },
            match_basis={"customer": "联合利华（UFS）", "time_window": "2026-04"},
        )
        result = writer.create(candidate)
        self.assertTrue(result.attempted)
        self.assertTrue(result.allowed)
        self.assertEqual(result.executed_operation, "update")
        self.assertEqual(result.dedupe_decision, "update_existing")
        self.assertEqual(result.remote_object_id, "task_existing")
        self.assertIn("patch", result.request_payload)
        self.assertNotIn("member_add", result.request_payload)
        self.assertNotIn("member_remove", result.request_payload)

    def test_todo_writer_ignores_duplicate_without_guid(self) -> None:
        class FakeClient:
            def invoke_json(self, argv: list[str]) -> dict[str, object]:
                if argv[:3] == ["task", "tasks", "create"]:
                    return {
                        "code": 0,
                        "data": {
                            "task": {
                                "guid": "task_new",
                                "url": "https://applink.feishu.cn/client/todo/detail?guid=task_new",
                            }
                        },
                    }
                raise AssertionError(f"unexpected command: {' '.join(argv)}")

        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "a7009aff-7d85-4378-82c9-1584873f469d",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                    "priority": {
                        "field_id": "f7587037-8ad1-443c-b350-f6600e0ccadd",
                        "name": "优先级",
                        "type": "single_select",
                        "options": ["高", "中", "低"],
                        "allowed_live_types": ["single_select"],
                        "write_policy": "safe_update",
                    },
                }

        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=FakeClient(),
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "summary": "跟进联合利华 Campaign 优化方案确认",
                    "customer": "联合利华",
                    "due_at": "2026-04-10",
                }
            ],
        )

        candidate = WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "owner", "customer", "priority"],
            payload={
                "summary": "跟进联合利华 Campaign 优化方案确认",
                "owner": "ou_owner",
                "customer": "联合利华",
                "priority": "高",
            },
            match_basis={"customer": "联合利华", "time_window": "2026-04"},
        )

        result = writer.create(candidate)
        self.assertTrue(result.attempted)
        self.assertEqual(result.executed_operation, "create")
        self.assertEqual(result.dedupe_decision, "create_new")
        self.assertEqual(result.remote_object_id, "task_new")

    def test_todo_writer_requires_time_window_for_duplicate_matching(self) -> None:
        class FakeClient:
            def invoke_json(self, argv: list[str]) -> dict[str, object]:
                if argv[:3] == ["task", "tasks", "create"]:
                    return {
                        "code": 0,
                        "data": {
                            "task": {
                                "guid": "task_new_no_window",
                                "url": "https://applink.feishu.cn/client/todo/detail?guid=task_new_no_window",
                            }
                        },
                    }
                raise AssertionError(f"unexpected command: {' '.join(argv)}")

        class PassingTodoSchemaBackend:
            def get_table_schema(self, object_name: str) -> dict[str, dict[str, object]] | None:
                if object_name != "待办":
                    return None
                return {
                    "summary": {
                        "field_id": "summary",
                        "name": "标题",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "required_create",
                    },
                    "owner": {
                        "field_id": "members.assignee",
                        "name": "负责人",
                        "type": "user",
                        "allowed_live_types": ["user"],
                        "write_policy": "required_create",
                        "valid_member_ids": ["ou_owner"],
                    },
                    "customer": {
                        "field_id": "a7009aff-7d85-4378-82c9-1584873f469d",
                        "name": "客户",
                        "type": "text",
                        "allowed_live_types": ["text"],
                        "write_policy": "safe_update",
                    },
                }

        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        writer = TodoWriter(
            client=FakeClient(),
            config=config,
            schema_preflight=SchemaPreflightRunner(PassingTodoSchemaBackend()),
            existing_tasks=[
                {
                    "guid": "task_existing",
                    "summary": "跟进联合利华 Campaign 优化方案确认",
                    "customer": "联合利华",
                    "due_at": "2026-04-10",
                }
            ],
        )

        candidate = WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "owner", "customer"],
            payload={
                "summary": "跟进联合利华 Campaign 优化方案确认",
                "owner": "ou_owner",
                "customer": "联合利华",
            },
            match_basis={"customer": "联合利华"},
        )

        result = writer.create(candidate)
        self.assertTrue(result.attempted)
        self.assertEqual(result.executed_operation, "create")
        self.assertEqual(result.dedupe_decision, "create_new")
        self.assertEqual(result.remote_object_id, "task_new_no_window")

    def test_capability_report_degrades_when_required_table_missing(self) -> None:
        responses = {
            "base +table-list --base-token app_example_base_token --limit 200": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"tables":['
                    '{"id":"tbl_customer_master_example","name":"客户主数据"},'
                    '{"id":"tbla91dGjJsb0axd","name":"客户联系记录"}'
                    ']}}'
                ),
                stderr="",
            ),
            "task tasklists list": subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"items":[{"guid":"00000000-0000-4000-8000-000000000001"}]}}',
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_customer_archive_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"files":[]}}',
                stderr="",
            ),
            (
                'drive files list --params '
                '{"folder_token":"fld_meeting_notes_example"}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"code":0,"data":{"files":[]}}',
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        reporter = LiveCapabilityReporter(
            client,
            config,
            LarkCliResourceProbe(client, config),
        )
        report = reporter.build(sources)
        checks = {item.name: item for item in report.checks}
        self.assertEqual(checks["base_access"].status, "degraded")
        self.assertIn("required_tables_missing", checks["base_access"].reasons)

    def test_customer_backend_supports_matrix_record_list_shape(self) -> None:
        responses = {
            (
                "base +field-list --base-token app_example_base_token "
                "--table-id tbl_customer_master_example --limit 200"
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"items":['
                    '{"field_name":"客户 ID"},'
                    '{"field_name":"简称"},'
                    '{"field_name":"公司名称"}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                'base +data-query --base-token app_example_base_token --dsl '
                '{"datasource": {"type": "table", "table": {"tableId": "tbl_customer_master_example"}}, '
                '"dimensions": [{"field_name": "客户 ID", "alias": "dim_customer_id_alt"}, '
                '{"field_name": "简称", "alias": "dim_short_name"}, '
                '{"field_name": "公司名称", "alias": "dim_company_name"}], '
                '"filters": {"type": 1, "conjunction": "or", "conditions": ['
                '{"field_name": "简称", "operator": "is", "value": ["联合利华"]}, '
                '{"field_name": "简称", "operator": "contains", "value": ["联合利华"]}, '
                '{"field_name": "公司名称", "operator": "is", "value": ["联合利华"]}, '
                '{"field_name": "公司名称", "operator": "contains", "value": ["联合利华"]}, '
                '{"field_name": "客户 ID", "operator": "is", "value": ["联合利华"]}]}, '
                '"pagination": {"limit": 20}, "shaper": {"format": "flat"}}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"ok":true,"data":{"main_data":[]}}',
                stderr="",
            ),
            (
                "base +record-list --base-token app_example_base_token "
                "--table-id tbl_customer_master_example --limit 200"
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"fields":["客户 ID","简称","公司名称"],"data":['
                    '["C_002","联合利华（UFS）","联合利华服务（合肥）有限公司上海分公司"]'
                    ']}}'
                ),
                stderr="",
            )
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        from runtime import LarkCliCustomerBackend  # noqa: E402

        backend = LarkCliCustomerBackend(client, config)
        rows = backend.search_customer_master("联合利华")
        self.assertEqual(rows[0]["客户ID"], "C_002")
        self.assertEqual(rows[0]["简称"], "联合利华（UFS）")

    def test_customer_backend_prefers_data_query_for_precise_lookup(self) -> None:
        responses = {
            (
                "base +field-list --base-token app_example_base_token "
                "--table-id tbl_customer_master_example --limit 200"
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"items":['
                    '{"field_name":"客户ID"},'
                    '{"field_name":"简称"},'
                    '{"field_name":"客户名称"},'
                    '{"field_name":"公司名称"},'
                    '{"field_name":"客户档案"}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                'base +data-query --base-token app_example_base_token --dsl '
                '{"datasource": {"type": "table", "table": {"tableId": "tbl_customer_master_example"}}, '
                '"dimensions": [{"field_name": "客户ID", "alias": "dim_customer_id"}, '
                '{"field_name": "简称", "alias": "dim_short_name"}, '
                '{"field_name": "客户名称", "alias": "dim_customer_name"}, '
                '{"field_name": "公司名称", "alias": "dim_company_name"}, '
                '{"field_name": "客户档案", "alias": "dim_archive_link"}], '
                '"filters": {"type": 1, "conjunction": "or", "conditions": ['
                '{"field_name": "简称", "operator": "is", "value": ["联合利华"]}, '
                '{"field_name": "简称", "operator": "contains", "value": ["联合利华"]}, '
                '{"field_name": "客户名称", "operator": "is", "value": ["联合利华"]}, '
                '{"field_name": "客户名称", "operator": "contains", "value": ["联合利华"]}, '
                '{"field_name": "公司名称", "operator": "is", "value": ["联合利华"]}, '
                '{"field_name": "公司名称", "operator": "contains", "value": ["联合利华"]}, '
                '{"field_name": "客户ID", "operator": "is", "value": ["联合利华"]}]}, '
                '"pagination": {"limit": 20}, "shaper": {"format": "flat"}}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"main_data":['
                    '{"dim_customer_id":{"value":"C_002"},'
                    '"dim_short_name":{"value":"联合利华（UFS）"},'
                    '"dim_customer_name":{"value":"联合利华中国"},'
                    '"dim_company_name":{"value":"联合利华服务公司"},'
                    '"dim_archive_link":{"value":"https://doc.example/u"}}'
                    ']}}'
                ),
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        backend = LarkCliCustomerBackend(client, config)
        rows = backend.search_customer_master("联合利华")
        self.assertEqual(rows[0]["客户ID"], "C_002")
        self.assertEqual(rows[0]["简称"], "联合利华（UFS）")
        self.assertEqual(rows[0]["客户档案"], "https://doc.example/u")

    def test_base_query_backend_prefers_data_query_for_customer_id_reads(self) -> None:
        responses = {
            (
                "base +field-list --base-token app_example_base_token "
                "--table-id 客户联系记录 --limit 200"
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"items":['
                    '{"field_name":"客户ID"},'
                    '{"field_name":"记录标题"},'
                    '{"field_name":"联系日期"}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                'base +data-query --base-token app_example_base_token --dsl '
                '{"datasource": {"type": "table", "table": {"tableId": "客户联系记录"}}, '
                '"dimensions": [{"field_name": "客户ID", "alias": "dim_field_0"}, '
                '{"field_name": "联系日期", "alias": "dim_field_1"}, '
                '{"field_name": "记录标题", "alias": "dim_field_2"}], '
                '"filters": {"type": 1, "conjunction": "or", "conditions": ['
                '{"field_name": "客户ID", "operator": "is", "value": ["C_002"]}]}, '
                '"pagination": {"limit": 5}, "shaper": {"format": "flat"}}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"main_data":['
                    '{"dim_field_0":{"value":"C_002"},'
                    '"dim_field_1":{"value":"2026-04-11"},'
                    '"dim_field_2":{"value":"联合利华｜续费沟通"}}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                "base +field-list --base-token app_example_base_token "
                "--table-id 行动计划 --limit 200"
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"items":['
                    '{"field_name":"客户ID"},'
                    '{"field_name":"具体行动"},'
                    '{"field_name":"计划完成时间"}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                'base +data-query --base-token app_example_base_token --dsl '
                '{"datasource": {"type": "table", "table": {"tableId": "行动计划"}}, '
                '"dimensions": [{"field_name": "具体行动", "alias": "dim_field_0"}, '
                '{"field_name": "客户ID", "alias": "dim_field_1"}, '
                '{"field_name": "计划完成时间", "alias": "dim_field_2"}], '
                '"filters": {"type": 1, "conjunction": "or", "conditions": ['
                '{"field_name": "客户ID", "operator": "is", "value": ["C_002"]}]}, '
                '"pagination": {"limit": 5}, "shaper": {"format": "flat"}}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"main_data":['
                    '{"dim_field_0":{"value":"推进续费方案"},'
                    '"dim_field_1":{"value":"C_002"},'
                    '"dim_field_2":{"value":"2026-04-20"}}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                "base +field-list --base-token app_example_base_token "
                "--table-id 合同清单 --limit 200"
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"items":['
                    '{"field_name":"客户ID"},'
                    '{"field_name":"合同编码"},'
                    '{"field_name":"合同状态"},'
                    '{"field_name":"合同到期日期"}'
                    ']}}'
                ),
                stderr="",
            ),
            (
                'base +data-query --base-token app_example_base_token --dsl '
                '{"datasource": {"type": "table", "table": {"tableId": "合同清单"}}, '
                '"dimensions": [{"field_name": "合同到期日期", "alias": "dim_field_0"}, '
                '{"field_name": "合同状态", "alias": "dim_field_1"}, '
                '{"field_name": "合同编码", "alias": "dim_field_2"}, '
                '{"field_name": "客户ID", "alias": "dim_field_3"}], '
                '"filters": {"type": 1, "conjunction": "or", "conditions": ['
                '{"field_name": "客户ID", "operator": "is", "value": ["C_002"]}]}, '
                '"pagination": {"limit": 5}, "shaper": {"format": "flat"}}'
            ): subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=(
                    '{"ok":true,"data":{"main_data":['
                    '{"dim_field_0":{"value":"2026-06-30"},'
                    '"dim_field_1":{"value":"执行中"},'
                    '"dim_field_2":{"value":"HT-001"},'
                    '"dim_field_3":{"value":"C_002"}}'
                    ']}}'
                ),
                stderr="",
            ),
        }
        client = LarkCliClient(runner=FakeRunner(responses))
        sources = RuntimeSourceLoader(REPO_ROOT).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        backend = LarkCliBaseQueryBackend(client, config)
        contact_rows = backend.query_rows_by_customer_id("客户联系记录", "C_002", limit=5)
        action_rows = backend.query_rows_by_customer_id("行动计划", "C_002", limit=5)
        contract_rows = backend.query_rows_by_customer_id("合同清单", "C_002", limit=5)
        self.assertEqual(contact_rows[0]["记录标题"], "联合利华｜续费沟通")
        self.assertEqual(action_rows[0]["具体行动"], "推进续费方案")
        self.assertEqual(contract_rows[0]["合同编码"], "HT-001")
        self.assertEqual(contract_rows[0]["合同状态"], "执行中")

    def test_render_live_diagnostic_includes_next_actions(self) -> None:
        report = {
            "resource_resolution": {
                "status": "partial",
                "missing_keys": [],
                "unconfirmed_keys": ["meeting_notes_folder"],
                "hints": [],
            },
            "capability_report": [
                {
                    "name": "base_access",
                    "status": "blocked",
                    "reasons": ["missing_base_token"],
                    "details": {"env_var": "FEISHU_AM_BASE_TOKEN"},
                },
                {
                    "name": "docs_access",
                    "status": "degraded",
                    "reasons": ["permission"],
                    "details": {"outcomes": [{"status": "degraded", "reason": "permission"}]},
                },
            ],
            "customer_resolution": None,
        }
        rendered = render_live_diagnostic(report)
        self.assertIn("conclusion: blocked", rendered)
        self.assertIn("reason: some configured resources are not yet confirmed live: meeting_notes_folder", rendered)
        self.assertIn("resource status: partial", rendered)
        self.assertIn("next action: export FEISHU_AM_BASE_TOKEN", rendered)
        self.assertIn("next action: run lark-cli auth login", rendered)

    def test_capability_report_uses_blocked_for_missing_required_inputs(self) -> None:
        env_backup = {key: os.environ.get(key) for key in RuntimeSourceLoader.ENV_VARS.values()}
        try:
            for key in RuntimeSourceLoader.ENV_VARS.values():
                os.environ.pop(key, None)

            client = LarkCliClient(runner=FakeRunner({}))
            sources = RuntimeSourceLoader(Path("/tmp/empty-runtime-sources")).load()
            config = LiveWorkbenchConfig.from_sources(sources)
            reporter = LiveCapabilityReporter(client, config, LarkCliResourceProbe(client, config))

            report = reporter.build(sources)
            checks = {item.name: item for item in report.checks}

            self.assertEqual(checks["base_access"].status, "blocked")
            self.assertEqual(checks["docs_access"].status, "blocked")
            self.assertEqual(checks["task_access"].status, "blocked")
        finally:
            for key, value in env_backup.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_suggest_next_actions_for_available_task_access(self) -> None:
        actions = suggest_next_actions(
            type(
                "Check",
                (),
                {"name": "task_access", "status": "available", "reasons": [], "details": {}},
            )()
        )
        self.assertEqual(actions, ["task adapter is usable; keep this as the known-good baseline"])

    def test_scene_result_structured_result_preserves_standard_fields(self) -> None:
        result = SceneResult(
            scene_name="post-meeting-synthesis",
            resource_status="resolved",
            customer_status="resolved",
            context_status="completed",
            used_sources=["客户主数据"],
            facts=["客户已完成阶段复盘"],
            judgments=["当前更适合继续跟进"],
            open_questions=["负责人是否仍为销售总监"],
            recommendations=["确认联合利华后续动作"],
            fallback_category="none",
            fallback_reason=None,
            fallback_message=None,
            write_ceiling="normal",
            output_text="artifact output",
            payload={"candidate_count": 1, "write_result_details": []},
        )

        structured = result.structured_result()

        self.assertEqual(structured["scene_name"], "post-meeting-synthesis")
        self.assertEqual(structured["facts"], ["客户已完成阶段复盘"])
        self.assertEqual(structured["judgments"], ["当前更适合继续跟进"])
        self.assertEqual(structured["candidate_count"], 1)
        structured["facts"].append("changed")
        self.assertEqual(result.facts, ["客户已完成阶段复盘"])

    def test_scene_result_structured_result_does_not_allow_payload_to_override_standard_fields(self) -> None:
        result = SceneResult(
            scene_name="post-meeting-synthesis",
            resource_status="resolved",
            customer_status="resolved",
            context_status="completed",
            write_ceiling="normal",
            payload={
                "scene_name": "archive-refresh",
                "resource_status": "blocked",
                "scene_payload": {"topic_text": "weekly review"},
            },
        )

        structured = result.structured_result()

        self.assertEqual(structured["scene_name"], "post-meeting-synthesis")
        self.assertEqual(structured["resource_status"], "resolved")
        self.assertEqual(
            structured["scene_payload"]["reserved_payload_fields"],
            {"scene_name": "archive-refresh", "resource_status": "blocked"},
        )

    def test_normalize_scene_path_expands_user_and_repo_relative_paths(self) -> None:
        repo_root = Path("/tmp/repo-root")

        with patch.object(scene_runtime.Path, "expanduser", return_value=Path("/Users/tester/demo.txt")):
            expanded = scene_runtime._normalize_scene_path("~/demo.txt", repo_root)

        relative = scene_runtime._normalize_scene_path("fixtures/demo.txt", repo_root)

        self.assertEqual(expanded, Path("/Users/tester/demo.txt"))
        self.assertEqual(relative, repo_root / "fixtures/demo.txt")

    def test_dispatch_scene_rejects_unknown_scene_name(self) -> None:
        request = SceneRequest(
            scene_name="unknown-scene",
            repo_root=REPO_ROOT,
            customer_query="联合利华",
        )

        with self.assertRaises(UnknownSceneError):
            dispatch_scene(request)

    def test_default_scene_registry_exposes_first_wave_scene_names(self) -> None:
        registry = build_default_scene_registry()

        self.assertEqual(
            registry.available_scenes(),
            [
                "archive-refresh",
                "customer-recent-status",
                "post-meeting-synthesis",
                "todo-capture-and-update",
            ],
        )

    def test_post_meeting_scene_result_uses_existing_gateway_bridge_surfaces(self) -> None:
        gateway_result = type(
            "FakeGatewayResult",
            (),
            {
                "resource_resolution": type("ResourceResolution", (), {"status": "resolved"})(),
                "customer_resolution": type("CustomerResolution", (), {"status": "resolved"})(),
            },
        )()
        recovery = type(
            "FakeRecovery",
            (),
            {
                "status": "completed",
                "write_ceiling": "normal",
                "used_sources": ["客户主数据", "客户联系记录"],
                "key_context": ["客户近期处于阶段复盘窗口"],
                "open_questions": ["下次跟进负责人是否变化"],
                "candidate_conflicts": [],
                "fallback_reason": None,
            },
        )()
        candidate = WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "customer"],
            payload={"summary": "确认联合利华后续动作", "customer": "联合利华"},
            match_basis={"customer": "联合利华"},
            source_context={"scenario": "post_meeting"},
        )

        with patch.object(scene_runtime.FeishuWorkbenchGateway, "for_live_lark_cli") as gateway_factory, patch.object(
            scene_runtime, "RuntimeSourceLoader"
        ) as source_loader_cls, patch.object(scene_runtime.LiveWorkbenchConfig, "from_sources", return_value=object()), patch.object(
            scene_runtime, "LarkCliBaseQueryBackend", return_value=object()
        ), patch.object(scene_runtime, "recover_live_context", return_value=recovery), patch.object(
            scene_runtime, "build_meeting_todo_candidates", return_value=[candidate]
        ), patch.object(
            scene_runtime,
            "build_meeting_output_artifact",
            return_value={"output_text": "artifact output", "write_result_details": []},
        ):
            gateway_factory.return_value.run.return_value = gateway_result
            source_loader_cls.return_value.load.return_value = object()
            result = scene_runtime.run_post_meeting_scene(
                SceneRequest(
                    scene_name="post-meeting-synthesis",
                    repo_root=REPO_ROOT,
                    customer_query="联合利华",
                    inputs={
                        "eval_name": "unilever-stage-review",
                        "transcript_file": str(
                            REPO_ROOT / "tests" / "fixtures" / "transcripts" / "20260410-联合利华 Campaign活动分析优化-阶段汇报.txt"
                        ),
                        "action_items": [],
                    },
                    options={"confirm_write": False},
                )
            )

        payload = result.structured_result()
        self.assertEqual(payload["scene_name"], "post-meeting-synthesis")
        self.assertEqual(payload["used_sources"], ["客户主数据", "客户联系记录"])
        self.assertEqual(payload["recommendations"], ["确认联合利华后续动作"])
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["context_status"], "completed")

    def test_customer_recent_status_scene_returns_structured_sections(self) -> None:
        gateway_result = type(
            "FakeGatewayResult",
            (),
            {
                "resource_resolution": type("ResourceResolution", (), {"status": "resolved"})(),
                "customer_resolution": type(
                    "CustomerResolution",
                    (),
                    {
                        "status": "resolved",
                        "candidates": [
                            type("Customer", (), {"short_name": "联合利华", "customer_id": "C_002"})()
                        ],
                    },
                )(),
            },
        )()
        recovery = type(
            "FakeRecovery",
            (),
            {
                "status": "partial",
                "write_ceiling": "recommendation-only",
                "used_sources": ["客户主数据", "客户联系记录"],
                "key_context": ["客户主数据快照: 联合利华｜客户ID C_002"],
                "open_questions": ["缺少当前行动计划"],
                "candidate_conflicts": ["客户档案候选缺少显式客户证据"],
                "missing_sources": ["行动计划"],
                "fallback_reason": "some targeted live reads are still missing",
            },
        )()

        with patch.object(scene_runtime, "_build_live_scene_context", return_value=(gateway_result, recovery)):
            result = scene_runtime.run_customer_recent_status_scene(
                SceneRequest(
                    scene_name="customer-recent-status",
                    repo_root=REPO_ROOT,
                    customer_query="联合利华",
                    inputs={"topic_text": "最近经营状态"},
                )
            )

        payload = result.structured_result()
        self.assertEqual(payload["scene_name"], "customer-recent-status")
        self.assertEqual(payload["facts"], ["客户主数据快照: 联合利华｜客户ID C_002"])
        self.assertTrue(any("recommendation-first" in item for item in payload["judgments"]))
        self.assertTrue(any("行动计划" in item for item in payload["recommendations"]))
        self.assertEqual(payload["fallback_category"], "context")

    def test_customer_recent_status_scene_classifies_permission_fallback(self) -> None:
        gateway_result = type(
            "FakeGatewayResult",
            (),
            {
                "resource_resolution": type("ResourceResolution", (), {"status": "degraded"})(),
                "customer_resolution": type(
                    "CustomerResolution",
                    (),
                    {
                        "status": "resolved",
                        "candidates": [
                            type("Customer", (), {"short_name": "联合利华", "customer_id": "C_002"})()
                        ],
                    },
                )(),
            },
        )()
        recovery = type(
            "FakeRecovery",
            (),
            {
                "status": "context-limited",
                "write_ceiling": "recommendation-only",
                "used_sources": [],
                "key_context": [],
                "open_questions": [],
                "candidate_conflicts": [],
                "missing_sources": ["客户档案"],
                "fallback_reason": "permission denied while reading drive folder",
            },
        )()

        with patch.object(scene_runtime, "_build_live_scene_context", return_value=(gateway_result, recovery)):
            result = scene_runtime.run_customer_recent_status_scene(
                SceneRequest(
                    scene_name="customer-recent-status",
                    repo_root=REPO_ROOT,
                    customer_query="联合利华",
                )
            )

        self.assertEqual(result.fallback_category, "permission")

    def test_archive_refresh_scene_surfaces_archive_refresh_guidance(self) -> None:
        gateway_result = type(
            "FakeGatewayResult",
            (),
            {
                "resource_resolution": type("ResourceResolution", (), {"status": "resolved"})(),
                "customer_resolution": type(
                    "CustomerResolution",
                    (),
                    {
                        "status": "resolved",
                        "candidates": [
                            type("Customer", (), {"short_name": "联合利华", "customer_id": "C_002"})()
                        ],
                    },
                )(),
            },
        )()
        recovery = type(
            "FakeRecovery",
            (),
            {
                "status": "partial",
                "write_ceiling": "recommendation-only",
                "used_sources": ["客户主数据", "客户档案候选"],
                "key_context": ["客户档案候选: 联合利华客户档案｜https://doc.example/archive"],
                "open_questions": ["需确认 canonical archive"],
                "candidate_conflicts": ["客户档案候选缺少显式客户证据"],
                "missing_sources": [],
                "fallback_reason": "some targeted live reads are still missing",
            },
        )()

        with patch.object(scene_runtime, "_build_live_scene_context", return_value=(gateway_result, recovery)):
            result = scene_runtime.run_archive_refresh_scene(
                SceneRequest(
                    scene_name="archive-refresh",
                    repo_root=REPO_ROOT,
                    customer_query="联合利华",
                )
            )

        payload = result.structured_result()
        self.assertEqual(payload["scene_name"], "archive-refresh")
        self.assertTrue(any("archive" in item for item in payload["judgments"]))
        self.assertTrue(any("canonical archive" in item for item in payload["recommendations"]))

    def test_todo_capture_and_update_scene_builds_candidates_and_writes_through_shared_path(self) -> None:
        gateway_result = type(
            "FakeGatewayResult",
            (),
            {
                "resource_resolution": type("ResourceResolution", (), {"status": "resolved"})(),
                "customer_resolution": type(
                    "CustomerResolution",
                    (),
                    {
                        "status": "resolved",
                        "candidates": [
                            type("Customer", (), {"short_name": "联合利华", "customer_id": "C_002"})()
                        ],
                    },
                )(),
            },
        )()
        recovery = type(
            "FakeRecovery",
            (),
            {
                "status": "completed",
                "write_ceiling": "normal",
                "used_sources": ["客户主数据", "行动计划"],
                "key_context": ["当前行动计划: 跟进联合利华复盘｜2026-04-20"],
                "open_questions": [],
                "candidate_conflicts": [],
                "missing_sources": [],
                "fallback_reason": None,
            },
        )()
        write_result = WriteExecutionResult(
            target_object="todo",
            attempted=True,
            allowed=True,
            preflight_status="safe",
            guard_status="allowed",
            dedupe_decision="create_new",
            executed_operation="create",
            remote_object_id="task_guid_22",
            source_context={"scenario": "todo_follow_on"},
        )

        with patch.object(scene_runtime, "_build_live_scene_context", return_value=(gateway_result, recovery)), patch.object(
            scene_runtime.TodoWriter, "for_live_lark_cli", return_value=object()
        ), patch.object(scene_runtime, "run_confirmed_todo_write", return_value=[write_result]):
            result = scene_runtime.run_todo_capture_and_update_scene(
                SceneRequest(
                    scene_name="todo-capture-and-update",
                    repo_root=REPO_ROOT,
                    customer_query="联合利华",
                    inputs={
                        "todo_items": [
                            {
                                "summary": "确认联合利华复盘结论",
                                "owner": "ou_owner",
                                "priority": "高",
                                "due_at": "2026-04-20",
                            }
                        ]
                    },
                    options={"confirm_write": True},
                )
            )

        payload = result.structured_result()
        self.assertEqual(payload["scene_name"], "todo-capture-and-update")
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["candidates"][0]["payload"]["summary"], "确认联合利华复盘结论")
        self.assertEqual(payload["write_result_details"][0]["executed_operation"], "create")

    def test_todo_capture_and_update_scene_unresolved_customer_stays_recommendation_only(self) -> None:
        gateway_result = type(
            "FakeGatewayResult",
            (),
            {
                "resource_resolution": type("ResourceResolution", (), {"status": "resolved"})(),
                "customer_resolution": type("CustomerResolution", (), {"status": "missing", "candidates": []})(),
            },
        )()
        recovery = type(
            "FakeRecovery",
            (),
            {
                "status": "context-limited",
                "write_ceiling": "recommendation-only",
                "used_sources": [],
                "key_context": [],
                "open_questions": [],
                "candidate_conflicts": [],
                "missing_sources": ["客户主数据"],
                "fallback_reason": "customer cannot be resolved (missing) from current live customer master",
            },
        )()

        with patch.object(scene_runtime, "_build_live_scene_context", return_value=(gateway_result, recovery)):
            result = scene_runtime.run_todo_capture_and_update_scene(
                SceneRequest(
                    scene_name="todo-capture-and-update",
                    repo_root=REPO_ROOT,
                    customer_query="联合利华",
                    inputs={"todo_items": [{"summary": "补一条待办"}]},
                )
            )

        payload = result.structured_result()
        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["fallback_category"], "customer")

    def test_runtime_cli_scene_command_supports_customer_recent_status_without_meeting_args(self) -> None:
        result = SceneResult(
            scene_name="customer-recent-status",
            resource_status="resolved",
            customer_status="resolved",
            context_status="completed",
            used_sources=["客户主数据"],
            facts=["客户主数据快照: 联合利华｜客户ID C_002"],
            judgments=["当前客户近期状态已有足够 live 证据，可继续输出经营判断。"],
            open_questions=[],
            recommendations=["基于当前 live 上下文整理一版客户最近状态结论，供后续会前/会后复用。"],
            fallback_category="none",
            fallback_reason=None,
            fallback_message=None,
            write_ceiling="normal",
            output_text="recent status output",
            payload={"scene_payload": {"topic_text": ""}},
        )

        with patch.object(runtime_main, "dispatch_scene", return_value=result) as dispatch:
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = runtime_main.main(
                    [
                        "scene",
                        "customer-recent-status",
                        "--customer-query",
                        "联合利华",
                        "--repo-root",
                        str(REPO_ROOT),
                        "--json",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        request = dispatch.call_args.args[0]
        self.assertEqual(exit_code, 0)
        self.assertEqual(request.scene_name, "customer-recent-status")
        self.assertEqual(request.inputs["eval_name"], None)
        self.assertEqual(payload["scene_name"], "customer-recent-status")

    def test_runtime_cli_scene_command_uses_canonical_scene_dispatch(self) -> None:
        result = SceneResult(
            scene_name="post-meeting-synthesis",
            resource_status="resolved",
            customer_status="resolved",
            context_status="completed",
            used_sources=["客户主数据"],
            facts=[],
            judgments=[],
            open_questions=[],
            recommendations=["确认联合利华后续动作"],
            fallback_category="none",
            fallback_reason=None,
            fallback_message=None,
            write_ceiling="normal",
            output_text="artifact output",
            payload={"candidate_count": 1, "candidates": [], "write_result_details": []},
        )

        with patch.object(runtime_main, "dispatch_scene", return_value=result) as dispatch:
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = runtime_main.main(
                    [
                        "scene",
                        "post-meeting-synthesis",
                        "--eval-name",
                        "unilever-stage-review",
                        "--transcript-file",
                        str(REPO_ROOT / "tests" / "fixtures" / "transcripts" / "20260410-联合利华 Campaign活动分析优化-阶段汇报.txt"),
                        "--customer-query",
                        "联合利华",
                        "--repo-root",
                        str(REPO_ROOT),
                        "--confirm-write",
                        "--json",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        request = dispatch.call_args.args[0]
        self.assertEqual(exit_code, 0)
        self.assertEqual(request.scene_name, "post-meeting-synthesis")
        self.assertTrue(request.options["confirm_write"])
        self.assertEqual(payload["scene_name"], "post-meeting-synthesis")
        self.assertEqual(payload["candidate_count"], 1)

    def test_runtime_cli_meeting_write_loop_routes_through_post_meeting_scene(self) -> None:
        write_result = WriteExecutionResult(
            target_object="todo",
            attempted=True,
            allowed=True,
            preflight_status="safe",
            guard_status="allowed",
            dedupe_decision="create_new",
            executed_operation="create",
            remote_object_id="task_guid_11",
            source_context={"scenario": "post_meeting"},
        )
        result = SceneResult(
            scene_name="post-meeting-synthesis",
            resource_status="resolved",
            customer_status="resolved",
            context_status="completed",
            used_sources=["客户主数据"],
            facts=[],
            judgments=[],
            open_questions=[],
            recommendations=["确认联合利华后续动作"],
            fallback_category="none",
            fallback_reason=None,
            fallback_message=None,
            write_ceiling="normal",
            output_text="artifact output",
            payload={
                "candidate_count": 1,
                "candidates": [{"payload": {"summary": "确认联合利华后续动作"}}],
                "write_result_details": [write_result.structured_result()],
            },
        )

        with patch.object(runtime_main, "dispatch_scene", return_value=result) as dispatch:
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = runtime_main.main(
                    [
                        "meeting-write-loop",
                        "--eval-name",
                        "unilever-stage-review",
                        "--transcript-file",
                        str(REPO_ROOT / "tests" / "fixtures" / "transcripts" / "20260410-联合利华 Campaign活动分析优化-阶段汇报.txt"),
                        "--customer-query",
                        "联合利华",
                        "--repo-root",
                        str(REPO_ROOT),
                        "--confirm-write",
                        "--json",
                    ]
                )

        payload = json.loads(stdout.getvalue())
        request = dispatch.call_args.args[0]
        self.assertEqual(exit_code, 0)
        self.assertEqual(request.scene_name, "post-meeting-synthesis")
        self.assertTrue(request.options["confirm_write"])
        self.assertEqual(payload["candidates"][0]["payload"]["summary"], "确认联合利华后续动作")
        self.assertEqual(payload["write_result_details"][0]["executed_operation"], "create")
        self.assertEqual(payload["write_result_details"][0]["remote_metadata"]["object_id"], "task_guid_11")


if __name__ == "__main__":
    unittest.main()
