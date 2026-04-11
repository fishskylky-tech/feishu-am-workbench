from __future__ import annotations

import argparse
from pathlib import Path
from typing import Protocol

from runtime.gateway import FeishuWorkbenchGateway
from runtime.lark_cli import LarkCliClient
from runtime.live_adapter import LarkCliBaseQueryBackend, LiveWorkbenchConfig
from runtime.runtime_sources import RuntimeSourceLoader
from runtime.models import CustomerMatch, CustomerResolution, GatewayResult, ResourceResolution


class GatewayRunner(Protocol):
    def run(self, customer_query: str) -> GatewayResult:
        ...


class QueryBackend(Protocol):
    def query_rows_by_customer_id(
        self, table_name: str, customer_id: str, limit: int = 20
    ) -> list[dict[str, object]]:
        ...


def build_meeting_output(
    *,
    eval_name: str,
    transcript_path: Path,
    gateway_result: GatewayResult,
    context_status: str,
    used_sources: list[str] | None = None,
    fallback_reason: str | None = None,
    key_context: list[str] | None = None,
    missing_sources: list[str] | None = None,
) -> str:
    transcript_text = transcript_path.read_text()
    transcript_title = transcript_path.name
    lines = [
        f"Transcript source: {transcript_title}",
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析结果: {_render_customer_resolution(gateway_result)}",
        f"上下文恢复状态: {context_status}",
    ]

    if used_sources:
        lines.append(f"已使用飞书资料: {'、'.join(used_sources)}")
    elif fallback_reason:
        lines.append(f"fallback 原因: {fallback_reason}")
    else:
        lines.append("fallback 原因: gateway executed but no live sources were retained for this output")

    if key_context:
        lines.append("关键补充背景:")
        lines.extend(f"- {item}" for item in key_context)
    if missing_sources:
        lines.append(f"未找到但应存在的资料: {'、'.join(missing_sources)}")

    lines.extend(_render_case_body(eval_name, transcript_text))
    return "\n".join(lines)


def run_gateway_and_build_meeting_output(
    *,
    eval_name: str,
    transcript_path: Path,
    customer_query: str,
    gateway: GatewayRunner,
    query_backend: QueryBackend,
) -> tuple[str, GatewayResult]:
    gateway_result = gateway.run(customer_query=customer_query)
    context = recover_live_context(
        gateway_result=gateway_result,
        query_backend=query_backend,
    )
    output_text = build_meeting_output(
        eval_name=eval_name,
        transcript_path=transcript_path,
        gateway_result=gateway_result,
        context_status=context["status"],
        used_sources=context["used_sources"],
        fallback_reason=context["fallback_reason"],
        key_context=context["key_context"],
        missing_sources=context["missing_sources"],
    )
    return output_text, gateway_result


def _render_customer_resolution(gateway_result: GatewayResult) -> str:
    resolution = gateway_result.customer_resolution
    if resolution is None:
        return "missing"
    if resolution.status == "resolved" and resolution.candidates:
        best = resolution.candidates[0]
        customer_id = best.customer_id or "missing"
        return f"{best.short_name} / 客户ID {customer_id}"
    if resolution.status == "ambiguous":
        names = "；".join(candidate.short_name for candidate in resolution.candidates) or "multiple candidates"
        return f"ambiguous: {names}"
    return "missing"


def recover_live_context(
    *,
    gateway_result: GatewayResult,
    query_backend: QueryBackend,
) -> dict[str, object]:
    resolution = gateway_result.customer_resolution
    if resolution is None:
        return {
            "status": "context-limited",
            "used_sources": [],
            "fallback_reason": "gateway did not return customer resolution",
            "key_context": [],
            "missing_sources": ["客户主数据"],
        }
    if resolution.status in {"missing", "ambiguous"}:
        return {
            "status": "context-limited",
            "used_sources": [],
            "fallback_reason": f"customer cannot be resolved ({resolution.status}) from current live customer master",
            "key_context": [],
            "missing_sources": ["客户主数据"],
        }

    best = resolution.candidates[0]
    customer_id = best.customer_id
    used_sources = ["客户主数据"]
    key_context = [_render_customer_snapshot(best)]
    missing_sources: list[str] = []

    contact_rows = query_backend.query_rows_by_customer_id("客户联系记录", customer_id, limit=5)
    if contact_rows:
        used_sources.append("客户联系记录")
        key_context.append(_render_latest_contact(contact_rows[0]))
    else:
        missing_sources.append("客户联系记录")

    action_rows = query_backend.query_rows_by_customer_id("行动计划", customer_id, limit=5)
    if action_rows:
        used_sources.append("行动计划")
        key_context.append(_render_latest_action(action_rows[0]))
    else:
        missing_sources.append("行动计划")

    if best.archive_link:
        used_sources.append("客户档案链接")
        key_context.append(f"客户档案链接: {best.archive_link}")
    else:
        missing_sources.append("客户档案")

    status = "completed" if not missing_sources else "partial"
    fallback_reason = None if status == "completed" else "some targeted live reads are still missing"
    return {
        "status": status,
        "used_sources": used_sources,
        "fallback_reason": fallback_reason,
        "key_context": key_context,
        "missing_sources": missing_sources,
    }


def _render_customer_snapshot(best: CustomerMatch) -> str:
    customer_id = best.customer_id or "missing"
    short_name = best.short_name or "unknown"
    return f"客户主数据快照: {short_name}｜客户ID {customer_id}"


def _render_latest_contact(row: dict[str, object]) -> str:
    date = str(row.get("联系日期") or row.get("记录时间") or "日期未提供")
    title = str(row.get("记录标题") or row.get("主题") or "最近联系记录")
    return f"最近联系记录: {date}｜{title}"


def _render_latest_action(row: dict[str, object]) -> str:
    action = str(row.get("具体行动") or row.get("行动主题") or row.get("标题") or "当前行动计划")
    due_at = str(row.get("计划完成时间") or row.get("截止时间") or "时间未提供")
    return f"当前行动计划: {action}｜{due_at}"


def _render_case_body(eval_name: str, transcript_text: str) -> list[str]:
    if eval_name == "unilever-stage-review":
        return _render_unilever_body(transcript_text)
    if eval_name == "yonghe-product-solution-discussion":
        return _render_yonghe_body(transcript_text)
    if eval_name == "dominos-ad-tracking-qa":
        return _render_dominos_body(transcript_text)
    raise KeyError(f"unsupported eval case: {eval_name}")


def _render_unilever_body(transcript_text: str) -> list[str]:
    open_questions = [
        "招募来源口径",
        "激活来源口径",
        "画像如何落地到投放",
    ]
    lines = [
        "Meeting type: stage_review",
        "write ceiling: 客户主数据: no-write; Todo: no-write; 行动计划: recommendation-only",
        "客户主数据: no-write",
        "Todo: no-write",
        "Open questions:",
    ]
    lines.extend(f"- {item}" for item in open_questions)
    lines.extend(
        [
            "Schedule:",
            "- 2026-08 或 2026-09 高峰",
            "- precision gap: 2026年下半年",
        ]
    )
    if "Campaign" in transcript_text:
        lines.append("主题: Campaign 活动分析优化阶段汇报")
    return lines


def _render_yonghe_body(transcript_text: str) -> list[str]:
    lines = [
        "Meeting type: alignment_clarification",
        "客户主数据: no-write",
        "输出重点:",
        "- 知识库",
        "- 记忆",
        "- 归因能力边界",
        "- 后续跟进",
    ]
    if "神策AI" in transcript_text:
        lines.append("会议主题: 神策AI 产品与能力边界讨论")
    return lines


def _render_dominos_body(transcript_text: str) -> list[str]:
    lines = [
        "Meeting type: delivery_issue_handling",
        "客户主数据: no-write",
        "输出重点:",
        "- 归因",
        "- UTM",
        "- dashboard",
        "- 口径",
        "- 支持动作",
    ]
    if "达美乐" in transcript_text:
        lines.append("会议主题: 广告追踪与取数口径答疑")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a minimal meeting output text that can be checked by evals.runner."
    )
    parser.add_argument("--eval-name", required=True)
    parser.add_argument("--transcript-file", required=True)
    parser.add_argument("--resource-status")
    parser.add_argument("--customer-status")
    parser.add_argument("--customer-name")
    parser.add_argument("--customer-id")
    parser.add_argument("--customer-query")
    parser.add_argument("--context-status")
    parser.add_argument("--used-source", action="append", default=[])
    parser.add_argument("--fallback-reason")
    parser.add_argument("--repo-root")
    parser.add_argument("--run-gateway", action="store_true")
    args = parser.parse_args(argv)

    if args.run_gateway:
        customer_query = args.customer_query or args.customer_name or args.customer_id
        if not customer_query:
            raise SystemExit("--run-gateway requires --customer-query, --customer-name, or --customer-id")
        repo_root = args.repo_root or str(Path(__file__).resolve().parents[1])
        gateway = FeishuWorkbenchGateway.for_live_lark_cli(repo_root)
        sources = RuntimeSourceLoader(repo_root).load()
        query_backend = LarkCliBaseQueryBackend(
            LarkCliClient(),
            LiveWorkbenchConfig.from_sources(sources),
        )
        output_text, _ = run_gateway_and_build_meeting_output(
            eval_name=args.eval_name,
            transcript_path=Path(args.transcript_file),
            customer_query=customer_query,
            gateway=gateway,
            query_backend=query_backend,
        )
        print(output_text)
        return 0

    missing = [
        name
        for name, value in (
            ("--resource-status", args.resource_status),
            ("--customer-status", args.customer_status),
            ("--context-status", args.context_status),
        )
        if not value
    ]
    if missing:
        raise SystemExit(f"manual mode requires {' '.join(missing)}")

    candidates = []
    if args.customer_name or args.customer_id:
        candidates.append(
            CustomerMatch(
                customer_id=args.customer_id or "",
                short_name=args.customer_name or "",
            )
        )
    gateway_result = GatewayResult(
        resource_resolution=ResourceResolution(status=args.resource_status),
        customer_resolution=CustomerResolution(
            status=args.customer_status,
            query=args.customer_name or "",
            candidates=candidates,
        ),
    )
    print(
        build_meeting_output(
            eval_name=args.eval_name,
            transcript_path=Path(args.transcript_file),
            gateway_result=gateway_result,
            context_status=args.context_status,
            used_sources=args.used_source,
            fallback_reason=args.fallback_reason,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
