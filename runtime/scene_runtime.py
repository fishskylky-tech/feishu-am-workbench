"""Shared scene runtime contracts and the first scene adapter."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from evals.meeting_output_bridge import (
    build_meeting_output_artifact,
    build_meeting_todo_candidates,
    recover_live_context,
    run_confirmed_todo_write,
)

from .gateway import FeishuWorkbenchGateway
from .lark_cli import LarkCliClient
from .live_adapter import LarkCliBaseQueryBackend, LiveWorkbenchConfig
from .models import WriteCandidate, WriteExecutionResult
from .runtime_sources import RuntimeSourceLoader
from .todo_writer import TodoWriter

SceneFallbackCategory = Literal[
    "none",
    "customer",
    "context",
    "permission",
    "validation",
    "safety",
]


@dataclass
class SceneRequest:
    scene_name: str
    repo_root: Path
    customer_query: str
    inputs: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneResult:
    scene_name: str
    resource_status: str
    customer_status: str
    context_status: str
    write_ceiling: str
    used_sources: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    judgments: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    fallback_category: SceneFallbackCategory = "none"
    fallback_reason: str | None = None
    fallback_message: str | None = None
    output_text: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def structured_result(self) -> dict[str, Any]:
        result = {
            "scene_name": self.scene_name,
            "resource_status": self.resource_status,
            "customer_status": self.customer_status,
            "context_status": self.context_status,
            "used_sources": list(self.used_sources),
            "facts": list(self.facts),
            "judgments": list(self.judgments),
            "open_questions": list(self.open_questions),
            "recommendations": list(self.recommendations),
            "fallback_category": self.fallback_category,
            "fallback_reason": self.fallback_reason,
            "fallback_message": self.fallback_message,
            "write_ceiling": self.write_ceiling,
            "output_text": self.output_text,
        }
        for key, value in self.payload.items():
            result[key] = deepcopy(value)
        return result

    def render_text(self) -> str:
        return self.output_text


def _build_live_scene_context(
    request: SceneRequest,
    *,
    topic_text: str = "",
) -> tuple[Any, Any]:
    repo_root = request.repo_root.expanduser()
    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    sources = RuntimeSourceLoader(repo_root).load()
    query_backend = LarkCliBaseQueryBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )
    gateway_result = gateway.run(customer_query=request.customer_query)
    recovery = recover_live_context(
        gateway_result=gateway_result,
        query_backend=query_backend,
        topic_text=topic_text,
    )
    return gateway_result, recovery


def _build_context_result(
    *,
    request: SceneRequest,
    gateway_result: Any,
    recovery: Any,
    facts: list[str],
    judgments: list[str],
    open_questions: list[str],
    recommendations: list[str],
    output_text: str,
    payload: dict[str, Any] | None = None,
    write_ceiling: str | None = None,
) -> SceneResult:
    resource_status = gateway_result.resource_resolution.status
    customer_resolution = gateway_result.customer_resolution
    customer_status = customer_resolution.status if customer_resolution is not None else "missing"
    effective_write_ceiling = write_ceiling or recovery.write_ceiling
    fallback_category, fallback_message = _classify_fallback(
        customer_status=customer_status,
        context_status=recovery.status,
        fallback_reason=recovery.fallback_reason,
        write_ceiling=effective_write_ceiling,
    )
    return SceneResult(
        scene_name=request.scene_name,
        resource_status=resource_status,
        customer_status=customer_status,
        context_status=recovery.status,
        used_sources=list(recovery.used_sources),
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        recommendations=recommendations,
        fallback_category=fallback_category,
        fallback_reason=recovery.fallback_reason,
        fallback_message=fallback_message,
        write_ceiling=effective_write_ceiling,
        output_text=output_text,
        payload=payload or {},
    )


def run_post_meeting_scene(request: SceneRequest) -> SceneResult:
    repo_root = request.repo_root.expanduser()
    transcript_file = Path(str(request.inputs["transcript_file"]))
    eval_name = str(request.inputs["eval_name"])
    action_items = list(request.inputs.get("action_items") or [])
    confirm_write = bool(request.options.get("confirm_write", False))

    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    sources = RuntimeSourceLoader(repo_root).load()
    query_backend = LarkCliBaseQueryBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )

    gateway_result = gateway.run(customer_query=request.customer_query)
    recovery = recover_live_context(
        gateway_result=gateway_result,
        query_backend=query_backend,
        topic_text=transcript_file.stem,
    )
    candidates = build_meeting_todo_candidates(
        eval_name=eval_name,
        gateway_result=gateway_result,
        action_items=action_items or None,
    )

    write_results: list[WriteExecutionResult] = []
    if confirm_write and candidates:
        todo_writer = TodoWriter.for_live_lark_cli(str(repo_root))
        write_results = run_confirmed_todo_write(
            candidates=candidates,
            todo_writer=todo_writer,
        )

    artifact = build_meeting_output_artifact(
        eval_name=eval_name,
        transcript_path=transcript_file,
        gateway_result=gateway_result,
        recovery=recovery,
        write_results=write_results,
    )

    resource_status = gateway_result.resource_resolution.status
    customer_resolution = gateway_result.customer_resolution
    customer_status = customer_resolution.status if customer_resolution is not None else "missing"
    facts = list(recovery.key_context)
    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    recommendations = [
        str(candidate.payload.get("summary") or "")
        for candidate in candidates
        if str(candidate.payload.get("summary") or "").strip()
    ]
    fallback_category, fallback_message = _classify_fallback(
        customer_status=customer_status,
        context_status=recovery.status,
        fallback_reason=recovery.fallback_reason,
        write_ceiling=recovery.write_ceiling,
    )

    return SceneResult(
        scene_name=request.scene_name,
        resource_status=resource_status,
        customer_status=customer_status,
        context_status=recovery.status,
        used_sources=list(recovery.used_sources),
        facts=facts,
        judgments=[],
        open_questions=open_questions,
        recommendations=recommendations,
        fallback_category=fallback_category,
        fallback_reason=recovery.fallback_reason,
        fallback_message=fallback_message,
        write_ceiling=recovery.write_ceiling,
        output_text=str(artifact["output_text"]),
        payload={
            "candidate_count": len(candidates),
            "candidates": [_serialize_candidate(candidate) for candidate in candidates],
            "write_result_details": deepcopy(artifact["write_result_details"]),
            "scene_payload": {
                "meeting_eval": eval_name,
                "transcript_file": transcript_file.name,
            },
        },
    )


def _serialize_candidate(candidate: Any) -> dict[str, Any]:
    return {
        "target_object": candidate.target_object,
        "operation": candidate.operation,
        "payload": dict(candidate.payload),
        "match_basis": dict(candidate.match_basis),
        "source_context": dict(candidate.source_context),
    }


def run_customer_recent_status_scene(request: SceneRequest) -> SceneResult:
    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    facts = list(recovery.key_context)
    judgments: list[str] = []
    if recovery.status == "completed":
        judgments.append("当前客户近期状态已有足够 live 证据，可继续输出经营判断。")
    else:
        judgments.append("当前客户近期状态仍有上下文缺口，判断应保持 recommendation-first。")
    if recovery.candidate_conflicts:
        judgments.append("部分档案或会议证据存在冲突，近期状态需要人工复核后再沉淀。")
    elif recovery.write_ceiling == "normal":
        judgments.append("当前证据链没有触发额外 safety downgrade。")

    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    recommendations: list[str] = []
    if recovery.missing_sources:
        recommendations.append(
            f"优先补齐 {'、'.join(recovery.missing_sources)} 后再更新客户最近状态。"
        )
    if recovery.candidate_conflicts:
        recommendations.append("先确认档案或会议纪要候选，再决定是否沉淀为正式客户状态结论。")
    if not recommendations:
        recommendations.append("基于当前 live 上下文整理一版客户最近状态结论，供后续会前/会后复用。")

    lines = [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

    return _build_context_result(
        request=request,
        gateway_result=gateway_result,
        recovery=recovery,
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        recommendations=recommendations,
        output_text="\n".join(lines),
        payload={
            "scene_payload": {
                "topic_text": topic_text,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
            }
        },
    )


def run_archive_refresh_scene(request: SceneRequest) -> SceneResult:
    topic_text = str(request.inputs.get("topic_text") or "客户档案")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    facts = list(recovery.key_context)
    has_archive_anchor = any("客户档案" in item for item in facts)
    judgments: list[str] = []
    if has_archive_anchor:
        judgments.append("当前 archive refresh 已有可定位的客户档案锚点。")
    else:
        judgments.append("当前还没有稳定的客户档案锚点，archive refresh 只能停留在候选确认。")
    if recovery.candidate_conflicts:
        judgments.append("档案候选存在冲突或弱证据，refresh 不能直接进入正式沉淀。")

    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    recommendations: list[str] = []
    if has_archive_anchor and not recovery.candidate_conflicts:
        recommendations.append("以当前客户档案锚点为主，整理需要补充到 archive 的最近进展和行动变化。")
    if "客户档案" in recovery.missing_sources or not has_archive_anchor:
        recommendations.append("先补齐 canonical archive 链接或确认档案候选，再执行 refresh。")
    if recovery.candidate_conflicts:
        recommendations.append("先确认 canonical archive，再决定是否把 refresh 结果当作正式客户事实沉淀。")
    if not recommendations:
        recommendations.append("当前 archive 视角已足够作为 refresh 建议输入，但后续写回仍需走现有共享安全路径。")

    lines = [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

    return _build_context_result(
        request=request,
        gateway_result=gateway_result,
        recovery=recovery,
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        recommendations=recommendations,
        output_text="\n".join(lines),
        payload={
            "scene_payload": {
                "topic_text": topic_text,
                "archive_anchor_ready": has_archive_anchor,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
            }
        },
    )


def run_todo_capture_and_update_scene(request: SceneRequest) -> SceneResult:
    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    candidates = _build_follow_on_todo_candidates(request, gateway_result)
    confirm_write = bool(request.options.get("confirm_write", False))

    write_results: list[WriteExecutionResult] = []
    if confirm_write and candidates:
        todo_writer = TodoWriter.for_live_lark_cli(str(request.repo_root.expanduser()))
        write_results = run_confirmed_todo_write(
            candidates=candidates,
            todo_writer=todo_writer,
        )

    facts = list(recovery.key_context)
    judgments: list[str] = []
    if candidates:
        judgments.append("当前 follow-on 信息已整理成可进入统一 Todo path 的候选。")
    else:
        judgments.append("当前没有足够明确的 follow-on 项可转成 Todo candidate。")
    if recovery.write_ceiling == "recommendation-only" or recovery.candidate_conflicts:
        judgments.append("由于 live context 不完整或证据冲突，当前仍应保持 recommendation-first。")

    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    if not candidates:
        open_questions.append("需要提供明确的 follow-on summary/owner/due_at 才能生成 Todo 候选。")

    recommendations = [
        str(candidate.payload.get("summary") or "")
        for candidate in candidates
        if str(candidate.payload.get("summary") or "").strip()
    ]
    if not recommendations:
        recommendations.append("先补充需要沉淀为 Todo 的后续动作，再决定是否确认写回。")

    lines = [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
        f"候选数量: {len(candidates)}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

    return _build_context_result(
        request=request,
        gateway_result=gateway_result,
        recovery=recovery,
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        recommendations=recommendations,
        output_text="\n".join(lines),
        payload={
            "candidate_count": len(candidates),
            "candidates": [_serialize_candidate(candidate) for candidate in candidates],
            "write_result_details": [item.structured_result() for item in write_results],
            "scene_payload": {
                "topic_text": topic_text,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
            },
        },
    )


def _build_follow_on_todo_candidates(
    request: SceneRequest,
    gateway_result: Any,
) -> list[Any]:
    resolution = gateway_result.customer_resolution
    if resolution is None or resolution.status != "resolved" or not resolution.candidates:
        return []

    customer = resolution.candidates[0]
    raw_items = list(request.inputs.get("todo_items") or [])
    candidates: list[Any] = []
    for index, item in enumerate(raw_items):
        summary = str(item.get("summary") or item.get("title") or "").strip()
        if not summary:
            continue
        due_at = item.get("due_at")
        payload: dict[str, Any] = {
            "summary": summary,
            "customer": customer.short_name,
            "priority": str(item.get("priority") or "中"),
            "description": str(
                item.get("description")
                or "来自 Todo follow-on scene 的建议态事项；确认后才进入统一写回。"
            ),
        }
        owner = str(item.get("owner") or "").strip()
        if owner:
            payload["owner"] = owner
        if due_at is not None:
            payload["due_at"] = due_at

        candidates.append(
            WriteExecutionCandidate(
                customer=customer,
                index=index,
                payload=payload,
            ).as_write_candidate()
        )
    return candidates


@dataclass
class WriteExecutionCandidate:
    customer: Any
    index: int
    payload: dict[str, Any]

    def as_write_candidate(self) -> Any:
        due_at = self.payload.get("due_at")
        if isinstance(due_at, str) and len(due_at) >= 7:
            time_window = due_at[:7]
        else:
            time_window = "follow_on"
        return WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "owner", "customer", "priority", "due_at"],
            payload=dict(self.payload),
            match_basis={
                "customer": self.customer.short_name,
                "time_window": time_window,
                "candidate_index": str(self.index),
            },
            source_context={
                "scenario": "todo_follow_on",
                "customer_id": self.customer.customer_id,
                "scene_name": "todo-capture-and-update",
            },
        )


def _render_customer_status(gateway_result: Any) -> str:
    customer_resolution = gateway_result.customer_resolution
    if customer_resolution is None:
        return "missing"
    if customer_resolution.status == "resolved" and customer_resolution.candidates:
        best = customer_resolution.candidates[0]
        return f"{best.short_name} / 客户ID {best.customer_id or 'missing'}"
    return customer_resolution.status


def _classify_fallback(
    *,
    customer_status: str,
    context_status: str,
    fallback_reason: str | None,
    write_ceiling: str,
) -> tuple[SceneFallbackCategory, str | None]:
    reason = (fallback_reason or "").casefold()
    if customer_status != "resolved":
        return "customer", "客户还没有被唯一确认，当前结果只能先停留在建议层。"
    if not fallback_reason and context_status == "completed" and write_ceiling != "recommendation-only":
        return "none", None
    if "permission" in reason or "scope" in reason or "denied" in reason or "forbidden" in reason:
        return "permission", "当前缺少必要权限或资源可见性，结果只能先停留在建议层。"
    if "schema" in reason or "preflight" in reason or "field" in reason or "validation" in reason:
        return "validation", "实时校验没有通过，当前不能继续推进写回。"
    if "guard" in reason or "protected" in reason or "risk" in reason or "blocked" in reason:
        return "safety", "安全规则拦住了继续执行或写回，当前只保留建议结果。"
    if context_status != "completed" or write_ceiling == "recommendation-only":
        return "context", "现场资料还不够完整，当前结果只能作为建议参考。"
    return "context", "当前结果存在受限条件，请先按 fallback 原因补足信息后再继续。"
