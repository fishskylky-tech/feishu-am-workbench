"""Thin JSON wrapper around local lark-cli commands."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass
class LarkCliCommandError(Exception):
    command: list[str]
    error_type: str
    message: str
    hint: str | None = None
    exit_code: int | None = None

    def __str__(self) -> str:
        suffix = f" ({self.hint})" if self.hint else ""
        return f"{self.error_type}: {self.message}{suffix}"


class LarkCliClient:
    def __init__(
        self,
        binary: str = "lark-cli",
        runner: Runner | None = None,
    ) -> None:
        self.binary = binary
        self.runner = runner or subprocess.run

    def invoke_json(self, args: list[str]) -> dict[str, Any]:
        command = [self.binary, *args]
        completed = self.runner(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        payload = self._parse_json(command, completed.stdout, completed.stderr)
        if completed.returncode != 0:
            raise self._build_error(command, completed.returncode, payload)
        if payload.get("ok") is False:
            raise self._build_error(command, completed.returncode, payload)
        return payload

    def _parse_json(
        self, command: list[str], stdout: str, stderr: str
    ) -> dict[str, Any]:
        raw = stdout.strip() or stderr.strip()
        if not raw:
            raise LarkCliCommandError(
                command=command,
                error_type="empty_output",
                message="lark-cli returned no output",
            )
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LarkCliCommandError(
                command=command,
                error_type="invalid_json",
                message=f"failed to parse lark-cli output: {exc}",
            ) from exc
        if isinstance(parsed, dict):
            return parsed
        raise LarkCliCommandError(
            command=command,
            error_type="invalid_payload",
            message="lark-cli did not return a JSON object",
        )

    def _build_error(
        self,
        command: list[str],
        exit_code: int,
        payload: dict[str, Any],
    ) -> LarkCliCommandError:
        error = payload.get("error")
        if isinstance(error, dict):
            return LarkCliCommandError(
                command=command,
                error_type=str(error.get("type", "command_failed")),
                message=str(error.get("message", "lark-cli command failed")),
                hint=(
                    str(error.get("hint"))
                    if error.get("hint") is not None
                    else None
                ),
                exit_code=exit_code,
            )
        return LarkCliCommandError(
            command=command,
            error_type="command_failed",
            message=str(payload.get("msg", "lark-cli command failed")),
            exit_code=exit_code,
        )
