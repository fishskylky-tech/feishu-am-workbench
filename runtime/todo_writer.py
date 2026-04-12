"""Minimal live Todo create writer guarded by schema preflight."""

from __future__ import annotations

import json
from datetime import datetime
import re

from .lark_cli import LarkCliClient
from .live_adapter import LarkCliSchemaBackend, LiveWorkbenchConfig
from .models import TodoWriteResult, WriteCandidate
from .runtime_sources import RuntimeSourceLoader
from .schema_preflight import SchemaPreflightRunner
from .write_guard import WriteGuard


class TodoWriter:
    def __init__(
        self,
        client: LarkCliClient,
        config: LiveWorkbenchConfig,
        schema_preflight: SchemaPreflightRunner,
        write_guard: WriteGuard | None = None,
        existing_tasks: list[dict[str, object]] | None = None,
    ) -> None:
        self.client = client
        self.config = config
        self.schema_preflight = schema_preflight
        self.write_guard = write_guard or WriteGuard()
        self.existing_tasks = existing_tasks or []

    @classmethod
    def for_live_lark_cli(cls, repo_root: str) -> "TodoWriter":
        sources = RuntimeSourceLoader(repo_root).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        client = LarkCliClient()
        return cls(
            client=client,
            config=config,
            schema_preflight=SchemaPreflightRunner(LarkCliSchemaBackend(client, config)),
        )

    def create(self, candidate: WriteCandidate) -> TodoWriteResult:
        report = self.schema_preflight.run(candidate)
        duplicate_task = self._find_duplicate_task(candidate)
        if duplicate_task:
            duplicate_task_guid = str(duplicate_task.get("guid") or "")
            if not duplicate_task_guid:
                duplicate_task = None
            else:
                decision = self._decide_duplicate_action(candidate, duplicate_task)
                if decision == "create_subtask":
                    if self._should_execute_create_subtask(candidate):
                        return self._create_subtask(
                            parent_task_guid=duplicate_task_guid,
                            candidate=candidate,
                            report=report,
                        )
                    return TodoWriteResult(
                        target_object=candidate.target_object or "todo",
                        attempted=False,
                        allowed=False,
                        preflight_status=report.status,
                        guard_status="blocked",
                        dedupe_decision="create_subtask",
                        executed_operation="blocked",
                        remote_object_id=duplicate_task_guid or None,
                        blocked_reasons=["semantic_duplicate_detected", "subtask_recommended"],
                        drift_items=self._collect_drift_items(report),
                        source_context=dict(candidate.source_context),
                        preflight_report=report,
                    )
                update_candidate = self._build_duplicate_update_candidate(candidate)
                result = self.update(duplicate_task_guid, update_candidate)
                result.dedupe_decision = "update_existing"
                return result

        guard = self.write_guard.evaluate(candidate, report, owner_required=True)
        if not guard.allowed:
            return TodoWriteResult(
                target_object=candidate.target_object or "todo",
                attempted=False,
                allowed=False,
                preflight_status=report.status,
                guard_status="blocked",
                dedupe_decision="no_write",
                executed_operation="blocked",
                blocked_reasons=list(dict.fromkeys(guard.reasons)),
                drift_items=self._collect_drift_items(report),
                source_context=dict(candidate.source_context),
                preflight_report=report,
                guard_result=guard,
            )

        request_payload = self._build_create_payload(candidate)
        response = self.client.invoke_json(
            [
                "task",
                "tasks",
                "create",
                "--data",
                json.dumps(request_payload, ensure_ascii=False),
            ]
        )
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        task = data.get("task") if isinstance(data, dict) and isinstance(data.get("task"), dict) else {}
        return TodoWriteResult(
            target_object=candidate.target_object or "todo",
            attempted=True,
            allowed=True,
            preflight_status=report.status,
            guard_status="allowed",
            dedupe_decision="create_new",
            executed_operation="create",
            remote_object_id=str(task.get("guid")) if task.get("guid") is not None else None,
            remote_url=str(task.get("url")) if task.get("url") is not None else None,
            drift_items=self._collect_drift_items(report),
            source_context=dict(candidate.source_context),
            preflight_report=report,
            guard_result=guard,
            request_payload=request_payload,
        )

    def update(self, task_guid: str, candidate: WriteCandidate) -> TodoWriteResult:
        report = self.schema_preflight.run(candidate)
        guard = self.write_guard.evaluate(candidate, report, owner_required=False)
        if not guard.allowed:
            return TodoWriteResult(
                target_object=candidate.target_object or "todo",
                attempted=False,
                allowed=False,
                preflight_status=report.status,
                guard_status="blocked",
                dedupe_decision="no_write",
                executed_operation="blocked",
                blocked_reasons=list(dict.fromkeys(guard.reasons)),
                drift_items=self._collect_drift_items(report),
                source_context=dict(candidate.source_context),
                preflight_report=report,
                guard_result=guard,
            )

        current_task = self._get_task(task_guid)
        patch_payload, update_fields = self._build_patch_payload(candidate)
        request_payload: dict[str, object] = {}
        task = current_task
        if update_fields:
            request_payload["patch"] = {
                "task": patch_payload,
                "update_fields": update_fields,
            }
            response = self.client.invoke_json(
                [
                    "task",
                    "tasks",
                    "patch",
                    "--params",
                    json.dumps({"task_guid": task_guid}, ensure_ascii=False),
                    "--data",
                    json.dumps(request_payload["patch"], ensure_ascii=False),
                ]
            )
            data = response.get("data") if isinstance(response.get("data"), dict) else {}
            patched = data.get("task") if isinstance(data, dict) and isinstance(data.get("task"), dict) else None
            if isinstance(patched, dict):
                task = patched

        owner_payload = candidate.payload.get("owner")
        if owner_payload is not None:
            member_ops = self._sync_owner(task_guid, current_task, owner_payload)
            if member_ops:
                request_payload.update(member_ops)
                task = self._get_task(task_guid)

        return TodoWriteResult(
            target_object=candidate.target_object or "todo",
            attempted=True,
            allowed=True,
            preflight_status=report.status,
            guard_status="allowed",
            dedupe_decision="update_existing",
            executed_operation="update",
            remote_object_id=str(task.get("guid")) if task.get("guid") is not None else task_guid,
            remote_url=str(task.get("url")) if task.get("url") is not None else None,
            drift_items=self._collect_drift_items(report),
            source_context=dict(candidate.source_context),
            preflight_report=report,
            guard_result=guard,
            request_payload=request_payload,
        )

    def _build_create_payload(self, candidate: WriteCandidate) -> dict[str, object]:
        payload = candidate.payload
        request: dict[str, object] = {
            "summary": str(payload.get("summary") or ""),
            "tasklists": [{"tasklist_guid": self.config.tasklist_guid}],
            "members": [self._build_assignee(payload["owner"])],
        }
        description = payload.get("description")
        if isinstance(description, str) and description.strip():
            request["description"] = description
        due = self._build_due(payload.get("due_at"))
        if due:
            request["due"] = due
        custom_fields = self._build_custom_fields(payload)
        if custom_fields:
            request["custom_fields"] = custom_fields
        return request

    def _build_subtask_create_payload(
        self, parent_task_guid: str, candidate: WriteCandidate
    ) -> dict[str, object]:
        request = self._build_create_payload(candidate)
        request["parent_task_guid"] = parent_task_guid
        return request

    def _build_patch_payload(
        self, candidate: WriteCandidate
    ) -> tuple[dict[str, object], list[str]]:
        payload = candidate.payload
        task_payload: dict[str, object] = {}
        update_fields: list[str] = []
        if "summary" in payload:
            task_payload["summary"] = str(payload.get("summary") or "")
            update_fields.append("summary")
        if "description" in payload:
            description = payload.get("description")
            task_payload["description"] = str(description) if description is not None else ""
            update_fields.append("description")
        if "due_at" in payload:
            due = self._build_due(payload.get("due_at"))
            task_payload["due"] = due or {"timestamp": "", "is_all_day": False}
            update_fields.append("due")
        custom_fields = self._build_custom_fields(payload)
        if custom_fields and any(key in payload for key in ("customer", "priority")):
            task_payload["custom_fields"] = custom_fields
            update_fields.append("custom_fields")
        return task_payload, update_fields

    def _build_assignee(self, owner_payload: object) -> dict[str, str]:
        if isinstance(owner_payload, dict):
            owner_id = owner_payload.get("id")
        else:
            owner_id = owner_payload
        return {
            "id": str(owner_id),
            "role": "assignee",
            "type": "user",
        }

    def _build_custom_fields(self, payload: dict[str, object]) -> list[dict[str, str]]:
        custom_fields: list[dict[str, str]] = []
        customer = payload.get("customer")
        if (
            self.config.todo_customer_field_guid
            and isinstance(customer, str)
            and customer.strip()
        ):
            custom_fields.append(
                {
                    "guid": self.config.todo_customer_field_guid,
                    "text_value": customer.strip(),
                }
            )
        priority = payload.get("priority")
        if (
            self.config.todo_priority_field_guid
            and isinstance(priority, str)
            and priority.strip()
        ):
            option_guid = self.config.todo_priority_option_guids.get(priority.strip())
            if option_guid:
                custom_fields.append(
                    {
                        "guid": self.config.todo_priority_field_guid,
                        "single_select_value": option_guid,
                    }
                )
        return custom_fields

    def _build_due(self, value: object) -> dict[str, object] | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return {"timestamp": str(int(value)), "is_all_day": False}
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None
            if raw.isdigit():
                return {"timestamp": raw, "is_all_day": False}
            try:
                if len(raw) == 10:
                    dt = datetime.strptime(raw, "%Y-%m-%d")
                    return {
                        "timestamp": str(int(dt.timestamp() * 1000)),
                        "is_all_day": True,
                    }
                dt = datetime.fromisoformat(raw)
                return {
                    "timestamp": str(int(dt.timestamp() * 1000)),
                    "is_all_day": False,
                }
            except ValueError:
                return None
        return None

    def _get_task(self, task_guid: str) -> dict[str, object]:
        response = self.client.invoke_json(
            [
                "task",
                "tasks",
                "get",
                "--params",
                json.dumps({"task_guid": task_guid}, ensure_ascii=False),
            ]
        )
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        task = data.get("task") if isinstance(data, dict) and isinstance(data.get("task"), dict) else None
        return task if isinstance(task, dict) else {"guid": task_guid}

    def _sync_owner(
        self,
        task_guid: str,
        current_task: dict[str, object],
        owner_payload: object,
    ) -> dict[str, object]:
        target_owner_id = self._extract_owner_id(owner_payload)
        current_assignees = self._extract_assignee_ids(current_task)
        operations: dict[str, object] = {}
        if target_owner_id in current_assignees and len(current_assignees) == 1:
            return operations

        if current_assignees:
            remove_members = [
                {"id": member_id, "role": "assignee", "type": "user"}
                for member_id in current_assignees
                if member_id != target_owner_id
            ]
            if remove_members:
                operations["member_remove"] = {"members": remove_members}
                self.client.invoke_json(
                    [
                        "task",
                        "members",
                        "remove",
                        "--params",
                        json.dumps({"task_guid": task_guid}, ensure_ascii=False),
                        "--data",
                        json.dumps(operations["member_remove"], ensure_ascii=False),
                    ]
                )

        if target_owner_id and target_owner_id not in current_assignees:
            operations["member_add"] = {
                "members": [
                    {"id": target_owner_id, "role": "assignee", "type": "user"}
                ]
            }
            self.client.invoke_json(
                [
                    "task",
                    "members",
                    "add",
                    "--params",
                    json.dumps({"task_guid": task_guid}, ensure_ascii=False),
                    "--data",
                    json.dumps(operations["member_add"], ensure_ascii=False),
                ]
            )
        return operations

    def _extract_assignee_ids(self, task: dict[str, object]) -> list[str]:
        members = task.get("members")
        if not isinstance(members, list):
            return []
        assignees: list[str] = []
        for member in members:
            if not isinstance(member, dict):
                continue
            if member.get("role") != "assignee":
                continue
            member_id = member.get("id")
            if member_id is not None:
                assignees.append(str(member_id))
        return assignees

    def _extract_owner_id(self, owner_payload: object) -> str | None:
        if isinstance(owner_payload, dict):
            owner_id = owner_payload.get("id")
            return str(owner_id) if owner_id is not None else None
        if owner_payload is None:
            return None
        return str(owner_payload)

    def _collect_drift_items(self, report) -> list[str]:
        return [
            item
            for field_result in report.field_results
            for item in field_result.drift_items
        ]

    def _should_execute_create_subtask(self, candidate: WriteCandidate) -> bool:
        flag = candidate.source_context.get("confirm_create_subtask")
        return bool(flag)

    def _create_subtask(
        self,
        *,
        parent_task_guid: str,
        candidate: WriteCandidate,
        report,
    ) -> TodoWriteResult:
        guard = self.write_guard.evaluate(candidate, report, owner_required=True)
        if not guard.allowed:
            reasons = list(dict.fromkeys([*guard.reasons, "subtask_confirmed_but_guard_blocked"]))
            return TodoWriteResult(
                target_object=candidate.target_object or "todo",
                attempted=False,
                allowed=False,
                preflight_status=report.status,
                guard_status="blocked",
                dedupe_decision="create_subtask",
                executed_operation="blocked",
                remote_object_id=parent_task_guid or None,
                blocked_reasons=reasons,
                drift_items=self._collect_drift_items(report),
                source_context=dict(candidate.source_context),
                preflight_report=report,
                guard_result=guard,
            )

        request_payload = self._build_subtask_create_payload(parent_task_guid, candidate)
        response = self.client.invoke_json(
            [
                "task",
                "tasks",
                "create",
                "--data",
                json.dumps(request_payload, ensure_ascii=False),
            ]
        )
        data = response.get("data") if isinstance(response.get("data"), dict) else {}
        task = data.get("task") if isinstance(data, dict) and isinstance(data.get("task"), dict) else {}
        return TodoWriteResult(
            target_object=candidate.target_object or "todo",
            attempted=True,
            allowed=True,
            preflight_status=report.status,
            guard_status="allowed",
            dedupe_decision="create_subtask",
            executed_operation="create",
            remote_object_id=str(task.get("guid")) if task.get("guid") is not None else None,
            remote_url=str(task.get("url")) if task.get("url") is not None else None,
            blocked_reasons=[],
            drift_items=self._collect_drift_items(report),
            source_context=dict(candidate.source_context),
            preflight_report=report,
            guard_result=guard,
            request_payload=request_payload,
        )

    def _find_duplicate_task(self, candidate: WriteCandidate) -> dict[str, object] | None:
        summary = str(candidate.payload.get("summary") or "").strip()
        customer = str(
            candidate.match_basis.get("customer")
            or candidate.payload.get("customer")
            or ""
        ).strip()
        due_at = str(
            candidate.match_basis.get("time_window")
            or candidate.payload.get("due_at")
            or ""
        ).strip()
        candidate_terms = self._normalize_terms(summary)
        if not summary or not customer or not candidate_terms:
            return None

        best_match: dict[str, object] | None = None
        best_overlap = 0
        for task in self.existing_tasks:
            task_customer = str(task.get("customer") or "").strip()
            if task_customer != customer:
                continue
            existing_terms = self._normalize_terms(str(task.get("summary") or ""))
            if not existing_terms:
                continue
            if not self._is_same_time_window(due_at, str(task.get("due_at") or "")):
                continue
            overlap = len(candidate_terms.intersection(existing_terms))
            if overlap >= 2 and overlap > best_overlap:
                best_overlap = overlap
                best_match = task
        return best_match

    def _decide_duplicate_action(
        self,
        candidate: WriteCandidate,
        existing_task: dict[str, object],
    ) -> str:
        candidate_terms = self._normalize_terms(str(candidate.payload.get("summary") or ""))
        existing_terms = self._normalize_terms(str(existing_task.get("summary") or ""))
        if not candidate_terms or not existing_terms:
            return "update_existing"

        overlap = len(candidate_terms.intersection(existing_terms))
        ratio = overlap / max(1, min(len(candidate_terms), len(existing_terms)))
        candidate_has_execution_detail = self._has_execution_detail_signal(candidate_terms)
        existing_has_parent_scope = self._has_parent_scope_signal(existing_terms)

        if ratio >= 0.75 and candidate_has_execution_detail and existing_has_parent_scope:
            return "create_subtask"
        return "update_existing"

    def _build_duplicate_update_candidate(self, candidate: WriteCandidate) -> WriteCandidate:
        patchable_fields = ["summary", "description", "due_at", "customer", "priority"]
        payload = {
            key: value
            for key, value in candidate.payload.items()
            if key in patchable_fields
        }
        semantic_fields = [
            field
            for field in candidate.semantic_fields
            if field in patchable_fields
        ]
        return WriteCandidate(
            object_name=candidate.object_name,
            target_object=candidate.target_object,
            layer=candidate.layer,
            operation="update",
            semantic_fields=semantic_fields,
            payload=payload,
            match_basis=dict(candidate.match_basis),
            source_context=dict(candidate.source_context),
        )

    def _normalize_terms(self, summary: str) -> set[str]:
        normalized = summary.lower()
        normalized = re.sub(r"[（）()｜|,，/\\:：_\\-]+", " ", normalized)
        normalized = re.sub(r"[·•。；;!！?？\[\]{}]+", " ", normalized)
        normalized = re.sub(r"([a-z0-9]+)([\u4e00-\u9fff])", r"\1 \2", normalized)
        normalized = re.sub(r"([\u4e00-\u9fff])([a-z0-9]+)", r"\1 \2", normalized)
        for token in ("方案", "确认", "推进", "跟进", "续费", "沟通", "处理", "更新"):
            normalized = normalized.replace(token, f" {token} ")
        synonym_map = {
            "campaign": "活动",
            "复盘": "总结",
            "会前包": "会前资料",
        }
        for src, dst in synonym_map.items():
            normalized = normalized.replace(src, dst)
        parts = [part for part in re.split(r"[\s｜|,，/]+", normalized) if part]
        stop_words = {"的", "和", "并", "及", "请", "帮", "一下"}
        terms = {part for part in parts if part not in stop_words}

        # Add CJK bi-grams for long continuous Chinese fragments to improve recall.
        for part in list(terms):
            if re.fullmatch(r"[\u4e00-\u9fff]{4,}", part):
                for idx in range(len(part) - 1):
                    terms.add(part[idx : idx + 2])
        return terms

    def _has_execution_detail_signal(self, terms: set[str]) -> bool:
        detail_tokens = {
            "整理",
            "同步",
            "提交",
            "发送",
            "对齐",
            "准备",
            "资料",
            "清单",
            "文档",
            "邮件",
        }
        return any(token in terms for token in detail_tokens)

    def _has_parent_scope_signal(self, terms: set[str]) -> bool:
        scope_tokens = {
            "项目",
            "计划",
            "方案",
            "策略",
            "推进",
            "跟进",
        }
        return any(token in terms for token in scope_tokens)

    def _is_same_time_window(self, candidate_due_at: str, existing_due_at: str) -> bool:
        if not candidate_due_at or not existing_due_at:
            return False
        candidate_window = candidate_due_at[:7]
        existing_window = existing_due_at[:7]
        return candidate_window == existing_window
