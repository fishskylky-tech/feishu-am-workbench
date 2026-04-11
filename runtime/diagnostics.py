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
    lines.append("Feishu Workbench Runtime Diagnostic")
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
        lines.append(f"  reasons: {', '.join(reasons)}")
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
    if check.name == "docs_access" and any(
        reason in {"permission", "missing_scope"} for reason in check.reasons
    ):
        return ["run lark-cli auth login with drive/doc read scopes for folder and doc access"]
    if check.name == "task_access" and check.status == "available":
        return ["task adapter is usable; keep this as the known-good baseline"]
    if check.status == "available":
        return ["no action required"]
    return ["inspect lark-cli auth state and current resource hint sources"]


def _to_check(raw: dict[str, Any]) -> CapabilityCheck:
    return CapabilityCheck(
        name=str(raw["name"]),
        status=str(raw["status"]),
        reasons=[str(item) for item in raw.get("reasons", [])],
        details=dict(raw.get("details", {})),
    )
