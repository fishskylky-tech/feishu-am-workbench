"""CLI entry for local runtime diagnostics and operator flows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .diagnostics import build_live_diagnostic, render_live_diagnostic
from .scene_registry import UnknownSceneError, dispatch_scene
from .scene_runtime import SceneRequest


def _run_diagnostic(argv: list[str]) -> int:
    repo_root = Path(argv[0]).expanduser() if argv else Path.cwd()
    report = build_live_diagnostic(repo_root)
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_live_diagnostic(report))
    return 0


def _parse_action_items(raw_values: list[str]) -> list[dict[str, object]]:
    return _parse_json_objects(raw_values, option_name="--action-item-json")


def _parse_todo_items(raw_values: list[str]) -> list[dict[str, object]]:
    return _parse_json_objects(raw_values, option_name="--todo-item-json")


def _parse_json_objects(raw_values: list[str], *, option_name: str) -> list[dict[str, object]]:
    action_items: list[dict[str, object]] = []
    for raw in raw_values:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid {option_name} payload: {exc}") from exc
        if not isinstance(item, dict):
            raise SystemExit(f"{option_name} requires a JSON object per item")
        action_items.append(item)
    return action_items


def _validate_scene_args(args: argparse.Namespace) -> None:
    if args.scene_name == "post-meeting-synthesis":
        missing: list[str] = []
        if not args.eval_name:
            missing.append("--eval-name")
        if not args.transcript_file:
            missing.append("--transcript-file")
        if missing:
            raise SystemExit(
                "post-meeting-synthesis requires " + ", ".join(missing)
            )


def _build_scene_request(args: argparse.Namespace) -> SceneRequest:
    _validate_scene_args(args)
    action_items = _parse_action_items(getattr(args, "action_item_json", []))
    todo_items = _parse_todo_items(getattr(args, "todo_item_json", []))
    return SceneRequest(
        scene_name=args.scene_name,
        repo_root=Path(args.repo_root).expanduser(),
        customer_query=args.customer_query,
        inputs={
            "eval_name": args.eval_name,
            "transcript_file": args.transcript_file,
            "action_items": action_items,
            "todo_items": todo_items,
            "topic_text": getattr(args, "topic_text", ""),
        },
        options={
            "confirm_write": bool(getattr(args, "confirm_write", False)),
        },
    )


def _run_scene_request(request: SceneRequest, as_json: bool) -> int:
    try:
        result = dispatch_scene(request)
    except UnknownSceneError as exc:
        raise SystemExit(str(exc)) from exc
    if as_json:
        print(json.dumps(result.structured_result(), ensure_ascii=False, indent=2))
    else:
        print(result.render_text())
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local runtime operator CLI")
    subparsers = parser.add_subparsers(dest="command")

    diagnose = subparsers.add_parser("diagnose", help="render live diagnostic")
    diagnose.add_argument("repo_root", nargs="?", default=".")
    diagnose.add_argument("--json", action="store_true")

    scene = subparsers.add_parser(
        "scene",
        help="run a named scene through the shared scene runtime contract",
    )
    scene.add_argument("scene_name")
    scene.add_argument("--eval-name")
    scene.add_argument("--transcript-file")
    scene.add_argument("--customer-query", required=True)
    scene.add_argument("--repo-root", default=".")
    scene.add_argument("--topic-text", default="")
    scene.add_argument("--confirm-write", action="store_true")
    scene.add_argument("--json", action="store_true")
    scene.add_argument("--action-item-json", action="append", default=[])
    scene.add_argument("--todo-item-json", action="append", default=[])

    meeting = subparsers.add_parser(
        "meeting-write-loop",
        help="compatibility wrapper for the post-meeting scene runtime",
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
    if not argv or argv[0] not in {"diagnose", "scene", "meeting-write-loop"}:
        return _run_diagnostic(argv)

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "diagnose":
        diagnostic_args = [args.repo_root]
        if args.json:
            diagnostic_args.append("--json")
        return _run_diagnostic(diagnostic_args)

    if args.command == "scene":
        request = _build_scene_request(args)
        return _run_scene_request(request, args.json)

    request = SceneRequest(
        scene_name="post-meeting-synthesis",
        repo_root=Path(args.repo_root).expanduser(),
        customer_query=args.customer_query,
        inputs={
            "eval_name": args.eval_name,
            "transcript_file": args.transcript_file,
            "action_items": _parse_action_items(args.action_item_json),
        },
        options={"confirm_write": args.confirm_write},
    )
    return _run_scene_request(request, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
