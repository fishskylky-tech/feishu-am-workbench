"""Minimal live Todo create writer guarded by schema preflight."""

from __future__ import annotations

import json
from datetime import datetime

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
    ) -> None:
        self.client = client
        self.config = config
        self.schema_preflight = schema_preflight
        self.write_guard = write_guard or WriteGuard()

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
        guard = self.write_guard.evaluate(candidate, report, owner_required=True)
        if not guard.allowed:
            return TodoWriteResult(
                attempted=False,
                allowed=False,
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
            attempted=True,
            allowed=True,
            preflight_report=report,
            guard_result=guard,
            task_guid=str(task.get("guid")) if task.get("guid") is not None else None,
            task_url=str(task.get("url")) if task.get("url") is not None else None,
            request_payload=request_payload,
        )

    def update(self, task_guid: str, candidate: WriteCandidate) -> TodoWriteResult:
        report = self.schema_preflight.run(candidate)
        guard = self.write_guard.evaluate(candidate, report, owner_required=False)
        if not guard.allowed:
            return TodoWriteResult(
                attempted=False,
                allowed=False,
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
            attempted=True,
            allowed=True,
            preflight_report=report,
            guard_result=guard,
            task_guid=str(task.get("guid")) if task.get("guid") is not None else task_guid,
            task_url=str(task.get("url")) if task.get("url") is not None else None,
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
