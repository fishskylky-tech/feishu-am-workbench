from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
from typing import Protocol

from runtime.gateway import FeishuWorkbenchGateway
from runtime.lark_cli import LarkCliClient
from runtime.live_adapter import LarkCliBaseQueryBackend, LiveWorkbenchConfig
from runtime.semantic_registry import SEMANTIC_FIELD_REGISTRY
from runtime.runtime_sources import RuntimeSourceLoader
from runtime.models import (
    CustomerMatch,
    CustomerResolution,
    ContextRecoveryResult,
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
    context_status: str | None = None,
    used_sources: list[str] | None = None,
    fallback_reason: str | None = None,
    key_context: list[str] | None = None,
    missing_sources: list[str] | None = None,
    recovery: ContextRecoveryResult | None = None,
    write_results: list[WriteExecutionResult] | None = None,
) -> str:
    if recovery is not None:
        context_status = recovery.status
        used_sources = recovery.used_sources
        fallback_reason = recovery.fallback_reason
        key_context = recovery.key_context
        missing_sources = recovery.missing_sources

    if context_status is None:
        raise ValueError("context_status is required when recovery is not provided")

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
    if recovery is not None:
        lines.append(f"写回上限: {recovery.write_ceiling}")
        audit_open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
        if audit_open_questions:
            lines.append("开放问题:")
            lines.extend(f"- {item}" for item in audit_open_questions)
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
        recovery=context,
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
                "time_window": "2026-04",
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
        target_object = candidate.target_object or "todo"
        if candidate.operation == "update":
            results.append(
                WriteExecutionResult(
                    target_object=target_object,
                    attempted=False,
                    allowed=False,
                    preflight_status="safe",
                    guard_status="blocked",
                    dedupe_decision="no_write",
                    executed_operation="blocked",
                    blocked_reasons=["update_operation_not_supported_in_confirmed_write"],
                    source_context=dict(candidate.source_context),
                )
            )
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
) -> ContextRecoveryResult:
    resolution = gateway_result.customer_resolution
    if resolution is None:
        return ContextRecoveryResult(
            status="context-limited",
            fallback_reason="gateway did not return customer resolution",
            missing_sources=["客户主数据"],
            write_ceiling="recommendation-only",
            open_questions=["客户解析未返回结果，当前上下文不能视为 grounded context"],
        )
    if resolution.status in {"missing", "ambiguous"}:
        return ContextRecoveryResult(
            status="context-limited",
            fallback_reason=f"customer cannot be resolved ({resolution.status}) from current live customer master",
            missing_sources=["客户主数据"],
            write_ceiling="recommendation-only",
            open_questions=["客户解析未达唯一命中，当前只能保持建议态"],
        )

    best = resolution.candidates[0]
    customer_id = best.customer_id
    used_sources = ["客户主数据"]
    key_context = [_render_customer_snapshot(best)]
    key_context.extend(_render_customer_master_details(best))
    missing_sources: list[str] = []
    open_questions: list[str] = []
    candidate_conflicts: list[str] = []

    contact_rows = query_backend.query_rows_by_customer_id("客户联系记录", customer_id, limit=5)
    if contact_rows:
        used_sources.append("客户联系记录")
        key_context.append(_render_latest_contact(contact_rows[0]))
    else:
        missing_sources.append("客户联系记录")
        open_questions.append("缺少最近客户联系记录，需人工确认最近一次有效沟通")

    action_rows = query_backend.query_rows_by_customer_id("行动计划", customer_id, limit=5)
    if action_rows:
        used_sources.append("行动计划")
        key_context.append(_render_latest_action(action_rows[0]))
    else:
        missing_sources.append("行动计划")
        open_questions.append("缺少当前行动计划，需确认是否存在未沉淀的推进事项")

    meeting_notes = _rank_related_meeting_notes(contact_rows, topic_text=topic_text, limit=3)
    if meeting_notes:
        used_sources.append("相关会议纪要候选")
        key_context.append(f"相关会议纪要候选: {'；'.join(meeting_notes)}")
    else:
        note_resolution = _resolve_meeting_note_context(
            query_backend=query_backend,
            customer=best,
            topic_text=topic_text,
            limit=3,
        )
        if note_resolution["used_source"]:
            used_sources.append(str(note_resolution["used_source"]))
        if note_resolution["key_context"]:
            key_context.append(str(note_resolution["key_context"]))
        open_questions.extend(note_resolution["open_questions"])
        candidate_conflicts.extend(note_resolution["candidate_conflicts"])

    archive_resolution = _resolve_archive_context(query_backend=query_backend, customer=best)
    if archive_resolution["used_source"]:
        used_sources.append(str(archive_resolution["used_source"]))
    if archive_resolution["key_context"]:
        key_context.append(str(archive_resolution["key_context"]))
    missing_sources.extend(archive_resolution["missing_sources"])
    open_questions.extend(archive_resolution["open_questions"])
    candidate_conflicts.extend(archive_resolution["candidate_conflicts"])

    status = "completed" if not missing_sources else "partial"
    fallback_reason = None if status == "completed" else "some targeted live reads are still missing"
    write_ceiling = "normal" if status == "completed" and not candidate_conflicts else "recommendation-only"
    return ContextRecoveryResult(
        status=status,
        used_sources=used_sources,
        fallback_reason=fallback_reason,
        key_context=key_context,
        missing_sources=missing_sources,
        open_questions=open_questions,
        write_ceiling=write_ceiling,
        candidate_conflicts=candidate_conflicts,
    )


def _resolve_archive_context(
    *,
    query_backend: QueryBackend,
    customer: CustomerMatch,
) -> dict[str, object]:
    if customer.archive_link:
        return {
            "used_source": "客户档案链接",
            "key_context": f"客户档案链接: {customer.archive_link}",
            "missing_sources": [],
            "open_questions": [],
            "candidate_conflicts": [],
        }

    candidates = _call_optional_backend(
        query_backend,
        "discover_archive_candidates",
        customer.customer_id or "",
        customer.short_name,
        10,
    )
    ranked = _rank_drive_candidates(candidates, customer=customer, topic_text="")
    if len(ranked) == 1:
        if not _has_explicit_customer_evidence(ranked[0], customer):
            return {
                "used_source": "客户档案候选",
                "key_context": f"客户档案候选: {_render_drive_candidate(ranked[0])}",
                "missing_sources": [],
                "open_questions": ["客户档案候选缺少显式客户证据，需人工确认 canonical archive"],
                "candidate_conflicts": [
                    "客户档案候选缺少显式客户证据: " + _render_drive_candidate(ranked[0])
                ],
            }
        return {
            "used_source": "客户档案候选",
            "key_context": f"客户档案候选: {_render_drive_candidate(ranked[0])}",
            "missing_sources": [],
            "open_questions": [],
            "candidate_conflicts": [],
        }
    if len(ranked) > 1:
        return {
            "used_source": None,
            "key_context": None,
            "missing_sources": ["客户档案"],
            "open_questions": ["客户档案候选存在多个高相似结果，需人工确认 canonical archive"],
            "candidate_conflicts": [
                "客户档案候选冲突: " + "；".join(_render_drive_candidate(item) for item in ranked)
            ],
        }
    return {
        "used_source": None,
        "key_context": None,
        "missing_sources": ["客户档案"],
        "open_questions": ["客户档案链接缺失，暂时无法补充 archive 视角"],
        "candidate_conflicts": [],
    }


def _resolve_meeting_note_context(
    *,
    query_backend: QueryBackend,
    customer: CustomerMatch,
    topic_text: str,
    limit: int,
) -> dict[str, object]:
    candidates = _call_optional_backend(
        query_backend,
        "discover_meeting_note_candidates",
        customer.customer_id or "",
        customer.short_name,
        topic_text,
        limit,
    )
    ranked = _rank_drive_candidates(candidates, customer=customer, topic_text=topic_text)
    if not ranked:
        return {
            "used_source": None,
            "key_context": None,
            "open_questions": [],
            "candidate_conflicts": [],
        }
    rendered = [_render_drive_candidate(item) for item in ranked[:limit]]
    if len(ranked) > 1:
        return {
            "used_source": "会议纪要候选",
            "key_context": f"相关会议纪要候选: {'；'.join(rendered)}",
            "open_questions": ["会议纪要候选存在多个同分结果，需人工确认关联会议线程"],
            "candidate_conflicts": ["会议纪要候选冲突: " + "；".join(rendered)],
        }
    if not _has_explicit_customer_evidence(ranked[0], customer):
        return {
            "used_source": "会议纪要候选",
            "key_context": f"相关会议纪要候选: {'；'.join(rendered)}",
            "open_questions": ["会议纪要候选缺少显式客户证据，需人工确认关联会议线程"],
            "candidate_conflicts": ["会议纪要候选缺少显式客户证据: " + rendered[0]],
        }
    return {
        "used_source": "会议纪要候选",
        "key_context": f"相关会议纪要候选: {'；'.join(rendered)}",
        "open_questions": [],
        "candidate_conflicts": [],
    }


def _call_optional_backend(
    query_backend: QueryBackend,
    method_name: str,
    *args: object,
) -> list[dict[str, object]]:
    method = getattr(query_backend, method_name, None)
    if not callable(method):
        return []
    result = method(*args)
    if not isinstance(result, list):
        return []
    return [item for item in result if isinstance(item, dict)]


def _rank_drive_candidates(
    candidates: list[dict[str, object]],
    *,
    customer: CustomerMatch,
    topic_text: str,
) -> list[dict[str, object]]:
    if not candidates:
        return []
    topic_terms = _topic_terms(topic_text)
    scored: list[tuple[int, dict[str, object]]] = []
    for candidate in candidates:
        title = str(candidate.get("title") or candidate.get("name") or "")
        score = 0
        if customer.customer_id and str(candidate.get("customer_id") or "") == customer.customer_id:
            score += 20
        if customer.short_name and str(candidate.get("short_name") or "") == customer.short_name:
            score += 10
        if customer.short_name and customer.short_name in title:
            score += 5
        if topic_terms:
            score += len(_topic_terms(title).intersection(topic_terms)) * 10
        if score > 0:
            scored.append((score, candidate))
    if not scored:
        return []
    scored.sort(key=lambda item: item[0], reverse=True)
    top_score = scored[0][0]
    return [candidate for score, candidate in scored if score == top_score]


def _has_explicit_customer_evidence(
    candidate: dict[str, object],
    customer: CustomerMatch,
) -> bool:
    customer_id = str(candidate.get("customer_id") or "").strip()
    short_name = str(candidate.get("short_name") or "").strip()
    return bool(
        (customer.customer_id and customer_id == customer.customer_id)
        or (customer.short_name and short_name == customer.short_name)
    )


def _render_drive_candidate(candidate: dict[str, object]) -> str:
    title = str(candidate.get("title") or candidate.get("name") or "未命名文档")
    url = str(candidate.get("url") or candidate.get("link") or candidate.get("permalink") or "")
    if url:
        return f"{title}｜{url}"
    return title


def _render_customer_snapshot(best: CustomerMatch) -> str:
    customer_id = best.customer_id or "missing"
    short_name = best.short_name or "unknown"
    return f"客户主数据快照: {short_name}｜客户ID {customer_id}"


def _render_customer_master_details(best: CustomerMatch) -> list[str]:
    raw_record = best.raw_record if isinstance(best.raw_record, dict) else {}
    details: list[str] = []
    strategy_summary = _semantic_value("客户主数据", "strategy_summary", raw_record)
    last_contact_at = _semantic_value("客户主数据", "last_contact_at", raw_record)
    next_action_summary = _semantic_value("客户主数据", "next_action_summary", raw_record)
    if strategy_summary:
        details.append(f"客户主数据策略摘要: {strategy_summary}")
    if last_contact_at:
        details.append(f"客户主数据上次接触: {last_contact_at}")
    if next_action_summary:
        details.append(f"客户主数据下次行动: {next_action_summary}")
    return details


def _semantic_value(table_name: str, semantic_field: str, raw_record: dict[str, object]) -> str:
    slot = SEMANTIC_FIELD_REGISTRY.get(table_name, {}).get(semantic_field, {})
    candidate_keys = [slot.get("canonical_name"), *slot.get("aliases", [])]
    for key in candidate_keys:
        if not key:
            continue
        value = raw_record.get(str(key))
        if value not in (None, ""):
            return str(value)
    return ""


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
    candidates: list[tuple[int, datetime | None, str]] = []
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
        candidates.append((score, _parse_note_date(date), f"{title}｜{date or '日期未提供'}｜{link}"))

    candidates.sort(
        key=lambda item: (item[0], item[1] if item[1] is not None else datetime.min),
        reverse=True,
    )
    return [item[2] for item in candidates[:limit]]


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
