from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = REPO_ROOT / "evals" / "evals.json"


@dataclass
class AssertionResult:
    assertion_id: str
    description: str
    passed: bool
    details: dict[str, Any]


def load_evals(path: Path = EVALS_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def get_eval_case(*, eval_id: int | None = None, eval_name: str | None = None) -> dict[str, Any]:
    payload = load_evals()
    cases = payload["evals"]
    for case in cases:
        if eval_id is not None and case["id"] == eval_id:
            return case
        if eval_name is not None and case["name"] == eval_name:
            return case
    needle = eval_id if eval_id is not None else eval_name
    raise KeyError(f"unknown eval case: {needle}")


def evaluate_output(case: dict[str, Any], output_text: str) -> dict[str, Any]:
    results = [_evaluate_assertion(assertion, output_text) for assertion in case["assertions"]]
    return {
        "eval_id": case["id"],
        "eval_name": case["name"],
        "scenario": case["scenario"],
        "passed": all(item.passed for item in results),
        "assertions": [
            {
                "id": item.assertion_id,
                "description": item.description,
                "passed": item.passed,
                "details": item.details,
            }
            for item in results
        ],
    }


def evaluate_case(*, eval_id: int | None = None, eval_name: str | None = None, output_text: str) -> dict[str, Any]:
    case = get_eval_case(eval_id=eval_id, eval_name=eval_name)
    return evaluate_output(case, output_text)


def _evaluate_assertion(assertion: dict[str, Any], output_text: str) -> AssertionResult:
    assertion_type = assertion["type"]
    text = output_text.casefold()
    if assertion_type == "contains_all":
        patterns = assertion["patterns"]
        missing = [pattern for pattern in patterns if pattern.casefold() not in text]
        return AssertionResult(
            assertion_id=assertion["id"],
            description=assertion["description"],
            passed=not missing,
            details={"type": assertion_type, "missing_patterns": missing},
        )
    if assertion_type == "contains_any":
        patterns = assertion["patterns"]
        matched = [pattern for pattern in patterns if pattern.casefold() in text]
        return AssertionResult(
            assertion_id=assertion["id"],
            description=assertion["description"],
            passed=bool(matched),
            details={"type": assertion_type, "matched_patterns": matched, "patterns": patterns},
        )
    if assertion_type == "not_contains_any":
        patterns = assertion["patterns"]
        forbidden = [pattern for pattern in patterns if pattern.casefold() in text]
        return AssertionResult(
            assertion_id=assertion["id"],
            description=assertion["description"],
            passed=not forbidden,
            details={"type": assertion_type, "forbidden_patterns": forbidden},
        )
    if assertion_type == "live_first_gate":
        details = _evaluate_live_first_gate(output_text)
        return AssertionResult(
            assertion_id=assertion["id"],
            description=assertion["description"],
            passed=details["passed"],
            details=details,
        )
    raise ValueError(f"unsupported assertion type: {assertion_type}")


def _evaluate_live_first_gate(output_text: str) -> dict[str, Any]:
    text = output_text.casefold()
    has_resource = _contains_any(
        text,
        ["资源解析状态", "resource_source_status", "gateway stage 1", "live-first 已尝试"],
    )
    has_customer = _contains_any(
        text,
        ["客户解析结果", "customer_resolution", "resolved customer", "客户id", "客户id`"],
    )
    has_context = _contains_any(
        text,
        ["上下文恢复状态", "context_recovery_status", "not-run", "context-limited", "completed", "partial"],
    )
    used_sources = _contains_any(
        text,
        ["已使用飞书资料", "context_sources_used", "context sources", "已使用资料"],
    )
    fallback_reason = _contains_any(
        text,
        ["fallback 原因", "未执行原因", "fallback reason"],
    )
    passed = has_resource and has_customer and has_context and (used_sources or fallback_reason)
    return {
        "type": "live_first_gate",
        "passed": passed,
        "has_resource_status": has_resource,
        "has_customer_resolution": has_customer,
        "has_context_status": has_context,
        "has_used_sources": used_sources,
        "has_fallback_reason": fallback_reason,
    }


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern.casefold() in text for pattern in patterns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run structured checks against one feishu-am-workbench eval case.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--eval-id", type=int)
    group.add_argument("--eval-name")
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output-file")
    output_group.add_argument("--output-text")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    output_text = (
        Path(args.output_file).read_text()
        if args.output_file
        else args.output_text
    )
    result = evaluate_case(eval_id=args.eval_id, eval_name=args.eval_name, output_text=output_text)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
