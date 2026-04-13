"""Minimal .env loader for runtime entrypoints."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(repo_root: str | Path, file_name: str = ".env", override: bool = False) -> list[str]:
    """Load KEY=VALUE pairs from a local .env file.

    This loader is intentionally minimal and only supports simple KEY=VALUE lines.
    Existing environment variables are preserved by default.
    """

    root = Path(repo_root)
    dotenv_path = root / file_name
    if not dotenv_path.exists() or not dotenv_path.is_file():
        return []

    loaded_keys: list[str] = []
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
            value = value[1:-1]

        if not override and key in os.environ:
            continue
        os.environ[key] = value
        loaded_keys.append(key)

    return loaded_keys
