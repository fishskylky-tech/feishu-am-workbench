"""Runtime diagnostics for local Feishu workbench capability checks."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .gateway import FeishuWorkbenchGateway
from .models import CapabilityCheck, GatewayResult


def build_live_diagnostic(repo_root: str | Path) -> dict[str, Any]:
    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    result = gateway.run(customer_query="")
    return {
        "resource_resolution": {
            "status": result.resource_resolution.status,
            "missing_keys": result.resource_resolution.missing_keys,
            "unconfirmed_keys": result.resource_resolution.unconfirmed_keys,
            "hints": [
                {
                    "key": hint.key,
                    "source_file": hint.source_file,
                    "value": hint.value,
                    "confirmed_live": hint.confirmed_live,
                }
                for hint in result.resource_resolution.hints_used
            ],
        },
        "capability_report": [
            asdict(check) for check in (result.capability_report.checks if result.capability_report else [])
        ],
        "customer_resolution": (
            {
                "status": result.customer_resolution.status,
                "query": result.customer_resolution.query,
            }
            if result.customer_resolution
            else None
        ),
    }


def render_live_diagnostic(report: dict[str, Any]) -> str:
    lines: list[str] = []
    resource = report["resource_resolution"]
    overall_status = _overall_status(report)
    summary_reason = _summary_reason(report)
    summary_actions = _summary_next_actions(report)

    lines.append("Feishu Workbench Runtime Diagnostic")
    lines.append(f"conclusion: {overall_status}")
    if summary_reason:
        lines.append(f"reason: {summary_reason}")
    for action in summary_actions:
        lines.append(f"next action: {action}")
    lines.append(f"resource status: {resource['status']}")
    if resource["missing_keys"]:
        lines.append(f"missing resources: {', '.join(resource['missing_keys'])}")
    if resource["unconfirmed_keys"]:
        lines.append(f"unconfirmed live resources: {', '.join(resource['unconfirmed_keys'])}")

    lines.append("")
    lines.append("capabilities:")
    for check in report["capability_report"]:
        lines.extend(_render_check(check))
    return "\n".join(lines)


def _render_check(check: dict[str, Any]) -> list[str]:
    lines = [f"- {check['name']}: {check['status']}"]
    reasons = check.get("reasons") or []
    if reasons:
        lines.append(f"  reason: {', '.join(reasons)}")
    details = check.get("details") or {}
    detail_lines = _render_details(details)
    lines.extend([f"  {line}" for line in detail_lines])
    lines.extend([f"  next action: {line}" for line in suggest_next_actions(_to_check(check))])
    return lines


def _render_details(details: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if "env_var" in details:
        lines.append(f"env var: {details['env_var']}")
    if "hint" in details and details["hint"]:
        lines.append(f"hint: {details['hint']}")
    if "message" in details and details["message"]:
        lines.append(f"message: {details['message']}")
    if "outcomes" in details:
        for index, outcome in enumerate(details["outcomes"], start=1):
            reason = outcome.get("reason") or "unknown"
            lines.append(f"outcome {index}: {outcome.get('status', 'unknown')} / {reason}")
            if outcome.get("hint"):
                lines.append(f"outcome {index} hint: {outcome['hint']}")
    required_tables = details.get("required_tables")
    if isinstance(required_tables, dict) and required_tables:
        rendered = [f"{name}->{target}" for name, target in required_tables.items()]
        lines.append(f"required tables: {', '.join(rendered)}")
    table_targets = details.get("table_targets")
    if isinstance(table_targets, dict) and table_targets:
        rendered = [f"{name}->{target}" for name, target in table_targets.items()]
        lines.append(f"table targets: {', '.join(rendered)}")
    return lines


def suggest_next_actions(check: CapabilityCheck) -> list[str]:
    if check.name == "base_access" and "missing_base_token" in check.reasons:
        return ["export FEISHU_AM_BASE_TOKEN into the current shell before live Base reads"]
    if check.name == "docs_access" and "docs_resource_missing" in check.reasons:
        return [
            "export FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER and FEISHU_AM_MEETING_NOTES_FOLDER before live Docs reads"
        ]
    if check.name == "task_access" and "tasklist_missing" in check.reasons:
        return ["export FEISHU_AM_TODO_TASKLIST_GUID before live Task reads"]
    if check.name == "docs_access" and any(
        reason in {"permission", "missing_scope"} for reason in check.reasons
    ):
        return ["run lark-cli auth login with drive/doc read scopes for folder and doc access"]
    if check.name == "task_access" and check.status == "available":
        return ["task adapter is usable; keep this as the known-good baseline"]
    if check.status == "available":
        return ["no action required"]
    return ["inspect lark-cli auth state and the current private runtime env configuration"]


def _overall_status(report: dict[str, Any]) -> str:
    resource = report["resource_resolution"]
    capability_report = report.get("capability_report") or []
    statuses = {str(check.get("status", "")) for check in capability_report}
    if resource["missing_keys"] or "blocked" in statuses:
        return "blocked"
    if resource["unconfirmed_keys"] or "degraded" in statuses or resource["status"] == "partial":
        return "degraded"
    return "available"


def _summary_reason(report: dict[str, Any]) -> str | None:
    resource = report["resource_resolution"]
    if resource["missing_keys"]:
        return f"missing required private runtime inputs: {', '.join(resource['missing_keys'])}"
    if resource["unconfirmed_keys"]:
        return f"some configured resources are not yet confirmed live: {', '.join(resource['unconfirmed_keys'])}"
    blocked_checks = [check for check in report.get("capability_report") or [] if check.get("status") == "blocked"]
    if blocked_checks:
        names = ", ".join(str(check.get("name")) for check in blocked_checks)
        return f"live startup is blocked in: {names}"
    degraded_checks = [check for check in report.get("capability_report") or [] if check.get("status") == "degraded"]
    if degraded_checks:
        names = ", ".join(str(check.get("name")) for check in degraded_checks)
        return f"live startup is degraded in: {names}"
    return None


def _summary_next_actions(report: dict[str, Any]) -> list[str]:
    resource = report["resource_resolution"]
    if resource["missing_keys"]:
        env_map = {
            "base_token": "FEISHU_AM_BASE_TOKEN",
            "customer_archive_folder": "FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER",
            "meeting_notes_folder": "FEISHU_AM_MEETING_NOTES_FOLDER",
            "todo_tasklist_guid": "FEISHU_AM_TODO_TASKLIST_GUID",
        }
        needed = [env_map[key] for key in resource["missing_keys"] if key in env_map]
        if needed:
            return [f"export the missing env vars and rerun: {', '.join(needed)}"]
    actions: list[str] = []
    for check in report.get("capability_report") or []:
        actions.extend(suggest_next_actions(_to_check(check)))
    deduped: list[str] = []
    for action in actions:
        if action not in deduped:
            deduped.append(action)
    return deduped[:3]


def _to_check(raw: dict[str, Any]) -> CapabilityCheck:
    return CapabilityCheck(
        name=str(raw["name"]),
        status=str(raw["status"]),
        reasons=[str(item) for item in raw.get("reasons", [])],
        details=dict(raw.get("details", {})),
    )
