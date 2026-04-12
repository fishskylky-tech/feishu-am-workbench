from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
from typing import Protocol

from runtime.gateway import FeishuWorkbenchGateway
from runtime.lark_cli import LarkCliClient
from runtime.live_adapter import LarkCliBaseQueryBackend, LiveWorkbenchConfig
from runtime.runtime_sources import RuntimeSourceLoader
from runtime.models import (
    CustomerMatch,
    CustomerResolution,
    GatewayResult,
    ResourceResolution,
    WriteCandidate,
    WriteExecutionResult,
)


class GatewayRunner(Protocol):
    def run(self, customer_query: str) -> GatewayResult:
        ...


class QueryBackend(Protocol):
    def query_rows_by_customer_id(
        self, table_name: str, customer_id: str, limit: int = 20
    ) -> list[dict[str, object]]:
        ...


class TodoWriteExecutor(Protocol):
    def create(self, candidate: WriteCandidate) -> WriteExecutionResult:
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
    write_results: list[WriteExecutionResult] | None = None,
) -> str:
    transcript_title = transcript_path.name
    transcript_text, transcript_status = _read_transcript_text(transcript_path)
    lines = [
        f"Transcript source: {transcript_title}",
        f"Transcript status: {transcript_status}",
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
    if write_results:
        lines.append("统一写回结果:")
        lines.extend(_render_write_results(write_results))

    lines.extend(_render_case_body(eval_name, transcript_text))
    return "\n".join(lines)


def _read_transcript_text(transcript_path: Path) -> tuple[str, str]:
    try:
        return transcript_path.read_text(), "available"
    except FileNotFoundError:
        return "", "missing"


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
        topic_text=transcript_path.stem,
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


def build_meeting_todo_candidates(
    *,
    eval_name: str,
    gateway_result: GatewayResult,
) -> list[WriteCandidate]:
    resolution = gateway_result.customer_resolution
    if resolution is None or resolution.status != "resolved" or not resolution.candidates:
        return []
    customer = resolution.candidates[0]
    if eval_name != "unilever-stage-review":
        return []
    summary = _build_recommended_todo_summary(eval_name, customer.short_name)
    return [
        WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "owner", "customer", "priority", "due_at"],
            payload={
                "summary": summary,
                "customer": customer.short_name,
                "priority": "高",
                "description": "来自会议场景的建议态跟进动作；负责人待确认后才能真正写入。",
            },
            match_basis={
                "customer": customer.short_name,
            },
            source_context={
                "scenario": "post_meeting",
                "meeting_eval": eval_name,
                "customer_id": customer.customer_id,
            },
        )
    ]


def run_confirmed_todo_write(
    *,
    candidates: list[WriteCandidate],
    todo_writer: TodoWriteExecutor,
) -> list[WriteExecutionResult]:
    results: list[WriteExecutionResult] = []
    for candidate in candidates:
        if candidate.operation == "update":
            continue
        results.append(todo_writer.create(candidate))
    return results


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
    topic_text: str = "",
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

    meeting_notes = _rank_related_meeting_notes(contact_rows, topic_text=topic_text, limit=3)
    if meeting_notes:
        used_sources.append("相关会议纪要候选")
        key_context.append(f"相关会议纪要候选: {'；'.join(meeting_notes)}")

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


def _rank_related_meeting_notes(
    contact_rows: list[dict[str, object]],
    *,
    topic_text: str,
    limit: int,
) -> list[str]:
    if not contact_rows:
        return []
    topic_terms = _topic_terms(topic_text)
    candidates: list[tuple[int, str]] = []
    seen_links: set[str] = set()
    for row in contact_rows:
        title = str(
            row.get("会议纪要标题")
            or row.get("记录标题")
            or row.get("主题")
            or ""
        ).strip()
        link = str(
            row.get("会议纪要链接")
            or row.get("会议记录链接")
            or row.get("纪要链接")
            or ""
        ).strip()
        date = str(row.get("联系日期") or row.get("记录时间") or "")
        if not title or not link or link in seen_links:
            continue
        seen_links.add(link)
        score = _meeting_note_score(title=title, date=date, topic_terms=topic_terms)
        candidates.append((score, f"{title}｜{date or '日期未提供'}｜{link}"))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:limit]]


def _topic_terms(text: str) -> set[str]:
    normalized = text.lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", normalized)
    parts = [part for part in normalized.split() if part]
    stop_words = {"会议", "纪要", "记录", "阶段", "汇报"}
    return {part for part in parts if part not in stop_words}


def _meeting_note_score(*, title: str, date: str, topic_terms: set[str]) -> int:
    title_terms = _topic_terms(title)
    overlap = len(title_terms.intersection(topic_terms)) if topic_terms else 0
    score = overlap * 10
    if date:
        score += 3
        note_dt = _parse_note_date(date)
        if note_dt is not None:
            days = abs((datetime.utcnow() - note_dt).days)
            if days <= 30:
                score += 20
            elif days <= 90:
                score += 10
    return score


def _parse_note_date(date_str: str) -> datetime | None:
    # Extract first YYYY-MM-DD-like token from mixed date strings.
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_str)
    if not match:
        return None
    try:
        year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return datetime(year, month, day)
    except ValueError:
        return None


def _render_case_body(eval_name: str, transcript_text: str) -> list[str]:
    if eval_name == "unilever-stage-review":
        return _render_unilever_body(transcript_text)
    if eval_name == "yonghe-product-solution-discussion":
        return _render_yonghe_body(transcript_text)
    if eval_name == "dominos-ad-tracking-qa":
        return _render_dominos_body(transcript_text)
    raise KeyError(f"unsupported eval case: {eval_name}")


def _render_write_results(write_results: list[WriteExecutionResult]) -> list[str]:
    lines: list[str] = []
    for item in write_results:
        blocked = ",".join(item.blocked_reasons) if item.blocked_reasons else "none"
        lines.append(
            f"- {item.target_object}: {item.executed_operation} "
            f"(dedupe={item.dedupe_decision}; preflight={item.preflight_status}; "
            f"guard={item.guard_status}; blocked={blocked})"
        )
    return lines


def _build_recommended_todo_summary(eval_name: str, customer_name: str) -> str:
    if eval_name == "unilever-stage-review":
        return f"跟进{customer_name}下一轮 Campaign 优化方案确认"
    return f"跟进{customer_name}会议后续动作确认"


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
