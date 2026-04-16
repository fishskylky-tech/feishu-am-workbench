"""CLI entry for local runtime diagnostics and operator flows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from evals.meeting_output_bridge import (
    build_meeting_output_artifact,
    build_meeting_todo_candidates,
    recover_live_context,
    run_confirmed_todo_write,
)
from .diagnostics import build_live_diagnostic, render_live_diagnostic
from .env_loader import load_dotenv
from .gateway import FeishuWorkbenchGateway
from .lark_cli import LarkCliClient
from .live_adapter import LarkCliBaseQueryBackend, LiveWorkbenchConfig
from .runtime_sources import RuntimeSourceLoader
from .todo_writer import TodoWriter


def _run_diagnostic(argv: list[str]) -> int:
    repo_root = Path(argv[0]).expanduser() if argv else Path.cwd()
    load_dotenv(repo_root)
    report = build_live_diagnostic(repo_root)
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_live_diagnostic(report))
    return 0


def _parse_action_items(raw_values: list[str]) -> list[dict[str, object]]:
    action_items: list[dict[str, object]] = []
    for raw in raw_values:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid --action-item-json payload: {exc}") from exc
        if not isinstance(item, dict):
            raise SystemExit("--action-item-json requires a JSON object per item")
        action_items.append(item)
    return action_items


def _serialize_candidate(candidate: Any) -> dict[str, Any]:
    return {
        "target_object": candidate.target_object,
        "operation": candidate.operation,
        "payload": dict(candidate.payload),
        "match_basis": dict(candidate.match_basis),
        "source_context": dict(candidate.source_context),
    }


def _build_meeting_write_loop_result(
    *,
    repo_root: Path,
    eval_name: str,
    transcript_file: Path,
    customer_query: str,
    confirm_write: bool,
    action_items: list[dict[str, object]],
) -> dict[str, Any]:
    load_dotenv(repo_root)
    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    sources = RuntimeSourceLoader(repo_root).load()
    query_backend = LarkCliBaseQueryBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )
    gateway_result = gateway.run(customer_query=customer_query)
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
    write_results = []
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
    return {
        "output_text": artifact["output_text"],
        "resource_status": gateway_result.resource_resolution.status,
        "customer_status": gateway_result.customer_resolution.status if gateway_result.customer_resolution else "missing",
        "context_status": recovery.status,
        "write_ceiling": recovery.write_ceiling,
        "candidate_count": len(candidates),
        "candidates": [_serialize_candidate(candidate) for candidate in candidates],
        "write_result_details": artifact["write_result_details"],
    }


def _render_meeting_write_loop(result: dict[str, Any]) -> str:
    lines = [str(result["output_text"])]
    candidate_count = int(result.get("candidate_count") or 0)
    if candidate_count:
        lines.append("待确认写回候选:")
        for candidate in result.get("candidates", []):
            payload = candidate.get("payload") or {}
            summary = str(payload.get("summary") or "未命名候选")
            target_object = str(candidate.get("target_object") or "todo")
            operation = str(candidate.get("operation") or "create")
            lines.append(f"- {target_object}: {operation}｜{summary}")
    else:
        lines.append("待确认写回候选: 无")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local runtime operator CLI")
    subparsers = parser.add_subparsers(dest="command")

    diagnose = subparsers.add_parser("diagnose", help="render live diagnostic")
    diagnose.add_argument("repo_root", nargs="?", default=".")
    diagnose.add_argument("--json", action="store_true")

    meeting = subparsers.add_parser(
        "meeting-write-loop",
        help="run the meeting recovery -> candidate -> optional confirmed-write operator flow",
    )
    meeting.add_argument("--eval-name", required=True)
    meeting.add_argument("--transcript-file", required=True)
    meeting.add_argument("--customer-query", required=True)
    meeting.add_argument("--repo-root", default=".")
    meeting.add_argument("--confirm-write", action="store_true")
    meeting.add_argument("--json", action="store_true")
    meeting.add_argument("--action-item-json", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] not in {"diagnose", "meeting-write-loop"}:
        return _run_diagnostic(argv)

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "diagnose":
        diagnostic_args = [args.repo_root]
        if args.json:
            diagnostic_args.append("--json")
        return _run_diagnostic(diagnostic_args)

    action_items = _parse_action_items(args.action_item_json)
    result = _build_meeting_write_loop_result(
        repo_root=Path(args.repo_root).expanduser(),
        eval_name=args.eval_name,
        transcript_file=Path(args.transcript_file).expanduser(),
        customer_query=args.customer_query,
        confirm_write=args.confirm_write,
        action_items=action_items,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_render_meeting_write_loop(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
